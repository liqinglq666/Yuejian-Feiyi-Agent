from __future__ import annotations

import html
from collections.abc import MutableMapping
from dataclasses import dataclass
from typing import Any

import streamlit as st

from core.config import active_model_source, platform_service_ready, user_api_configured
from core.models import GUANGDONG_CITIES, MAX_RAW_REQUEST_CHARS, TaskRequest, TaskType
from ui.components import (
    SCENE_DESCRIPTIONS,
    SCENE_PUBLIC_NAMES,
    render_scene_note,
    render_section_heading,
)

WORKSPACE_UI_BUILD_ID = "2026.10.20.editorial"

SCENES: dict[str, tuple[str, str]] = {
    "游客路线": ("🧭", "自动规划非遗路线"),
    "学生研学": ("📚", "生成任务卡与报告提纲"),
    "亲子体验": ("👨‍👩‍👧", "轻松、安全、可互动"),
    "内容创作": ("🎬", "图文与短视频成品"),
    "非遗问答": ("🦁", "快速理解文化与技艺"),
}


@dataclass(frozen=True)
class ExamplePreset:
    scene: str
    text: str
    city: str
    duration: str
    identity: str
    interests: tuple[str, ...]
    output_style: str
    content_format: str = "图文"


EXAMPLES: dict[str, ExamplePreset] = {
    "广州一日路线": ExamplePreset(
        scene="游客路线",
        text="我第一次来广州，有一天时间，想体验岭南非遗文化，最好适合拍照和写研学记录。",
        city="广州",
        duration="一天",
        identity="外地游客",
        interests=("非遗", "拍照", "研学"),
        output_style="游客友好",
    ),
    "高中研学任务": ExamplePreset(
        scene="学生研学",
        text="我是高中生，要做一份广东非遗研学报告，请设计围绕粤剧、醒狮和广绣的任务卡。",
        city="自动判断",
        duration="一天",
        identity="学生研学",
        interests=("粤剧", "醒狮", "广绣", "研学"),
        output_style="研学报告",
    ),
    "佛山亲子体验": ExamplePreset(
        scene="亲子体验",
        text="我周末带孩子去佛山，想体验醒狮和石湾陶塑，节奏轻松一点。",
        city="佛山",
        duration="周末",
        identity="亲子家庭",
        interests=("醒狮", "非遗"),
        output_style="游客友好",
    ),
    "英歌舞图文": ExamplePreset(
        scene="内容创作",
        text="帮我写一篇介绍潮汕英歌舞的图文内容，适合小红书发布。",
        city="汕头",
        duration="不限",
        identity="内容创作者",
        interests=("非遗", "拍照"),
        output_style="小红书风格",
        content_format="图文",
    ),
}

CITIES = ["自动判断", *GUANGDONG_CITIES]
DURATIONS = ["自动判断", "半天", "一天", "两天", "周末", "不限"]
IDENTITIES = ["自动匹配", "外地游客", "学生研学", "亲子家庭", "本地居民", "内容创作者"]
INTERESTS = [
    "非遗",
    "岭南建筑",
    "粤剧",
    "醒狮",
    "广绣",
    "龙舟",
    "潮汕工夫茶",
    "美食",
    "拍照",
    "研学",
    "短视频",
]


def apply_example(
    state: MutableMapping[str, Any],
    scene: str,
    text: str,
    city: str = "自动判断",
    duration: str = "自动判断",
    identity: str = "自动匹配",
    interests: tuple[str, ...] = (),
    output_style: str = "清晰实用",
    content_format: str = "图文",
) -> None:
    state["selected_scene"] = scene
    state["last_scene"] = scene
    state["user_input"] = text
    state["selected_city"] = city
    state["selected_duration"] = duration
    state["selected_identity"] = identity
    state["selected_interests"] = list(interests)
    state["output_style"] = output_style
    state["content_format"] = content_format


def select_scene(state: MutableMapping[str, Any], scene: str) -> None:
    state["selected_scene"] = scene


