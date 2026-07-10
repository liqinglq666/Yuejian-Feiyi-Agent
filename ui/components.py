from __future__ import annotations

import base64
import html
from functools import lru_cache
from pathlib import Path

import streamlit as st

from core.models import TaskRequest

ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"

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


@lru_cache(maxsize=8)
def asset_data_uri(filename: str) -> str:
    """读取本地图片并转换成可直接嵌入网页的 Data URI。"""
    path = ASSET_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"缺少页面素材：{filename}")

    mime = "image/webp" if path.suffix.lower() == ".webp" else "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def render_topbar_and_hero() -> None:
    hero_uri = asset_data_uri("readme_hero_lingnan.png")
    st.markdown(
        f"""
        <style>
        .hero-image-banner {{
            position: relative;
            min-height: 340px;
            overflow: hidden;
            border-radius: 30px;
            margin-bottom: 1.25rem;
            background: #f7f0e7;
            box-shadow: 0 26px 62px rgba(22, 50, 79, .15);
            isolation: isolate;
        }}
        .hero-image-bg {{
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: center center;
            z-index: 0;
        }}
        .hero-image-banner::after {{
            content: "";
            position: absolute;
            inset: 0;
            z-index: 1;
            background: linear-gradient(
                90deg,
                rgba(250, 247, 240, .98) 0%,
                rgba(250, 247, 240, .93) 34%,
                rgba(250, 247, 240, .62) 52%,
                rgba(250, 247, 240, .08) 73%
            );
        }}
        .hero-image-content {{
            position: relative;
            z-index: 2;
            max-width: 55%;
            padding: 2.1rem 2.2rem;
        }}
        .hero-image-kicker {{
            display: inline-flex;
            padding: .36rem .7rem;
            color: #0f6f72;
            background: rgba(255, 255, 255, .76);
            border: 1px solid rgba(21, 154, 156, .16);
            border-radius: 999px;
            font-size: .8rem;
            font-weight: 850;
            backdrop-filter: blur(10px);
        }}
        .hero-image-title {{
            max-width: 670px;
            margin: .72rem 0 .45rem;
            color: #16324f !important;
            font-size: 2.75rem;
            line-height: 1.08;
            font-weight: 950;
            letter-spacing: .018em;
        }}
        .hero-image-subtitle {{
            max-width: 620px;
            color: #425f70;
            font-size: 1rem;
            line-height: 1.72;
            font-weight: 640;
        }}
        .hero-image-chips {{
            display: flex;
            flex-wrap: wrap;
            gap: .42rem;
            margin-top: .9rem;
        }}
        .hero-image-chip {{
            padding: .34rem .64rem;
            color: #16324f;
            background: rgba(255, 255, 255, .76);
            border: 1px solid rgba(22, 50, 79, .09);
            border-radius: 999px;
            font-size: .76rem;
            font-weight: 760;
            backdrop-filter: blur(10px);
        }}
        @media (max-width: 920px) {{
            .hero-image-banner {{ min-height: 395px; }}
            .hero-image-bg {{ object-position: 70% center; }}
            .hero-image-banner::after {{
                background: linear-gradient(
                    90deg,
                    rgba(250, 247, 240, .98) 0%,
                    rgba(250, 247, 240, .94) 56%,
                    rgba(250, 247, 240, .48) 100%
                );
            }}
            .hero-image-content {{ max-width: 100%; padding: 1.55rem 1.2rem; }}
            .hero-image-title {{ max-width: 82%; font-size: 2.15rem; }}
            .hero-image-subtitle {{ max-width: 78%; font-size: .93rem; }}
        }}
        </style>
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
        <div class="hero-image-banner">
            <img
                class="hero-image-bg"
                src="{hero_uri}"
                alt="醒狮、粤剧、广绣、陶塑与岭南建筑组成的广东非遗插画"
                loading="eager"
                decoding="async"
            />
            <div class="hero-image-content">
                <div class="hero-image-kicker">🦁 寻脉岭南，智游非遗</div>
                <h1 class="hero-image-title">一句话，规划你的岭南非遗体验</h1>
                <div class="hero-image-subtitle">
                    说清楚去哪里、和谁、想体验什么，粤见非遗会为你生成可出发、可研学、可发布的完整方案。
                </div>
                <div class="hero-image-chips">
                    <span class="hero-image-chip">🧭 城市文化路线</span>
                    <span class="hero-image-chip">📚 研学任务卡</span>
                    <span class="hero-image-chip">👨‍👩‍👧 亲子互动</span>
                    <span class="hero-image-chip">🎬 图文与短视频</span>
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
