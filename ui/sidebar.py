from __future__ import annotations

import html

import streamlit as st

from core.config import PROVIDER_PRESETS, build_model_config
from core.models import TaskRequest
from core.state import set_toast, start_new_plan
from services.llm import ModelGatewayError, test_connection


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
        _render_recent_plans()
        _render_preferences()
        _render_model_settings()

        with st.expander("使用帮助", expanded=False):
            st.markdown(
                "写清楚 **去哪里、多久、和谁、想体验什么**，结果会更准确。\n\n"
                "开放时间、票务、预约和演出安排等实时信息，请以官方平台最新公告为准。"
            )


def _render_model_status() -> None:
    api_ready = bool(str(st.session_state.get("user_api_key", "")).strip())
    provider = str(st.session_state.get("provider", "未选择服务"))
    state_class = "ready" if api_ready else "waiting"
    state_text = "已填写 API Key" if api_ready else "等待连接"
    st.markdown(
        f"""
        <div class="model-status-card">
            <div class="status-row">
                <div>
                    <div class="status-title"><span class="status-dot {state_class}"></span>{html.escape(state_text)}</div>
                    <div class="status-value">{html.escape(provider)}</div>
                </div>
                <div class="status-value">🔒 仅当前会话</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
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
            request = TaskRequest.from_dict(item["request"])
            st.session_state.root_request = request.to_dict()
            st.session_state.current_answer = item.get("answer", "")
            st.session_state.current_sources = ""
            st.session_state.revision_history = []
            st.session_state.pending_job = None
            st.session_state.selected_scene = request.scene
            st.session_state.user_input = request.raw_request
            st.session_state.selected_city = request.city
            st.session_state.selected_duration = request.duration
            st.session_state.selected_identity = request.identity
            st.session_state.selected_interests = list(request.interests)
            st.session_state.output_style = request.output_style
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


def _render_model_settings() -> None:
    with st.expander("模型与隐私", expanded=False):
        st.caption("连接一个 OpenAI Compatible 模型后即可生成。API Key 只保存在当前会话中。")
        st.text_input("API Key", type="password", key="user_api_key", placeholder="粘贴你的 API Key")

        provider_names = list(PROVIDER_PRESETS)
        provider = st.selectbox("接口服务", provider_names, key="provider")
        preset = PROVIDER_PRESETS[provider]

        if st.session_state.get("last_provider") != provider:
            st.session_state.last_provider = provider
            st.session_state.user_base_url = preset.base_url
            st.session_state.user_model_name = preset.default_model
            st.rerun()

        custom = provider == "自定义 OpenAI 兼容接口"
        st.text_input(
            "Base URL",
            key="user_base_url",
            disabled=not custom,
            placeholder="https://example.com/v1",
        )
        st.text_input(
            "模型名称",
            key="user_model_name",
            placeholder="例如：qwen-plus / deepseek-chat",
            help="服务商更新模型名称后，可直接填写其当前支持的模型 ID。",
        )

        if preset.model_examples:
            st.caption("常见模型：" + " / ".join(preset.model_examples))

        if st.button("测试模型连接", use_container_width=True):
            try:
                config = build_model_config(st.session_state)
                with st.spinner("正在测试模型连接…"):
                    answer = test_connection(config)
                st.success(f"连接正常：{answer[:30]}")
            except (ValueError, ModelGatewayError) as exc:
                st.error(str(exc))
