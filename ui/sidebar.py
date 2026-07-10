from __future__ import annotations

import html

import streamlit as st

from core.config import PROVIDER_PRESETS, build_model_config
from core.models import TaskRequest
from core.state import clear_current_plan, set_toast
from services.llm import ModelGatewayError, test_connection


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="brand-card">
                <div class="brand-title">🦁 粤见非遗</div>
                <div class="brand-sub">寻脉岭南，智游非遗</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        _render_recent_plans()
        st.divider()
        _render_preferences()
        st.divider()
        _render_model_settings()
        st.divider()

        if st.button("重新开始", use_container_width=True):
            clear_current_plan(st.session_state)
            set_toast(st.session_state, "已清空当前方案", "🧹")
            st.rerun()

        with st.expander("如何写得更准？", expanded=False):
            st.markdown("写清楚去哪里、多久、和谁、想体验什么。实时开放与票务信息仍需以官方平台为准。")


def _render_recent_plans() -> None:
    st.markdown("### 最近生成")
    recent = st.session_state.get("recent_plans", [])
    if not recent:
        st.caption("你生成过的方案会显示在这里。")
        return

    for index, item in enumerate(recent):
        st.markdown(
            f"""
            <div class="recent-card">
                <div class="recent-title">{html.escape(item.get('title', '未命名方案'))}</div>
                <div class="recent-meta">{html.escape(item.get('time', ''))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("查看", key=f"load_recent_{index}", use_container_width=True):
            request = TaskRequest.from_dict(item["request"])
            st.session_state.root_request = request.to_dict()
            st.session_state.current_answer = item.get("answer", "")
            st.session_state.current_sources = ""
            st.session_state.revision_history = []
            st.session_state.pending_job = None
            set_toast(st.session_state, f"已载入：{item.get('title', '方案')}", "📌")
            st.rerun()


def _render_preferences() -> None:
    with st.expander("更多偏好", expanded=False):
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
    with st.expander("模型接入", expanded=True):
        st.caption("API Key 只保存在当前 Streamlit 会话中，不写入仓库。")
        st.text_input("API Key", type="password", key="user_api_key")

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
            st.caption("常见示例：" + " / ".join(preset.model_examples))

        if st.button("测试模型连接", use_container_width=True):
            try:
                config = build_model_config(st.session_state)
                with st.spinner("正在测试模型连接…"):
                    answer = test_connection(config)
                st.success(f"连接正常，模型返回：{answer[:30]}")
            except (ValueError, ModelGatewayError) as exc:
                st.error(str(exc))
