from __future__ import annotations

import logging
from collections.abc import Callable
from time import perf_counter
from typing import Any

import streamlit as st

from core.config import build_model_config, debug_ui_enabled, user_api_configured
from core.models import ModelConfig, RetrievalBundle, RevisionRequest, TaskRequest, TaskType
from core.state import (
    apply_pending_form_sync,
    complete_initial_generation,
    complete_revision,
    initialize_state,
    queue_initial_generation,
    set_toast,
)
from services.llm import (
    ModelGatewayError,
    collect_stream_with_safe_fallback,
    model_runtime_summary,
)
from services.output import sanitize_model_output
from services.prompt_builder import build_initial_messages, build_revision_messages
from services.retrieval import KnowledgeBaseError, retrieve
from ui.components import render_request_summary, render_topbar_and_hero
from ui.mobile_styles import apply_mobile_styles
from ui.results import render_results
from ui.sidebar import render_sidebar
from ui.styles import apply_styles
from ui.workspace import WORKSPACE_UI_BUILD_ID, render_workspace

logger = logging.getLogger(__name__)

APP_BUILD_ID = "2026.08.24.1"
GENERATION_RETRIEVAL_TOP_K = 3
GENERATION_RETRIEVAL_CHAR_BUDGET = 2200


HERO_LAYER_FIX_CSS = """
<style>
.hero-image-bg {
    z-index: 0 !important;
}
.hero-image-banner::after {
    z-index: 1 !important;
    pointer-events: none;
}
.hero-image-content {
    position: relative;
    z-index: 2 !important;
}
</style>
"""


def _show_pending_toast() -> None:
    message = str(st.session_state.get("toast_message", ""))
    if not message:
        return
    st.toast(message, icon=st.session_state.get("toast_icon", "🦁"))
    st.session_state.toast_message = ""
    st.session_state.toast_icon = "🦁"


def _stream_answer(
    config: ModelConfig,
    messages: list[dict[str, str]],
    *,
    answer_placeholder: Any,
    model_line: Any,
    status: Any,
    started_at: float,
) -> str:
    final_answer = ""
    first_token_seconds: float | None = None
    runtime_label = model_runtime_summary(config)
    debug = debug_ui_enabled()

    for text, is_final in collect_stream_with_safe_fallback(
        config,
        messages,
        temperature=float(st.session_state.temperature),
    ):
        if first_token_seconds is None:
            first_token_seconds = perf_counter() - started_at
            if debug:
                model_line.markdown(
                    f"✓ {runtime_label} 首字响应 · {first_token_seconds:.1f}s，正在继续生成…"
                )
            status.update(label="正在生成专属方案…")
        final_answer = sanitize_model_output(text)
        answer_placeholder.markdown(final_answer if is_final else final_answer + "▌")

    generation_seconds = perf_counter() - started_at
    logger.info(
        "Generation completed: model=%s first_token=%.3fs total=%.3fs",
        runtime_label,
        first_token_seconds or generation_seconds,
        generation_seconds,
    )
    if debug:
        model_line.markdown(f"✓ {runtime_label} 生成完成 · {generation_seconds:.1f}s")
    else:
        model_line.markdown("✓ 专属方案已生成")

    if not final_answer.strip():
        raise ModelGatewayError("模型没有返回可用内容。")
    return final_answer


def _generate_with_progress(
    config: ModelConfig,
    retrieval_query: str,
    message_builder: Callable[[RetrievalBundle], list[dict[str, str]]],
) -> tuple[str, RetrievalBundle]:
    answer_placeholder = st.empty()
    overall_started = perf_counter()
    debug = debug_ui_enabled()

    with st.status("正在为你生成方案…", expanded=True) as status:
        request_line = st.empty()
        retrieval_line = st.empty()
        model_line = st.empty()

        request_line.markdown("✓ 已理解你的需求")
        retrieval_line.markdown("◌ 正在整理相关非遗资料…")
        status.update(label="正在整理相关非遗资料…")

        retrieval_started = perf_counter()
        retrieval = retrieve(
            retrieval_query,
            top_k=GENERATION_RETRIEVAL_TOP_K,
            max_total_chars=GENERATION_RETRIEVAL_CHAR_BUDGET,
        )
        retrieval_seconds = perf_counter() - retrieval_started
        logger.info(
            "Retrieval completed: chunks=%d duration=%.3fs",
            len(retrieval.chunks),
            retrieval_seconds,
        )
        if debug:
            retrieval_line.markdown(
                f"✓ 检索完成 · {len(retrieval.chunks)} 条相关资料 · {retrieval_seconds:.2f}s"
            )
        else:
            retrieval_line.markdown("✓ 已整理相关非遗资料")

        messages = message_builder(retrieval)
        if debug:
            model_line.markdown(
                f"◌ {model_runtime_summary(config)} · 正在等待首字响应…"
            )
        else:
            model_line.markdown("◌ 正在生成专属方案…")
        status.update(label="正在生成专属方案…")

        answer = _stream_answer(
            config,
            messages,
            answer_placeholder=answer_placeholder,
            model_line=model_line,
            status=status,
            started_at=perf_counter(),
        )
        total_seconds = perf_counter() - overall_started
        logger.info("Generation workflow completed in %.3fs", total_seconds)
        label = f"方案已生成 · {total_seconds:.1f}s" if debug else "方案已生成"
        status.update(label=label, state="complete", expanded=False)

    return answer, retrieval


