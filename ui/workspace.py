from __future__ import annotations

import html
from collections.abc import MutableMapping
from dataclasses import dataclass
from typing import Any

import streamlit as st

from core.models import TaskRequest
from ui.components import (
    SCENE_DESCRIPTIONS,
    SCENE_PUBLIC_NAMES,
    render_scene_note,
    render_section_heading,
)

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
    ),
}

CITIES = ["自动判断", "广州", "佛山", "潮州", "汕头", "深圳", "梅州", "江门", "珠海", "东莞"]
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
) -> None:
    state["selected_scene"] = scene
    state["last_scene"] = scene
    state["user_input"] = text
    state["selected_city"] = city
    state["selected_duration"] = duration
    state["selected_identity"] = identity
    state["selected_interests"] = list(interests)
    state["output_style"] = output_style


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
    )


def _select_scene_callback(scene: str) -> None:
    select_scene(st.session_state, scene)


def _render_scene_selector() -> str:
    render_section_heading(
        "STEP 01",
        "选择你想做什么",
        "不同场景会使用不同的输出结构，生成结果不再只是同一种长文。",
    )
    selected = str(st.session_state.selected_scene)
    columns = st.columns(len(SCENES), gap="small")
    for column, (scene, (icon, description)) in zip(columns, SCENES.items(), strict=True):
        with column:
            public_name = SCENE_PUBLIC_NAMES.get(scene, scene)
            st.button(
                f"{icon} {public_name}",
                key=f"scene_{scene}",
                type="primary" if scene == selected else "secondary",
                use_container_width=True,
                disabled=bool(st.session_state.pending_job),
                on_click=_select_scene_callback,
                args=(scene,),
                help=SCENE_DESCRIPTIONS.get(scene, description),
            )
            st.caption(description)
    return selected


def _render_examples() -> None:
    st.markdown('<div class="prompt-hint">没有灵感？从这些常用需求开始：</div>', unsafe_allow_html=True)
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


def _render_workspace_aside(scene: str, city: str, duration: str, identity: str) -> None:
    public_name = SCENE_PUBLIC_NAMES.get(scene, scene)
    description = SCENE_DESCRIPTIONS.get(scene, "生成广东非遗文化方案。")
    api_ready = bool(str(st.session_state.get("user_api_key", "")).strip())
    api_text = "模型已连接，可以生成" if api_ready else "还需在侧边栏填写 API Key"
    st.markdown(
        f"""
        <div class="workspace-aside">
            <div class="workspace-aside-title">本次将生成 · {html.escape(public_name)}</div>
            <div class="workspace-aside-copy">{html.escape(description)}</div>
            <div class="condition-strip">
                <span class="condition-pill">📍 {html.escape(city)}</span>
                <span class="condition-pill">⏱ {html.escape(duration)}</span>
                <span class="condition-pill">👤 {html.escape(identity)}</span>
            </div>
            <div class="aside-list">
                <div class="aside-item">
                    <div class="aside-icon">🧠</div>
                    <div class="aside-text"><strong>按场景组织结果</strong><span>路线、研学、创作与问答使用不同模板</span></div>
                </div>
                <div class="aside-item">
                    <div class="aside-icon">📚</div>
                    <div class="aside-text"><strong>检索广东非遗知识</strong><span>重要事实会附带来源编号</span></div>
                </div>
                <div class="aside-item">
                    <div class="aside-icon">✨</div>
                    <div class="aside-text"><strong>生成后继续调整</strong><span>可转亲子版、研学表或短视频脚本</span></div>
                </div>
                <div class="aside-item">
                    <div class="aside-icon">🔌</div>
                    <div class="aside-text"><strong>模型状态</strong><span>{html.escape(api_text)}</span></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workspace() -> TaskRequest | None:
    scene = _render_scene_selector()
    render_scene_note(scene)

    left, right = st.columns([2.35, 0.9], gap="large")
    with left:
        with st.container(border=True):
            render_section_heading(
                "STEP 02",
                "告诉我你想怎样体验岭南",
                "需求写得越具体，路线、任务和成品就越贴近你的真实场景。",
            )

            user_input = st.text_area(
                "一句话需求",
                key="user_input",
                height=155,
                placeholder="例如：周末带孩子去佛山，想体验醒狮和陶塑，路线轻松一点……",
                disabled=bool(st.session_state.pending_job),
                label_visibility="collapsed",
            )
            _render_examples()

            st.markdown("#### 补充条件")
            c1, c2, c3 = st.columns(3)
            with c1:
                city = st.selectbox(
                    "📍 城市",
                    CITIES,
                    key="selected_city",
                    disabled=bool(st.session_state.pending_job),
                )
            with c2:
                duration = st.selectbox(
                    "⏱ 时间",
                    DURATIONS,
                    key="selected_duration",
                    disabled=bool(st.session_state.pending_job),
                )
            with c3:
                identity = st.selectbox(
                    "👤 身份",
                    IDENTITIES,
                    key="selected_identity",
                    disabled=bool(st.session_state.pending_job),
                )

            with st.expander("添加兴趣偏好，让方案更懂你", expanded=False):
                interests = st.multiselect(
                    "特别想包含",
                    INTERESTS,
                    key="selected_interests",
                    disabled=bool(st.session_state.pending_job),
                    placeholder="可多选，例如：粤剧、醒狮、拍照",
                )

            st.markdown(
                f"""
                <div class="condition-strip">
                    <span class="condition-pill">{html.escape(SCENE_PUBLIC_NAMES.get(scene, scene))}</span>
                    <span class="condition-pill">{html.escape(city)}</span>
                    <span class="condition-pill">{html.escape(duration)}</span>
                    <span class="condition-pill">{html.escape(st.session_state.output_style)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "生成我的非遗方案 →" if not st.session_state.pending_job else "正在生成中…",
                type="primary",
                use_container_width=True,
                disabled=bool(st.session_state.pending_job),
            ):
                try:
                    return TaskRequest(
                        scene=scene,
                        raw_request=user_input,
                        city=city,
                        duration=duration,
                        identity=identity,
                        interests=tuple(interests),
                        output_style=st.session_state.output_style,
                    )
                except ValueError as exc:
                    st.warning(str(exc))

    with right:
        _render_workspace_aside(scene, city, duration, identity)

    return None
