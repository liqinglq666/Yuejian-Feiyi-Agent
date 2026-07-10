from __future__ import annotations

import html

import streamlit as st

from core.models import TaskRequest

SCENE_DESCRIPTIONS = {
    "游客路线": "生成城市文化路线、每站看点、体验建议与出发提醒。",
    "学生研学": "生成研学主题、观察任务、采访问题、记录表和报告提纲。",
    "亲子体验": "生成轻松路线、孩子互动任务、休息节奏和安全提醒。",
    "内容创作": "生成标题、完整文案、配图建议和传播标签。",
    "非遗问答": "解释非遗背景、核心看点和适合的体验方式。",
}

SCENE_ICONS = {
    "游客路线": "🧭",
    "学生研学": "📚",
    "亲子体验": "👨‍👩‍👧",
    "内容创作": "🎬",
    "非遗问答": "🦁",
}


def render_topbar_and_hero() -> None:
    st.markdown(
        """
        <div class="topbar">
            <div class="topbar-left"><div class="topbar-logo">粤</div><div>粤见非遗</div></div>
            <div class="topbar-pill">广东非遗体验工作台 · Agent v2</div>
        </div>
        <div class="hero">
            <div class="hero-kicker">🦁 寻脉岭南，智游非遗</div>
            <h1 class="hero-title">粤见非遗</h1>
            <div class="hero-subtitle">从一句需求开始，检索广东非遗知识，生成可出发、可研学、可发布的文化体验方案。</div>
            <div class="hero-chips">
                <span class="hero-chip">显式任务路由</span>
                <span class="hero-chip">混合知识检索</span>
                <span class="hero-chip">来源标注</span>
                <span class="hero-chip">连续优化不套娃</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_scene_note(scene: str) -> None:
    icon = SCENE_ICONS.get(scene, "🦁")
    description = SCENE_DESCRIPTIONS.get(scene, "生成广东非遗文化方案。")
    st.markdown(
        f"""
        <div class="scene-note">
            <div class="scene-title">{icon} 当前用途：{html.escape(scene)}</div>
            <div class="scene-desc">{html.escape(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_request_summary(request: TaskRequest) -> None:
    conditions = " · ".join(
        [
            request.scene,
            request.city,
            request.duration,
            request.identity,
            request.output_style,
        ]
    )
    st.markdown(
        f"""
        <div class="request-summary">
            <div class="request-icon">🍊</div>
            <div>
                <div class="request-label">本次需求</div>
                <div class="request-main">{html.escape(request.raw_request)}</div>
                <div class="request-meta">{html.escape(conditions)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
