from __future__ import annotations

import streamlit as st

from core.config import build_model_config
from core.models import ModelConfig, RevisionRequest, TaskRequest, TaskType
from core.state import (
    apply_pending_form_sync,
    complete_initial_generation,
    complete_revision,
    initialize_state,
    queue_initial_generation,
    set_toast,
)
from services.llm import ModelGatewayError, collect_stream_with_safe_fallback
from services.output import sanitize_model_output
from services.prompt_builder import build_initial_messages, build_revision_messages
from services.retrieval import KnowledgeBaseError, retrieve
from ui.components import render_request_summary, render_topbar_and_hero
from ui.results import render_results
from ui.sidebar import render_sidebar
from ui.styles import apply_styles
from ui.workspace import render_workspace

APP_BUILD_ID = "2026.07.10.5"


def _show_pending_toast() -> None:
    message = str(st.session_state.get("toast_message", ""))
    if not message:
        return
    st.toast(message, icon=st.session_state.get("toast_icon", "🦁"))
    st.session_state.toast_message = ""
    st.session_state.toast_icon = "🦁"


def _stream_answer(config: ModelConfig, messages: list[dict[str, str]]) -> str:
    placeholder = st.empty()
    final_answer = ""
    with st.status("正在检索知识并生成方案…", expanded=True) as status:
        st.write("正在读取结构化需求")
        st.write("正在检索广东非遗知识")
        st.write("正在生成并核对输出结构")
        for text, is_final in collect_stream_with_safe_fallback(
            config,
            messages,
            temperature=float(st.session_state.temperature),
        ):
            final_answer = sanitize_model_output(text)
            placeholder.markdown(final_answer if is_final else final_answer + "▌")
        status.update(label="方案已生成", state="complete", expanded=False)

    if not final_answer.strip():
        raise ModelGatewayError("模型没有返回可用内容。")
    return final_answer


def _process_pending_job() -> None:
    job = st.session_state.get("pending_job")
    if not job:
        return

    try:
        config = build_model_config(st.session_state)
        kind = job.get("kind")
        if kind == "initial":
            task_request = TaskRequest.from_dict(job["request"])
            retrieval = retrieve(task_request.retrieval_query)
            messages = build_initial_messages(task_request, retrieval)
            render_request_summary(task_request)
            answer = _stream_answer(config, messages)
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
            retrieval = retrieve(retrieval_query)
            messages = build_revision_messages(revision, retrieval)
            render_request_summary(effective_request)
            answer = _stream_answer(config, messages)
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
        st.error(str(exc))


def main() -> None:
    st.set_page_config(
        page_title="粤见非遗｜广东非遗体验工作台",
        page_icon="🦁",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    initialize_state(st.session_state)
    apply_pending_form_sync(st.session_state)
    apply_styles()
    render_sidebar()
    st.sidebar.caption(f"Build {APP_BUILD_ID}")
    _show_pending_toast()
    render_topbar_and_hero()

    request = render_workspace()
    if request is not None:
        try:
            build_model_config(st.session_state)
        except ValueError as exc:
            st.warning(str(exc))
        else:
            queue_initial_generation(st.session_state, request)
            set_toast(st.session_state, "已收到需求，正在生成方案…", "🦁")
            st.rerun()

    _process_pending_job()
    render_results()


if __name__ == "__main__":
    main()
