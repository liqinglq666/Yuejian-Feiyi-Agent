"""Backward-compatible public agent API.

The Streamlit application uses the structured service layer directly. These
functions remain for scripts or third-party imports that used the original API.
"""
from __future__ import annotations

import os
from collections.abc import Generator

from dotenv import load_dotenv

from core.models import ModelConfig, TaskRequest, TaskType
from services.llm import build_client
from services.prompt_builder import build_initial_messages
from services.retrieval import retrieve

load_dotenv()

KEYWORD_GROUPS: tuple[tuple[TaskType, tuple[str, ...]], ...] = (
    (TaskType.VIDEO, ("短视频", "分镜", "旁白", "镜头", "口播")),
    (TaskType.SOCIAL, ("小红书", "朋友圈", "图文", "文案", "标签")),
    (TaskType.STUDY, ("研学", "任务卡", "采访问题", "报告提纲")),
    (TaskType.ROUTE, ("路线", "行程", "一日游", "半天", "亲子")),
)

SCENE_BY_TASK = {
    TaskType.QA: "非遗问答",
    TaskType.ROUTE: "游客路线",
    TaskType.STUDY: "学生研学",
    TaskType.SOCIAL: "内容创作",
    TaskType.VIDEO: "内容创作",
}


def detect_task_type(user_input: str) -> str:
    """Compatibility fallback only; the web app uses explicit task routing."""
    for task_type, keywords in KEYWORD_GROUPS:
        if any(keyword in user_input for keyword in keywords):
            return task_type.value
    return TaskType.QA.value


def _build_request(user_input: str, task_type: str | TaskType | None) -> TaskRequest:
    resolved = TaskType(task_type or detect_task_type(user_input))
    return TaskRequest(
        scene=SCENE_BY_TASK[resolved],
        raw_request=user_input,
        task_type=resolved,
    )


def _config(api_key: str | None, base_url: str | None, model_name: str | None) -> ModelConfig:
    return ModelConfig(
        api_key=(api_key or os.getenv("OPENAI_API_KEY", "")).strip(),
        base_url=(
            base_url
            or os.getenv("OPENAI_BASE_URL", "")
            or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        ).strip(),
        model_name=(model_name or os.getenv("MODEL_NAME", "") or "qwen-turbo").strip(),
    )


def get_client(api_key: str | None = None, base_url: str | None = None):
    """Compatibility client factory retained for existing imports and tests."""
    return build_client(_config(api_key, base_url, None))


def _messages(user_input: str, task_type: str | TaskType | None) -> list[dict[str, str]]:
    request = _build_request(user_input, task_type)
    retrieval = retrieve(request.retrieval_query)
    return build_initial_messages(request, retrieval)


def _raise_compat_error(exc: Exception, *, streaming: bool = False) -> None:
    del exc
    prefix = "模型流式调用失败" if streaming else "模型调用失败"
    raise RuntimeError(
        f"{prefix}，请检查 API Key、Base URL、模型名称和网络连接。"
    ) from None


def ask_agent(
    user_input: str,
    temperature: float = 0.62,
    max_tokens: int = 1600,
    api_key: str | None = None,
    base_url: str | None = None,
    model_name: str | None = None,
    task_type: str | TaskType | None = None,
) -> str:
    if not user_input.strip():
        return "请先输入你的需求，例如：我第一次来广州，有一天时间，想体验岭南非遗文化。"

    try:
        client = get_client(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=_config(api_key, base_url, model_name).model_name,
            messages=_messages(user_input, task_type),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        answer = response.choices[0].message.content
        if not answer:
            raise RuntimeError("模型返回内容为空。")
        return answer.strip()
    except Exception as exc:
        _raise_compat_error(exc)


def ask_agent_stream(
    user_input: str,
    temperature: float = 0.62,
    max_tokens: int = 1600,
    api_key: str | None = None,
    base_url: str | None = None,
    model_name: str | None = None,
    task_type: str | TaskType | None = None,
) -> Generator[str, None, None]:
    if not user_input.strip():
        yield "请先输入你的需求，例如：我第一次来广州，有一天时间，想体验岭南非遗文化。"
        return

    try:
        client = get_client(api_key=api_key, base_url=base_url)
        stream = client.chat.completions.create(
            model=_config(api_key, base_url, model_name).model_name,
            messages=_messages(user_input, task_type),
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content
    except Exception as exc:
        _raise_compat_error(exc, streaming=True)
