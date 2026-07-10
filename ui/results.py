from __future__ import annotations

import streamlit as st

from core.models import TaskRequest, TaskType, task_type_for_action
from core.state import queue_revision, set_toast
from services.export import build_docx, build_markdown, build_plain_text
from services.output import sanitize_model_output
from ui.components import render_request_summary

REVISION_ACTIONS: dict[str, str] = {
    "压缩成半天": "把方案压缩成半天，保留最值得体验的节点，并减少往返。",
    "更适合亲子": "改成适合亲子家庭的版本，增加孩子能参与的互动任务，节奏轻松。",
    "生成小红书文案": "改写成一篇可直接发布的小红书图文，包含标题、正文、配图建议和标签。",
    "生成短视频脚本": "改写成一条 60 秒短视频脚本，包含分镜、旁白、字幕和拍摄建议。",
    "加研学记录表": "改写成研学方案，并补充可填写的观察记录表、采访问题和报告提纲。",
}


def render_results() -> None:
    st.markdown("## 方案结果")

    root_payload = st.session_state.get("root_request")
    answer = str(st.session_state.get("current_answer", ""))
    if not root_payload or not answer.strip():
        st.info("还没有生成内容。填写需求后点击“生成方案”。")
        return

    request = TaskRequest.from_dict(root_payload)
    render_request_summary(request)

    result_left, result_right = st.columns([2.25, 0.95], gap="large")
    with result_left:
        st.markdown(
            '<div class="answer-shell"><div class="answer-header">🦁 粤见非遗为你生成</div>',
            unsafe_allow_html=True,
        )
        st.markdown(sanitize_model_output(answer))
        st.markdown("</div>", unsafe_allow_html=True)

        sources = str(st.session_state.get("current_sources", ""))
        if sources.strip():
            with st.expander("查看本次知识来源", expanded=False):
                st.markdown(sources)

        history = st.session_state.get("revision_history", [])
        if history:
            with st.expander("查看调整记录", expanded=False):
                for item in history:
                    st.markdown(f"- {item.get('created_at', '')} · {item.get('instruction', '')}")

    with result_right:
        with st.container(border=True):
            st.markdown("### ⚡ 继续调整")
            for action, instruction in REVISION_ACTIONS.items():
                if st.button(
                    action,
                    key=f"revision_{action}",
                    use_container_width=True,
                    disabled=bool(st.session_state.pending_job),
                ):
                    fallback = request.task_type or TaskType.QA
                    target_type = task_type_for_action(action, fallback)
                    queue_revision(st.session_state, instruction, target_type)
                    set_toast(st.session_state, f"正在处理：{action}", "✨")
                    st.rerun()

            st.divider()
            st.markdown("### 📦 保存方案")
            markdown = build_markdown(request, answer, st.session_state.get("current_sources", ""))
            plain_text = build_plain_text(request, answer, st.session_state.get("current_sources", ""))
            docx = build_docx(request, answer, st.session_state.get("current_sources", ""))

            st.download_button(
                "下载 Markdown",
                data=markdown.encode("utf-8"),
                file_name="yuejian_feiyi_result.md",
                mime="text/markdown",
                use_container_width=True,
            )
            st.download_button(
                "下载 TXT",
                data=plain_text.encode("utf-8"),
                file_name="yuejian_feiyi_result.txt",
                mime="text/plain",
                use_container_width=True,
            )
            st.download_button(
                "下载 Word",
                data=docx,
                file_name="yuejian_feiyi_result.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
