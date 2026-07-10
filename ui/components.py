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

SCENE_PUBLIC_NAMES = {
    "游客路线": "城市漫游",
    "学生研学": "研学探索",
    "亲子体验": "亲子体验",
    "内容创作": "内容创作",
    "非遗问答": "非遗问答",
}


def render_topbar_and_hero() -> None:
    st.markdown(
        """
        <div class="topbar">
            <div class="topbar-left">
                <div class="topbar-logo">粤</div>
                <div>粤见非遗</div>
            </div>
            <div class="topbar-nav">
                <span class="topbar-pill">路线规划</span>
                <span class="topbar-pill">研学任务</span>
                <span class="topbar-pill">内容创作</span>
            </div>
        </div>
        <div class="hero">
            <div class="hero-grid">
                <div>
                    <div class="hero-kicker">🦁 寻脉岭南，智游非遗</div>
                    <h1 class="hero-title">一句话，规划你的岭南非遗体验</h1>
                    <div class="hero-subtitle">
                        说清楚去哪里、和谁、想体验什么，粤见非遗会为你生成可出发、可研学、可发布的完整方案。
                    </div>
                    <div class="hero-chips">
                        <span class="hero-chip">🧭 城市文化路线</span>
                        <span class="hero-chip">📚 研学任务卡</span>
                        <span class="hero-chip">👨‍👩‍👧 亲子互动</span>
                        <span class="hero-chip">🎬 图文与短视频</span>
                    </div>
                </div>
                <div class="hero-art" aria-hidden="true">
                    <div class="hero-seal">獅</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_heading(kicker: str, title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="section-heading">
            <div class="section-eyebrow">{html.escape(kicker)}</div>
            <div class="section-title">{html.escape(title)}</div>
            <div class="section-copy">{html.escape(copy)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_scene_note(scene: str) -> None:
    icon = SCENE_ICONS.get(scene, "🦁")
    description = SCENE_DESCRIPTIONS.get(scene, "生成广东非遗文化方案。")
    public_name = SCENE_PUBLIC_NAMES.get(scene, scene)
    st.markdown(
        f"""
        <div class="scene-note">
            <div class="scene-title">{icon} 已选择：{html.escape(public_name)}</div>
            <div class="scene-desc">{html.escape(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_request_summary(request: TaskRequest) -> None:
    conditions = " · ".join(
        [
            SCENE_PUBLIC_NAMES.get(request.scene, request.scene),
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


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-icon">🪭</div>
            <div class="empty-title">你的岭南非遗方案会出现在这里</div>
            <div class="empty-copy">先选择一个场景，再写下一句话需求。路线、任务卡、文案和来源都会自动整理好。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result_overview(request: TaskRequest) -> None:
    title = SCENE_PUBLIC_NAMES.get(request.scene, request.scene)
    interests = "、".join(request.interests) if request.interests else "智能匹配"
    st.markdown(
        f"""
        <div class="result-hero">
            <div class="result-label">已生成 · {html.escape(title)}</div>
            <div class="result-title">{html.escape(request.raw_request)}</div>
            <div class="result-meta">{html.escape(request.city)} · {html.escape(request.duration)} · 兴趣：{html.escape(interests)}</div>
        </div>
        <div class="fact-grid">
            <div class="fact-card"><div class="fact-label">适用身份</div><div class="fact-value">{html.escape(request.identity)}</div></div>
            <div class="fact-card"><div class="fact-label">输出风格</div><div class="fact-value">{html.escape(request.output_style)}</div></div>
            <div class="fact-card"><div class="fact-label">当前用途</div><div class="fact-value">{html.escape(title)}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
