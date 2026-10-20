"""FastAPI gateway for the Next.js Yuejian web application.

The existing deterministic retrieval, prompts, revision planning and document
export modules are reused verbatim. BYOK credentials are request-scoped, never
stored server-side, serialized into results, or returned to the browser.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections import defaultdict, deque
from collections.abc import Iterator
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field, SecretStr

from core.config import build_model_config, platform_service_ready
from core.models import (
    MAX_RAW_REQUEST_CHARS,
    MAX_REVISION_INSTRUCTION_CHARS,
    RetrievalBundle,
    RevisionRequest,
    TaskRequest,
    TaskType,
)
from core.quotas import _visitor_fingerprint, reserve_platform_request, shared_quota_ready
from core.revisions import REVISION_PRESETS, plan_custom_revision, plan_quick_revision
from services.export import build_docx, build_markdown, build_plain_text
from services.llm import ModelGatewayError, collect_stream_with_safe_fallback
from services.output import sanitize_model_output
from services.prompt_builder import build_initial_messages, build_revision_messages
from services.quality import inspect_answer
from services.retrieval import KnowledgeBaseError, retrieve
from services.scenarios import resolve_policy

logger = logging.getLogger(__name__)
app = FastAPI(title="粤见非遗 API", version="2.0.0", docs_url="/docs" if os.getenv("API_DOCS_ENABLED") == "1" else None)
origins = [entry.strip() for entry in os.getenv("WEB_ALLOWED_ORIGINS", "http://localhost:3000").split(",") if entry.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Basic abuse control suitable for a single-instance preview. Multi-instance
# deployments must use a shared rate limiter (e.g. Redis / API gateway).
_window: dict[str, deque[float]] = defaultdict(deque)
_window_lock = threading.Lock()
RATE_LIMIT = max(1, int(os.getenv("GENERATE_RATE_LIMIT_PER_MIN", "8")))
EXPORT_RATE_LIMIT = max(1, int(os.getenv("EXPORT_RATE_LIMIT_PER_MIN", "25")))
_EXPORT_WINDOW: dict[str, deque[float]] = defaultdict(deque)


class TaskInput(BaseModel):
    scene: Literal["游客路线", "学生研学", "亲子体验", "内容创作", "非遗问答"]
    raw_request: str = Field(min_length=1, max_length=MAX_RAW_REQUEST_CHARS)
    city: str = Field(default="自动判断", max_length=32)
    duration: str = Field(default="自动判断", max_length=32)
    identity: str = Field(default="自动匹配", max_length=32)
    interests: list[str] = Field(default_factory=list, max_length=12)
    output_style: str = Field(default="清晰实用", max_length=32)
    task_type: TaskType | None = None

    def to_domain(self) -> TaskRequest:
        return TaskRequest.from_dict(self.model_dump(mode="json"))


class ModelOptions(BaseModel):
    mode: Literal["auto", "user"] = "auto"
    provider: str = Field(default="阿里云百炼", max_length=80)
    api_key: SecretStr | None = Field(default=None, repr=False)
    base_url: str = Field(default="", max_length=300)
    model_name: str = Field(default="", max_length=100)
    temperature: float = Field(default=0.62, ge=0.1, le=1.0)

    def resolve(self):
        if self.mode == "auto":
            return build_model_config({"model_mode": "auto"})
        return build_model_config(
            {
                "model_mode": "user",
                "user_provider": self.provider,
                "user_api_key": self.api_key.get_secret_value() if self.api_key else "",
                "user_base_url": self.base_url,
                "user_model_name": self.model_name,
            }
        )


class GenerateInput(BaseModel):
    request: TaskInput
    model: ModelOptions = Field(default_factory=ModelOptions)


class ReviseInput(GenerateInput):
    current_answer: str = Field(min_length=1, max_length=35000)
    instruction: str = Field(default="", max_length=MAX_REVISION_INSTRUCTION_CHARS)
    preset: str | None = None


class ExportInput(BaseModel):
    request: TaskInput
    answer: str = Field(min_length=1, max_length=35000)
    sources: str = Field(default="", max_length=10000)
    format: Literal["md", "txt", "docx"]


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _rate_limit(request: Request) -> None:
    # The socket peer may be a shared proxy; only trust the edge-injected
    # visitor header under Vercel, via the quota fingerprint helper.
    client_ip = _visitor_fingerprint(request)
    now = time.monotonic()
    with _window_lock:
        queue = _window[client_ip]
        while queue and now - queue[0] >= 60:
            queue.popleft()
        if len(queue) >= RATE_LIMIT:
            raise HTTPException(status_code=429, detail="请求过于频繁，请一分钟后重试。")
        queue.append(now)


def _prepare_generation(body: GenerateInput, revise: bool):
    try:
        model_config = body.model.resolve()
        task = body.request.to_domain()
        revision = None
        if revise:
            assert isinstance(body, ReviseInput)
            if body.preset:
                plan = plan_quick_revision(task, body.preset)
            else:
                plan = plan_custom_revision(task, body.instruction)
            task = plan.revised_request
            revision = RevisionRequest(
                root_request=task,
                current_answer=body.current_answer,
                instruction=plan.instruction,
                target_task_type=plan.target_task_type,
            )
        # Fail invalid combinations before reserving the platform AI quota.
        resolve_policy(task)
        return model_config, task, revision
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _generation_events(config, task: TaskRequest, revision: RevisionRequest | None, temperature: float) -> Iterator[str]:
    try:
        yield _sse("stage", {"value": "retrieving", "label": "正在检索广东非遗知识…"})
        query = task.retrieval_query if revision is None else f"{task.retrieval_query} {revision.instruction}"
        bundle: RetrievalBundle = retrieve(query, top_k=3, max_total_chars=2200)
        messages = (
            build_initial_messages(task, bundle)
            if revision is None
            else build_revision_messages(revision, bundle)
        )
        yield _sse("stage", {"value": "writing", "label": "正在策划专属文化方案…"})
        last = ""
        began_at = time.monotonic()
        first_token_ms = None
        last_sent_at = began_at - 1.0
        for text, is_final in collect_stream_with_safe_fallback(
            config, messages, temperature=temperature
        ):
            cleaned = sanitize_model_output(text)
            now = time.monotonic()
            if cleaned.strip() and first_token_ms is None:
                first_token_ms = round((now - began_at) * 1000)
            if is_final:
                if not cleaned.strip():
                    raise ModelGatewayError("模型没有返回可用内容。")
                yield _sse("complete", {
                    "answer": cleaned,
                    "sources": bundle.source_markdown(),
                    "request": task.to_dict(),
                    "quality": inspect_answer(cleaned, task.task_type, bundle, request=task),
                    "metrics": {
                        "first_token_ms": first_token_ms,
                        "total_ms": round((now - began_at) * 1000),
                    },
                })
            elif cleaned != last and now - last_sent_at >= 0.12:
                # Send only appended text. A sanitized rewrite uses a snapshot.
                if last and cleaned.startswith(last):
                    yield _sse("delta", {"text": cleaned[len(last):]})
                else:
                    yield _sse("snapshot", {"text": cleaned})
                last = cleaned
                last_sent_at = now
    except (ValueError, ModelGatewayError, KnowledgeBaseError) as exc:
        yield _sse("failure", {"message": str(exc)})
    except Exception:
        logger.exception("Unhandled generation failure (payload redacted)")
        yield _sse("failure", {"message": "当前生成服务暂不可用，请稍后重试。"})


@app.middleware("http")
async def no_store(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/v1/status")
def status() -> dict:
    return {
        "service": "ok",
        "platform_ready": platform_service_ready(),
        "platform_quota_protected": shared_quota_ready(),
        "scenes": ["游客路线", "学生研学", "亲子体验", "内容创作", "非遗问答"],
        "revision_presets": list(REVISION_PRESETS),
    }


@app.post("/v1/generate")
def generate(body: GenerateInput, request: Request) -> StreamingResponse:
    _rate_limit(request)
    config, task, revision = _prepare_generation(body, revise=False)
    if config.credential_source == "platform":
        reserve_platform_request(request)
    return StreamingResponse(
        _generation_events(config, task, revision, body.model.temperature),
        media_type="text/event-stream; charset=utf-8",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-store"},
    )


@app.post("/v1/revise")
def revise(body: ReviseInput, request: Request) -> StreamingResponse:
    _rate_limit(request)
    config, task, revision = _prepare_generation(body, revise=True)
    if config.credential_source == "platform":
        reserve_platform_request(request)
    return StreamingResponse(
        _generation_events(config, task, revision, body.model.temperature),
        media_type="text/event-stream; charset=utf-8",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-store"},
    )


@app.post("/v1/export")
def export(body: ExportInput, request: Request) -> Response:
    # Export is free, but document creation still needs resource protection.
    # This is a per-instance safeguard; API gateway/WAF provides global controls.
    client_ip = _visitor_fingerprint(request)
    now = time.monotonic()
    with _window_lock:
        queue = _EXPORT_WINDOW[client_ip]
        while queue and now - queue[0] >= 60:
            queue.popleft()
        if len(queue) >= EXPORT_RATE_LIMIT:
            raise HTTPException(status_code=429, detail="导出过于频繁，请稍后重试。")
        queue.append(now)
    try:
        task = body.request.to_domain()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if body.format == "md":
        payload = build_markdown(task, body.answer, body.sources).encode("utf-8")
        mime = "text/markdown; charset=utf-8"
    elif body.format == "txt":
        payload = build_plain_text(task, body.answer, body.sources).encode("utf-8")
        mime = "text/plain; charset=utf-8"
    else:
        payload = build_docx(task, body.answer, body.sources)
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return Response(
        content=payload,
        media_type=mime,
        headers={
            "Content-Disposition": f'attachment; filename="yuejian-feiyi.{body.format}"',
            "Cache-Control": "no-store",
        },
    )
