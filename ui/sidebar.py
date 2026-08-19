from __future__ import annotations

import html

import streamlit as st

from core.config import model_service_ready
from core.state import load_recent_plan, set_toast, start_new_plan


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

        with st.expander("使用帮助", expanded=False):
            st.markdown(
                "写清楚 **去哪里、多久、和谁、想体验什么**，结果会更准确。\n\n"
                "AI 服务由平台统一提供，无需填写 API Key 或模型地址。\n\n"
                "开放时间、票务、预约和演出安排等实时信息，请以官方平台最新公告为准。"
            )


def _render_model_status() -> None:
    ready = model_service_ready()
    state_class = "ready" if ready else "waiting"
    state_text = "AI 服务已就绪" if ready else "AI 服务暂不可用"
    state_value = "平台统一提供" if ready else "等待管理员配置"
    st.markdown(
        f"""
        <div class="model-status-card">
            <div class="status-row">
                <div>
                    <div class="status-title"><span class="status-dot {state_class}"></span>{html.escape(state_text)}</div>
                    <div class="status-value">{html.escape(state_value)}</div>
                </div>
                <div class="status-value">🔒 服务端托管</div>
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
