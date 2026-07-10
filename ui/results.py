from __future__ import annotations

import re

import streamlit as st

from core.models import TaskRequest, TaskType
from core.revisions import REVISION_PRESETS, RevisionPlan, plan_custom_revision, plan_quick_revision
from core.state import queue_revision, set_toast
from services.export import build_docx, build_markdown, build_plain_text
from services.output import sanitize_model_output
from ui.components import render_empty_state, render_result_overview, render_section_heading

_HEADING_PATTERN = re.compile(r"^(#{2,3})\s+(.+?)\s*$")


def split_markdown_sections(markdown: str) -> list[tuple[str, str]]:
    """把模型 Markdown 按二、三级标题拆成可用于 Tabs 的内容块。"""
    sections: list[tuple[str, str]] = []
    current_title = "方案概览"
    current_lines: list[str] = []

    for line in markdown.splitlines():
        match = _HEADING_PATTERN.match(line.strip())
        if match:
            body = "\n".join(current_lines).strip()
            if body:
                sections.append((current_title, body))
            current_title = match.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)

    body = "\n".join(current_lines).strip()
    if body:
        sections.append((current_title, body))

    return sections or [("完整内容", markdown.strip())]


def _select_section_content(
    sections: list[tuple[str, str]],
    keywords: tuple[str, ...],
    fallback: str,
) -> str:
    matched: list[str] = []
    for title, body in sections:
        if any(keyword in title for keyword in keywords):
            matched.append(f"### {title}\n\n{body}")
    return "\n\n".join(matched) if matched else fallback


def _render_sources(sources: str) -> None:
    if sources.strip():
        st.markdown(sources)
        st.caption("来源编号与正文中的 [S1]、[S2] 对应。实时开放、票务和演出信息仍请以官方平台为准。")
    else:
        st.info("当前结果没有可展示的知识来源记录。")


def _render_route_tabs(answer: str, sources: str) -> None:
    sections = split_markdown_sections(answer)
    route = _select_section_content(sections, ("总览", "路线", "行程", "时间轴", "节点"), answer)
    tips = _select_section_content(sections, ("体验", "记录", "提醒", "准备", "建议"), answer)
    tab_route, tab_tips, tab_full, tab_sources = st.tabs(
        ["🗺️ 路线视图", "🎒 体验提醒", "📄 完整方案", "📚 知识来源"]
    )
    with tab_route:
        st.markdown(route)
    with tab_tips:
        st.markdown(tips)
    with tab_full:
        st.markdown(answer)
    with tab_sources:
        _render_sources(sources)


def _render_study_tabs(answer: str, sources: str) -> None:
    sections = split_markdown_sections(answer)
    tasks = _select_section_content(sections, ("主题", "目标", "准备", "任务", "观察", "采访"), answer)
    report = _select_section_content(sections, ("记录", "报告", "提纲", "总结", "成果"), answer)
    tab_tasks, tab_report, tab_full, tab_sources = st.tabs(
        ["📚 研学任务", "📝 记录与报告", "📄 完整方案", "📚 知识来源"]
    )
    with tab_tasks:
        st.markdown(tasks)
    with tab_report:
        st.markdown(report)
    with tab_full:
        st.markdown(answer)
    with tab_sources:
        _render_sources(sources)


def _render_social_tabs(answer: str, sources: str) -> None:
    sections = split_markdown_sections(answer)
    copy = _select_section_content(sections, ("定位", "标题", "正文", "文案", "发布"), answer)
    assets = _select_section_content(sections, ("配图", "标签", "选题", "拍摄", "封面"), answer)
    tab_preview, tab_assets, tab_full, tab_sources = st.tabs(
        ["📱 发布预览", "📷 配图与标签", "📄 完整内容", "📚 知识来源"]
    )
    with tab_preview:
        st.markdown(copy)
    with tab_assets:
        st.markdown(assets)
    with tab_full:
        st.markdown(answer)
    with tab_sources:
        _render_sources(sources)


def _render_video_tabs(answer: str, sources: str) -> None:
    sections = split_markdown_sections(answer)
    storyboard = _select_section_content(sections, ("钩子", "分镜", "旁白", "字幕", "脚本"), answer)
    shooting = _select_section_content(sections, ("拍摄", "镜头", "标题", "标签", "建议"), answer)
    tab_storyboard, tab_shooting, tab_full, tab_sources = st.tabs(
        ["🎬 分镜脚本", "📹 拍摄建议", "📄 完整内容", "📚 知识来源"]
    )
    with tab_storyboard:
        st.markdown(storyboard)
    with tab_shooting:
        st.markdown(shooting)
    with tab_full:
        st.markdown(answer)
    with tab_sources:
        _render_sources(sources)


