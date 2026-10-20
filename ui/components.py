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
    brand_col, nav_col = st.columns([1.35, 1.15], vertical_alignment="center")
    with brand_col:
        st.html(
            """
            <div class="topbar-left">
                <div class="topbar-logo" aria-hidden="true">粤</div>
                <div class="editorial-brand-copy">
                    <span>粤见非遗</span>
                    <span class="editorial-brand-sub">YUEJIAN · LINGNAN HERITAGE STUDIO</span>
                </div>
            </div>
            """
        )

    with nav_col:
        st.html('<div class="topbar-nav-label">EXPLORE / 探索体验</div>')
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
    st.html(
        f"""
        <section class="editorial-hero" aria-label="粤见非遗，岭南文化体验">
            <div class="editorial-hero-art">
                <img src="{hero_uri}"
                    alt="岭南非遗主题插画，包含醒狮、粤剧、广绣、陶塑与岭南建筑"
                    loading="eager" decoding="async"/>
            </div>
            <div class="editorial-hero-content">
                <div class="editorial-hero-eyebrow">LINGNAN · CULTURE IN MOTION</div>
                <h1>遇见岭南，<br/><span>让非遗可感。</span></h1>
                <p class="editorial-hero-desc">
                    从一段城市漫游，到一场亲子研学。<br/>
                    以文化为起点，用 AI 定制属于你的广东非遗体验。
                </p>
                <div class="editorial-hero-foot">
                    <div class="editorial-hero-seal">粤<br/>见</div>
                    <div class="editorial-hero-meta">
                        <strong>一处入口，五种探索方式</strong><br/>
                        智能路线 · 文化研学 · 亲子体验 · 创意表达
                    </div>
                </div>
            </div>
        </section>
        <div class="editorial-ribbon">
            <div><span>01</span>选择场景 &nbsp; / &nbsp; <span>02</span>描述需求 &nbsp; / &nbsp; <span>03</span>获取方案</div>
            <div>EXPLORE THE LIVING HERITAGE OF GUANGDONG</div>
        </div>
        """
    )

def render_section_heading(kicker: str, title: str, copy: str) -> None:
    st.html(
        f"""
        <div class="section-heading">
            <div class="section-eyebrow">{html.escape(kicker)}</div>
            <div class="section-title">{html.escape(title)}</div>
            <div class="section-copy">{html.escape(copy)}</div>
        </div>
        """
    )

def render_scene_note(scene: str) -> None:
    icon = SCENE_ICONS.get(scene, "🦁")
    description = SCENE_DESCRIPTIONS.get(scene, "生成广东非遗文化方案。")
    public_name = SCENE_PUBLIC_NAMES.get(scene, scene)
    st.html(
        f"""
        <div class="scene-note">
            <div class="scene-title">{icon} 已选择：{html.escape(public_name)}</div>
            <div class="scene-desc">{html.escape(description)}</div>
        </div>
        """
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
    st.html(
        f"""
        <div class="request-summary">
            <div class="request-icon">🍊</div>
            <div>
                <div class="request-label">本次需求</div>
                <div class="request-main">{html.escape(request.raw_request)}</div>
                <div class="request-meta">{html.escape(conditions)}</div>
            </div>
        </div>
        """
    )


def render_empty_state() -> None:
    st.html(
        """
        <section class="empty-state">
            <div class="empty-icon" aria-hidden="true">✦</div>
            <div class="empty-title">下一段非遗故事，等你开启。</div>
            <div class="empty-copy">选择上方场景，描述想去的城市、同行的人或感兴趣的技艺。这里将呈现一份兼具文化背景、行动建议与参考资料的专属体验方案。</div>
            <div class="empty-features">
                <div class="empty-feature"><span>01 / DISCOVER</span>城市文化路线<small>把非遗地标串成有节奏的探索旅程</small></div>
                <div class="empty-feature"><span>02 / LEARN</span>研学与亲子体验<small>让传统技艺成为可以参与的课堂</small></div>
                <div class="empty-feature"><span>03 / CREATE</span>文化内容创作<small>将所见所感转化为文字与视频灵感</small></div>
            </div>
        </section>
        """
    )

def render_result_overview(request: TaskRequest) -> None:
    title = SCENE_PUBLIC_NAMES.get(request.scene, request.scene)
    interests = "、".join(request.interests) if request.interests else "智能匹配"
    st.html(
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
        """
    )
