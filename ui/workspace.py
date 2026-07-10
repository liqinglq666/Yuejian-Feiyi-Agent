from __future__ import annotations

import streamlit as st

from core.models import TaskRequest
from ui.components import SCENE_DESCRIPTIONS, render_scene_note

SCENES = ["游客路线", "学生研学", "亲子体验", "内容创作", "非遗问答"]

EXAMPLES = {
    "广州一日路线": ("游客路线", "我第一次来广州，有一天时间，想体验岭南非遗文化，最好适合拍照和写研学记录。"),
    "高中研学任务": ("学生研学", "我是高中生，要做一份广东非遗研学报告，请设计围绕粤剧、醒狮和广绣的任务卡。"),
    "佛山亲子体验": ("亲子体验", "我周末带孩子去佛山，想体验醒狮和石湾陶塑，节奏轻松一点。"),
    "英歌舞图文": ("内容创作", "帮我写一篇介绍潮汕英歌舞的图文内容，适合小红书发布。"),
}


def render_workspace() -> TaskRequest | None:
    left, right = st.columns([2.15, 1], gap="large")

    with left:
        with st.container(border=True):
            st.markdown("### 创建方案")
            st.caption("选择用途，补充城市和时间，再用一句话描述需求。")

            scene = st.radio(
                "用途",
                SCENES,
                horizontal=True,
                key="selected_scene",
                disabled=bool(st.session_state.pending_job),
            )
            render_scene_note(scene)

            c1, c2 = st.columns(2)
            with c1:
                city = st.selectbox(
                    "城市",
                    [
                        "自动判断",
                        "广州",
                        "佛山",
                        "潮州",
                        "汕头",
                        "深圳",
                        "梅州",
                        "江门",
                        "珠海",
                        "东莞",
                    ],
                    disabled=bool(st.session_state.pending_job),
                )
            with c2:
                duration = st.selectbox(
                    "时间",
                    ["自动判断", "半天", "一天", "两天", "周末", "不限"],
                    disabled=bool(st.session_state.pending_job),
                )

            st.caption("试试这些：")
            columns = st.columns(4)
            for column, (label, (example_scene, text)) in zip(
                columns, EXAMPLES.items(), strict=True
            ):
                with column:
                    if st.button(
                        label,
                        key=f"example_{label}",
                        use_container_width=True,
                        disabled=bool(st.session_state.pending_job),
                    ):
                        st.session_state.selected_scene = example_scene
                        st.session_state.user_input = text
                        st.rerun()

            user_input = st.text_area(
                "一句话需求",
                key="user_input",
                height=145,
                disabled=bool(st.session_state.pending_job),
            )

            with st.expander("补充设置，可不填"):
                identity = st.selectbox(
                    "身份",
                    ["自动匹配", "外地游客", "学生研学", "亲子家庭", "本地居民", "内容创作者"],
                    disabled=bool(st.session_state.pending_job),
                )
                interests = st.multiselect(
                    "特别想包含",
                    [
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
                    ],
                    disabled=bool(st.session_state.pending_job),
                )

            if st.button(
                "✨ 生成方案" if not st.session_state.pending_job else "正在生成中…",
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
        with st.container(border=True):
            st.markdown("### 本次将生成")
            st.markdown(f"**{scene}**")
            st.caption(SCENE_DESCRIPTIONS.get(scene, "广东非遗文化方案。"))
            st.markdown(
                f"- 城市：{city}\n- 时间：{duration}\n- 输出风格：{st.session_state.output_style}"
            )
            st.divider()
            st.markdown("**生成后可继续：**")
            st.markdown("- 压缩成半天\n- 改成亲子版\n- 生成小红书文案\n- 生成短视频脚本\n- 加研学记录表")

    return None