def _apply_example_callback(preset: ExamplePreset) -> None:
    apply_example(
        st.session_state,
        preset.scene,
        preset.text,
        preset.city,
        preset.duration,
        preset.identity,
        preset.interests,
        preset.output_style,
        preset.content_format,
    )


def _select_scene_callback(scene: str) -> None:
    select_scene(st.session_state, scene)


def _render_scene_selector() -> str:
    render_section_heading(
        "CHAPTER 01 / DISCOVER",
        "选择一种，打开岭南的方式",
        "从漫游、研学到内容创作，选择你此刻最想开启的体验。",
    )
    selected = str(st.session_state.selected_scene)
    columns = st.columns(len(SCENES), gap="small")
    for index, (column, (scene, (_, description))) in enumerate(
        zip(columns, SCENES.items(), strict=True), start=1
    ):
        with column:
            public_name = SCENE_PUBLIC_NAMES.get(scene, scene)
            st.html(f'<div class="scene-card-index">{index:02d} / EXPLORE</div>')
            st.button(
                public_name,
                key=f"scene_{scene}",
                type="primary" if scene == selected else "secondary",
                use_container_width=True,
                disabled=bool(st.session_state.pending_job),
                on_click=_select_scene_callback,
                args=(scene,),
                help=SCENE_DESCRIPTIONS.get(scene, description),
            )
            st.html(f'<div class="scene-card-caption">{html.escape(description)}</div>')
    return selected

def _render_examples() -> None:
    st.html('<div class="prompt-hint">没有想好怎么写？试试以下灵感：</div>')
    columns = st.columns(len(EXAMPLES), gap="small")
    for column, (label, preset) in zip(columns, EXAMPLES.items(), strict=True):
        with column:
            st.button(
                label,
                key=f"example_{label}",
                use_container_width=True,
                disabled=bool(st.session_state.pending_job),
                on_click=_apply_example_callback,
                args=(preset,),
            )

def _model_status_text() -> str:
    source = active_model_source(st.session_state)
    if source == "user" and user_api_configured(st.session_state):
        return "当前使用你的个人 API"
    if source == "platform" and platform_service_ready():
        return "当前使用平台 API"
    if user_api_configured(st.session_state):
        return "平台 API 不可用，可切换到我的 API"
    return "平台 API 不可用，可在侧边栏配置个人 API"


def _workspace_aside_markup(
    scene: str,
    city: str,
    duration: str,
    identity: str,
    content_format: str,
    api_text: str,
) -> str:
    public_name = SCENE_PUBLIC_NAMES.get(scene, scene)
    description = SCENE_DESCRIPTIONS.get(scene, "生成广东非遗文化方案。")
    pills = [
        f'<span class="condition-pill">📍 {html.escape(city)}</span>',
        f'<span class="condition-pill">⏱ {html.escape(duration)}</span>',
        f'<span class="condition-pill">👤 {html.escape(identity)}</span>',
    ]
    if scene == "内容创作":
        pills.append(f'<span class="condition-pill">🎬 {html.escape(content_format)}</span>')

    return "".join(
        [
            f'<div class="workspace-aside" data-ui-build="{WORKSPACE_UI_BUILD_ID}">',
            f'<div class="workspace-aside-title">你的专属文化提案 · {html.escape(public_name)}</div>',
            f'<div class="workspace-aside-copy">{html.escape(description)}</div>',
            '<div class="condition-strip">',
            *pills,
            "</div>",
            '<div class="aside-list">',
            '<div class="aside-item"><div class="aside-icon">01</div><div class="aside-text"><strong>理解你的兴趣</strong><span>结合出行偏好与所选文化主题</span></div></div>',
            '<div class="aside-item"><div class="aside-icon">02</div><div class="aside-text"><strong>检索非遗知识</strong><span>参考广东文化项目知识资料</span></div></div>',
            '<div class="aside-item"><div class="aside-icon">03</div><div class="aside-text"><strong>生成可用提案</strong><span>按场景呈现，并可下载与修改</span></div></div>',
            "</div>",
            f'<div class="aside-model-status"><span>AI SERVICE STATUS</span><strong>{html.escape(api_text)}</strong></div>',
            '<div class="editorial-aside-bottom">粤 · 见</div>',
            "</div>",
        ]
    )

