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

TOP_NAV_SCENES = (
    ("路线规划", "游客路线"),
    ("研学任务", "学生研学"),
    ("内容创作", "内容创作"),
)


@lru_cache(maxsize=8)
def asset_data_uri(filename: str) -> str:
    """读取本地图片并转换成可直接嵌入网页的 Data URI。"""
    path = ASSET_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"缺少页面素材：{filename}")

    mime = "image/webp" if path.suffix.lower() == ".webp" else "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _switch_top_nav_scene(scene: str) -> None:
    st.session_state["selected_scene"] = scene
    st.session_state["last_scene"] = scene


def _render_topbar() -> None:
    brand_col, nav_col = st.columns([1.45, 1.0], vertical_alignment="center")
    with brand_col:
        st.markdown(
            """
            <div class="topbar-left">
                <div class="topbar-logo">粤</div>
                <div>粤见非遗</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with nav_col:
        columns = st.columns(len(TOP_NAV_SCENES), gap="small")
        current_scene = str(st.session_state.get("selected_scene", "游客路线"))
        for column, (label, scene) in zip(columns, TOP_NAV_SCENES, strict=True):
            with column:
                st.button(
                    label,
                    key=f"topnav_{scene}",
                    type="primary" if current_scene == scene else "secondary",
                    use_container_width=True,
                    disabled=bool(st.session_state.get("pending_job")),
                    on_click=_switch_top_nav_scene,
                    args=(scene,),
                )


def render_topbar_and_hero() -> None:
    hero_uri = asset_data_uri("readme_hero_lingnan.png")
    _render_topbar()
    st.markdown(
        f"""
        <style>
        .hero-image-banner {{
            position: relative;
            min-height: 286px;
            overflow: hidden;
            border-radius: 24px;
            margin: .58rem 0 1rem;
            background: #f7f0e7;
            box-shadow: 0 16px 38px rgba(22, 50, 79, .10);
            isolation: isolate;
        }}
        .hero-image-bg {{
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: 63% center;
            z-index: 0;
        }}
        .hero-image-banner::after {{
            content: "";
            position: absolute;
            inset: 0;
            z-index: 1;
            background: linear-gradient(
                90deg,
                rgba(250, 247, 240, .985) 0%,
                rgba(250, 247, 240, .94) 31%,
                rgba(250, 247, 240, .70) 48%,
                rgba(250, 247, 240, .06) 72%
            );
        }}
        .hero-image-content {{
            position: relative;
            z-index: 2;
            max-width: 52%;
            padding: 1.55rem 1.8rem 1.45rem;
        }}
        .hero-image-kicker {{
            display: inline-flex;
            padding: .31rem .62rem;
            color: #0f6f72;
            background: rgba(255, 255, 255, .78);
            border: 1px solid rgba(21, 154, 156, .14);
            border-radius: 999px;
            font-size: .76rem;
            font-weight: 820;
        }}
        .hero-image-title {{
            max-width: 650px;
            margin: .62rem 0 .38rem;
            color: #16324f !important;
            font-size: 2.38rem;
            line-height: 1.10;
            font-weight: 940;
            letter-spacing: .012em;
        }}
        .hero-image-subtitle {{
            max-width: 600px;
            color: #425f70;
            font-size: .94rem;
            line-height: 1.62;
            font-weight: 620;
        }}
        .hero-image-chips {{
            display: flex;
            flex-wrap: wrap;
            gap: .36rem;
            margin-top: .72rem;
        }}
        .hero-image-chip {{
            padding: .29rem .56rem;
            color: #16324f;
            background: rgba(255, 255, 255, .78);
            border: 1px solid rgba(22, 50, 79, .08);
            border-radius: 999px;
            font-size: .72rem;
            font-weight: 730;
        }}
        @media (max-width: 920px) {{
            .hero-image-banner {{ min-height: 330px; border-radius: 20px; }}
            .hero-image-bg {{ object-position: 72% center; }}
            .hero-image-banner::after {{
                background: linear-gradient(
                    90deg,
                    rgba(250, 247, 240, .985) 0%,
                    rgba(250, 247, 240, .94) 58%,
                    rgba(250, 247, 240, .44) 100%
                );
            }}
            .hero-image-content {{ max-width: 100%; padding: 1.35rem 1rem; }}
            .hero-image-title {{ max-width: 82%; font-size: 1.92rem; }}
            .hero-image-subtitle {{ max-width: 78%; font-size: .88rem; }}
        }}
        </style>
        <div class="hero-image-banner">
            <img
                class="hero-image-bg"
                src="{hero_uri}"
                alt="醒狮、粤剧、广绣、陶塑与岭南建筑组成的广东非遗插画"
                loading="eager"
                decoding="async"
            />
            <div class="hero-image-content">
                <div class="hero-image-kicker">寻脉岭南 · 智游非遗</div>
                <h1 class="hero-image-title">一句话，规划你的岭南非遗体验</h1>
                <div class="hero-image-subtitle">
                    说清楚去哪里、和谁、想体验什么，粤见非遗会为你生成可出发、可研学、可发布的完整方案。
                </div>
                <div class="hero-image-chips">
                    <span class="hero-image-chip">城市文化路线</span>
                    <span class="hero-image-chip">研学任务卡</span>
                    <span class="hero-image-chip">亲子互动</span>
                    <span class="hero-image-chip">图文与短视频</span>
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