def _render_qa_tabs(answer: str, sources: str) -> None:
    sections = split_markdown_sections(answer)
    core = _select_section_content(sections, ("一句话", "背景", "核心", "看点", "解释"), answer)
    experience = _select_section_content(sections, ("体验", "方式", "地点", "建议", "提醒"), answer)
    tab_core, tab_experience, tab_sources = st.tabs(["💡 核心解答", "🧭 如何体验", "📚 知识来源"])
    with tab_core:
        st.markdown(core)
    with tab_experience:
        st.markdown(experience)
    with tab_sources:
        _render_sources(sources)


def _render_task_result(request: TaskRequest, answer: str, sources: str) -> None:
    task_type = request.task_type or TaskType.QA
    if task_type == TaskType.ROUTE:
        _render_route_tabs(answer, sources)
    elif task_type == TaskType.STUDY:
        _render_study_tabs(answer, sources)
    elif task_type == TaskType.SOCIAL:
        _render_social_tabs(answer, sources)
    elif task_type == TaskType.VIDEO:
        _render_video_tabs(answer, sources)
    else:
        _render_qa_tabs(answer, sources)


def _queue_revision_plan(plan: RevisionPlan, label: str) -> None:
    queue_revision(
        st.session_state,
        plan.instruction,
        plan.target_task_type,
        revised_request=plan.revised_request,
    )
    condition = f"{plan.revised_request.scene} · {plan.revised_request.duration}"
    set_toast(st.session_state, f"正在处理：{label}（{condition}）", "✨")
    st.rerun()


def _queue_quick_revision(request: TaskRequest, action: str) -> None:
    _queue_revision_plan(plan_quick_revision(request, action), action)


def _render_revision_panel(request: TaskRequest) -> None:
    with st.container(border=True):
        st.markdown("### ✨ 继续打磨")
        st.caption("快捷调整会同步更新当前方案的场景、时间和输出类型。")
        for action in REVISION_PRESETS:
            if st.button(
                action,
                key=f"revision_{action}",
                use_container_width=True,
                disabled=bool(st.session_state.pending_job),
            ):
                _queue_quick_revision(request, action)

        st.divider()
        custom_instruction = st.text_area(
            "自定义调整",
            key="custom_revision",
            height=95,
            placeholder="例如：压缩成半天，减少景点数量，增加拍照机位……",
            disabled=bool(st.session_state.pending_job),
        )
        if st.button(
            "按我的要求重新生成",
            key="submit_custom_revision",
            type="primary",
            use_container_width=True,
            disabled=bool(st.session_state.pending_job),
        ):
            if not custom_instruction.strip():
                st.warning("先写下你希望怎样调整。")
            else:
                plan = plan_custom_revision(request, custom_instruction)
                _queue_revision_plan(plan, "自定义调整")


def _render_downloads(request: TaskRequest, answer: str, sources: str) -> None:
    st.markdown("#### 保存这份方案")
    markdown = build_markdown(request, answer, sources)
    plain_text = build_plain_text(request, answer, sources)
    docx = build_docx(request, answer, sources)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "下载 Markdown",
            data=markdown.encode("utf-8"),
            file_name="yuejian_feiyi_result.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "下载 TXT",
            data=plain_text.encode("utf-8"),
            file_name="yuejian_feiyi_result.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with c3:
        st.download_button(
            "下载 Word",
            data=docx,
            file_name="yuejian_feiyi_result.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )


def render_results() -> None:
    render_section_heading(
        "RESULT",
        "你的非遗方案",
        "生成结果会根据任务类型自动拆成更适合阅读和使用的视图。",
    )

    root_payload = st.session_state.get("root_request")
    raw_answer = str(st.session_state.get("current_answer", ""))
    if not root_payload or not raw_answer.strip():
        render_empty_state()
        return

    request = TaskRequest.from_dict(root_payload)
    answer = sanitize_model_output(raw_answer)
    sources = str(st.session_state.get("current_sources", ""))
    render_result_overview(request)

    result_left, result_right = st.columns([2.35, 0.85], gap="large")
    with result_left:
        with st.container(border=True):
            _render_task_result(request, answer, sources)
        _render_downloads(request, answer, sources)

        history = st.session_state.get("revision_history", [])
        if history:
            with st.expander("查看方案调整记录", expanded=False):
                for item in history:
                    summary = f"{item.get('scene', '')} · {item.get('duration', '')}"
                    st.markdown(
                        f"- {item.get('created_at', '')} · {item.get('instruction', '')} · {summary}"
                    )

    with result_right:
        _render_revision_panel(request)