def _render_gateway_recovery_hint() -> None:
    if user_api_configured(st.session_state):
        st.info("当前 AI 服务暂时不可用。你已连接自己的 API，可在“AI 服务”中切换后重试。")
    else:
        st.info("当前 AI 服务暂时不可用，请稍后重试。你也可以在“AI 服务”中连接自己的 API。")


def _render_generation_error(
    exc: Exception,
    *,
    config: ModelConfig | None,
) -> None:
    debug = debug_ui_enabled()
    if isinstance(exc, ModelGatewayError):
        if config is not None and config.credential_source == "user":
            st.error(str(exc))
        else:
            st.error("暂时无法生成方案，请稍后重试。")
            _render_gateway_recovery_hint()
    elif isinstance(exc, KnowledgeBaseError):
        st.error("相关资料暂时无法整理，请稍后重试。")
    else:
        st.error("当前请求暂时无法处理，请重新提交。")

    if debug:
        st.caption(f"诊断信息：{exc}")


def _process_pending_job() -> None:
    job = st.session_state.get("pending_job")
    if not job:
        return

    config: ModelConfig | None = None
    try:
        config = build_model_config(st.session_state)
        kind = job.get("kind")
        if kind == "initial":
            task_request = TaskRequest.from_dict(job["request"])
            render_request_summary(task_request)
            answer, retrieval = _generate_with_progress(
                config,
                task_request.retrieval_query,
                lambda bundle: build_initial_messages(task_request, bundle),
            )
            complete_initial_generation(
                st.session_state,
                task_request,
                answer,
                retrieval.source_markdown(),
            )
        elif kind == "revision":
            effective_request = TaskRequest.from_dict(
                job.get("revised_request") or job["root_request"]
            )
            revision = RevisionRequest(
                root_request=effective_request,
                current_answer=job["current_answer"],
                instruction=job["instruction"],
                target_task_type=TaskType(job["target_task_type"]),
            )
            retrieval_query = f"{effective_request.retrieval_query} {revision.instruction}"
            render_request_summary(effective_request)
            answer, retrieval = _generate_with_progress(
                config,
                retrieval_query,
                lambda bundle: build_revision_messages(revision, bundle),
            )
            complete_revision(
                st.session_state,
                revision.instruction,
                revision.target_task_type,
                answer,
                retrieval.source_markdown(),
                revised_request=effective_request,
            )
        else:
            raise ValueError("未知生成任务。")

        set_toast(st.session_state, "方案已生成，可以继续优化或下载", "✅")
        st.rerun()
    except (ValueError, KnowledgeBaseError, ModelGatewayError) as exc:
        st.session_state.pending_job = None
        _render_generation_error(exc, config=config)


def _render_model_unavailable_notice(exc: ValueError) -> None:
    st.warning("AI 服务暂时不可用，请稍后重试，或在侧边栏“AI 服务”中连接自己的 API。")
    if debug_ui_enabled():
        st.caption(f"诊断信息：{exc}")


def main() -> None:
    st.set_page_config(
        page_title="粤见非遗｜广东非遗体验工作台",
        page_icon="🦁",
        layout="wide",
        initial_sidebar_state="auto",
    )

    initialize_state(st.session_state)
    apply_pending_form_sync(st.session_state)
    apply_styles()
    apply_mobile_styles()
    st.markdown(HERO_LAYER_FIX_CSS, unsafe_allow_html=True)
    render_sidebar()
    if debug_ui_enabled():
        st.sidebar.caption(f"Build {APP_BUILD_ID} · UI {WORKSPACE_UI_BUILD_ID}")
    _show_pending_toast()
    render_topbar_and_hero()

    request = render_workspace()
    if request is not None:
        try:
            build_model_config(st.session_state)
        except ValueError as exc:
            _render_model_unavailable_notice(exc)
        else:
            queue_initial_generation(st.session_state, request)
            set_toast(st.session_state, "已收到需求，正在生成方案…", "🦁")
            st.rerun()

    _process_pending_job()
    render_results()


if __name__ == "__main__":
    main()
