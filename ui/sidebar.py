from __future__ import annotations

import html

import streamlit as st

from core.config import (
    PROVIDER_PRESETS,
    build_user_model_config,
    platform_service_ready,
    user_api_configured,
)
from core.state import clear_user_api_config, load_recent_plan, set_toast, start_new_plan
from services.llm import ModelGatewayError, test_connection

MODE_LABELS = {
    "自动": "auto",
    "平台 API": "platform",
    "我的 API": "user",
}
MODE_VALUES = {value: label for label, value in MODE_LABELS.items()}


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="brand-card">
                <div class="brand-title">🦁 粤见非遗</div>
                <div class="brand-sub">把广东非遗知识转化为可出发、可学习、可发布的真实方案。</div>
                <div class="brand-badge">LINGNAN CULTURE AGENT</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("＋ 新建方案", type="primary", use_container_width=True):
            start_new_plan(st.session_state)
            set_toast(st.session_state, "已打开一张新的非遗灵感纸", "🪭")
            st.rerun()

        _render_model_status()
        _render_model_settings()
        _render_recent_plans()
        _render_preferences()

        with st.expander("使用帮助", expanded=False):
            st.markdown(
                "写清楚 **去哪里、多久、和谁、想体验什么**，结果会更准确。\n\n"
                "默认优先使用平台 API；你也可以在“AI 模型服务”中选择“我的 API”。\n\n"
                "个人 API Key 仅保存在当前 Streamlit 会话中，不会写入最近方案或导出文件。\n\n"
                "开放时间、票务、预约和演出安排等实时信息，请以官方平台最新公告为准。"
            )