def _render_workspace_aside(
    scene: str,
    city: str,
    duration: str,
    identity: str,
    content_format: str,
) -> None:
    st.html(
        _workspace_aside_markup(
            scene,
            city,
            duration,
            identity,
            content_format,
            _model_status_text(),
        )
    )


def render_workspace() -> TaskRequest | None:
    scene = _render_scene_selector()
    render_scene_note(scene)
    pending = bool(st.session_state.pending_job)

    left, right = st.columns([2.55, 0.95], gap="large")
    with left:
        with st.container(border=True):
            render_section_heading(
                "CHAPTER 02 / CUSTOMIZE",
                "说说你的岭南故事",
                "告诉我们同行的人、出行时间与心中的兴趣，余下交给智能策展。",
            )
            st.html('<div class="editorial-input-label"><strong>体验灵感</strong><span>YOUR IDEA / 自由描述</span></div>')

            user_input = st.text_area(
                "一句话需求",
                key="user_input",
                height=132,
                max_chars=MAX_RAW_REQUEST_CHARS,
                placeholder="例如：周末带孩子去佛山，想体验醒狮和陶塑，路线轻松一点……",
                disabled=pending,
                label_visibility="collapsed",
            )
            _render_examples()

            content_format = str(st.session_state.get("content_format", "图文"))
            if scene == "内容创作":
                content_format = st.radio(
                    "🎬 内容形式",
                    ["图文", "短视频"],
                    key="content_format",
                    horizontal=True,
                    disabled=pending,
                    help="图文会生成可发布正文；短视频会生成 60 秒分镜、旁白和拍摄建议。",
                )

            st.html('<div class="editorial-subheading"><strong>定制你的体验</strong><small>DETAILS / 可按需调整</small></div>')
            c1, c2, c3 = st.columns(3)
            with c1:
                city = st.selectbox(
                    "📍 城市",
                    CITIES,
                    key="selected_city",
                    disabled=pending,
                )
            with c2:
                duration = st.selectbox(
                    "⏱ 时间",
                    DURATIONS,
                    key="selected_duration",
                    disabled=pending,
                )
            with c3:
                identity = st.selectbox(
                    "👤 身份",
                    IDENTITIES,
                    key="selected_identity",
                    disabled=pending,
                )

            with st.expander("添加兴趣偏好，让方案更懂你", expanded=False):
                interests = st.multiselect(
                    "特别想包含",
                    INTERESTS,
                    key="selected_interests",
                    disabled=pending,
                    placeholder="可多选，例如：粤剧、醒狮、拍照",
                )

            st.html(
                "".join(
                    [
                        '<div class="condition-strip">',
                        f'<span class="condition-pill">{html.escape(SCENE_PUBLIC_NAMES.get(scene, scene))}</span>',
                        f'<span class="condition-pill">{html.escape(city)}</span>',
                        f'<span class="condition-pill">{html.escape(duration)}</span>',
                        f'<span class="condition-pill">{html.escape(st.session_state.output_style)}</span>',
                        "</div>",
                    ]
                )
            )

            if not pending and st.button(
                "生成专属文化提案  ↗",
                type="primary",
                use_container_width=True,
            ):
                try:
                    task_type = None
                    if scene == "内容创作":
                        task_type = (
                            TaskType.VIDEO if content_format == "短视频" else TaskType.SOCIAL
                        )
                    return TaskRequest(
                        scene=scene,
                        raw_request=user_input,
                        city=city,
                        duration=duration,
                        identity=identity,
                        interests=tuple(interests),
                        output_style=st.session_state.output_style,
                        task_type=task_type,
                    )
                except ValueError as exc:
                    st.warning(str(exc))

    with right:
        _render_workspace_aside(scene, city, duration, identity, content_format)

    return None