def _render_model_status() -> None:
    mode = str(st.session_state.get("model_mode", "auto"))
    platform_ready = platform_service_ready()
    user_ready = user_api_configured(st.session_state)

    if mode == "user":
        ready = user_ready
        state_text = "个人 API 已就绪" if ready else "个人 API 待配置"
        state_value = "当前使用：我的 API" if ready else "请补全 Key、地址和模型"
        badge = "🔑 会话级"
    elif mode == "platform":
        ready = platform_ready
        state_text = "平台 API 已就绪" if ready else "平台 API 暂不可用"
        state_value = "当前使用：平台 API" if ready else "可切换到我的 API"
        badge = "🔒 服务端托管"
    else:
        ready = platform_ready
        state_text = "AI 服务已就绪" if ready else "平台 API 暂不可用"
        state_value = "自动使用平台 API" if ready else "可配置并切换到我的 API"
        badge = "⚡ 自动模式"

    state_class = "ready" if ready else "waiting"
    st.markdown(
        f"""
        <div class="model-status-card">
            <div class="status-row">
                <div>
                    <div class="status-title"><span class="status-dot {state_class}"></span>{html.escape(state_text)}</div>
                    <div class="status-value">{html.escape(state_value)}</div>
                </div>
                <div class="status-value">{html.escape(badge)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _sync_model_mode_from_choice() -> None:
    label = str(st.session_state.get("model_mode_choice", "自动"))
    st.session_state["model_mode"] = MODE_LABELS.get(label, "auto")


def _apply_provider_preset() -> None:
    provider = str(st.session_state.get("user_provider", "阿里云百炼"))
    preset = PROVIDER_PRESETS.get(provider, {})
    st.session_state["user_base_url"] = preset.get("base_url", "")
    st.session_state["user_model_name"] = preset.get("model_name", "")
    st.session_state["user_api_test_status"] = ""
    st.session_state["user_api_test_message"] = ""


def _use_personal_api() -> None:
    st.session_state["model_mode"] = "user"
    st.session_state["model_mode_choice"] = "我的 API"
    set_toast(st.session_state, "已切换到你的个人 API", "🔑")


def _clear_personal_api() -> None:
    clear_user_api_config(st.session_state)
    st.session_state["model_mode_choice"] = "自动"
    set_toast(st.session_state, "已清除本次会话中的个人 API Key", "🧹")


def _render_model_settings() -> None:
    with st.expander("AI 模型服务", expanded=False):
        current_mode = str(st.session_state.get("model_mode", "auto"))
        if "model_mode_choice" not in st.session_state:
            st.session_state["model_mode_choice"] = MODE_VALUES.get(current_mode, "自动")

        st.radio(
            "使用方式",
            list(MODE_LABELS),
            key="model_mode_choice",
            horizontal=True,
            on_change=_sync_model_mode_from_choice,
            help="自动模式只会使用平台 API；平台不可用时不会未经确认消耗你的个人额度。",
        )
        _sync_model_mode_from_choice()

        platform_ready = platform_service_ready()
        if platform_ready:
            st.caption("🟢 平台 API 可用。自动模式会优先使用平台额度。")
        else:
            st.caption("🟠 平台 API 当前未提供。你仍可配置自己的 OpenAI-compatible API。")

        if st.session_state.get("model_mode") != "user" and not user_api_configured(
            st.session_state
        ):
            st.caption("需要自备 API 时，再展开下面的个人配置即可。")

        st.markdown("**我的 API（BYOK）**")
        st.selectbox(
            "服务商",
            list(PROVIDER_PRESETS),
            key="user_provider",
            on_change=_apply_provider_preset,
            disabled=bool(st.session_state.pending_job),
        )
        st.text_input(
            "API Key",
            key="user_api_key",
            type="password",
            placeholder="仅保存在当前会话",
            disabled=bool(st.session_state.pending_job),
        )
        st.text_input(
            "Base URL",
            key="user_base_url",
            placeholder="https://.../v1",
            disabled=bool(st.session_state.pending_job),
        )
        st.text_input(
            "模型名称",
            key="user_model_name",
            placeholder="例如 qwen-plus",
            disabled=bool(st.session_state.pending_job),
        )

        left, right = st.columns(2)
        with left:
            if st.button(
                "测试连接",
                key="test_user_api",
                use_container_width=True,
                disabled=bool(st.session_state.pending_job),
            ):
                try:
                    answer = test_connection(build_user_model_config(st.session_state))
                    st.session_state["user_api_test_status"] = "ok"
                    st.session_state["user_api_test_message"] = (
                        "连接成功" if answer.strip() else "接口已连接"
                    )
                except (ValueError, ModelGatewayError) as exc:
                    st.session_state["user_api_test_status"] = "error"
                    st.session_state["user_api_test_message"] = str(exc)
        with right:
            st.button(
                "使用此 API",
                key="use_user_api",
                use_container_width=True,
                disabled=(
                    bool(st.session_state.pending_job)
                    or not user_api_configured(st.session_state)
                ),
                on_click=_use_personal_api,
            )

        status = str(st.session_state.get("user_api_test_status", ""))
        message = str(st.session_state.get("user_api_test_message", ""))
        if status == "ok" and message:
            st.success(message)
        elif status == "error" and message:
            st.error(message)

        st.caption(
            "隐私说明：个人 API Key 只保存在当前 Streamlit 会话内；不写入数据库、最近方案、URL 或导出文件。"
        )
        st.button(
            "清除我的 API Key",
            key="clear_user_api",
            use_container_width=True,
            disabled=not bool(str(st.session_state.get("user_api_key", "")).strip()),
            on_click=_clear_personal_api,
        )


def _render_recent_plans() -> None:
    st.markdown("### 最近方案")
    recent = st.session_state.get("recent_plans", [])
    if not recent:
        st.caption("生成后的方案会保留在当前会话中。")
        return

    for index, item in enumerate(recent):
        title = item.get("title", "未命名方案")
        created_at = item.get("time", "")
        st.markdown(
            f"""
            <div class="recent-card">
                <div class="recent-title">{html.escape(title)}</div>
                <div class="recent-meta">{html.escape(created_at)} · 点击下方重新打开</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("打开方案", key=f"load_recent_{index}", use_container_width=True):
            load_recent_plan(st.session_state, item)
            set_toast(st.session_state, f"已载入：{title}", "📌")
            st.rerun()


def _render_preferences() -> None:
    with st.expander("偏好设置", expanded=False):
        st.selectbox(
            "输出风格",
            ["清晰实用", "游客友好", "研学报告", "小红书风格", "专业讲解"],
            key="output_style",
        )
        st.slider(
            "表达灵活度",
            min_value=0.1,
            max_value=1.0,
            step=0.05,
            key="temperature",
            help="越高越活泼，越低越稳妥。",
        )
