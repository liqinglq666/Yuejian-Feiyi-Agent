from __future__ import annotations

import streamlit as st

MOBILE_CSS = r"""
<style>
@media (max-width: 920px) {
    html, body, .stApp, [data-testid="stAppViewContainer"] {
        max-width: 100%;
        overflow-x: hidden;
    }

    .block-container {
        padding-top: .4rem !important;
        padding-left: .78rem !important;
        padding-right: .78rem !important;
        padding-bottom: 5rem !important;
    }

    section[data-testid="stSidebar"] {
        width: min(88vw, 320px) !important;
        max-width: min(88vw, 320px) !important;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: .72rem !important;
    }

    .topbar-left {
        min-height: 2.35rem;
    }

    .section-heading {
        margin-bottom: .58rem;
    }

    .section-title {
        font-size: 1.18rem;
        line-height: 1.26;
    }

    .section-copy {
        font-size: .81rem;
        line-height: 1.48;
    }

    .scene-note {
        padding: .62rem .7rem;
        margin: .34rem 0 .62rem;
    }

    .scene-title {
        font-size: .9rem;
    }

    .scene-desc {
        font-size: .77rem;
        line-height: 1.45;
    }

    .workspace-aside {
        margin-top: .55rem;
        padding: .82rem;
        border-radius: 16px;
    }

    .condition-strip {
        gap: .3rem;
        margin-top: .46rem;
    }

    .condition-pill {
        padding: .26rem .48rem;
        font-size: .69rem;
    }

    .request-summary {
        gap: .48rem;
        padding: .72rem .78rem;
        border-radius: 14px;
    }

    .request-main,
    .result-title,
    .answer-shell,
    .source-box {
        overflow-wrap: anywhere;
        word-break: break-word;
    }

    .stButton > button,
    .stDownloadButton > button {
        min-height: 44px !important;
        border-radius: 11px !important;
        touch-action: manipulation;
    }

    .stTextArea textarea,
    .stTextInput input {
        font-size: 16px !important;
        line-height: 1.45 !important;
    }

    div[data-baseweb="select"] > div {
        min-height: 44px !important;
        font-size: 16px !important;
    }

    div[role="radiogroup"] {
        flex-wrap: wrap !important;
        row-gap: .3rem !important;
    }

    [data-testid="stExpander"] summary {
        min-height: 44px;
        align-items: center;
    }

    div[data-baseweb="tab-list"] {
        overflow-x: auto;
        overflow-y: hidden;
        scrollbar-width: none;
        -webkit-overflow-scrolling: touch;
    }

    div[data-baseweb="tab-list"]::-webkit-scrollbar {
        display: none;
    }

    button[data-baseweb="tab"] {
        flex: 0 0 auto;
        white-space: nowrap;
        min-height: 44px;
    }

    div[data-testid="stMarkdownContainer"] {
        max-width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }

    div[data-testid="stMarkdownContainer"] table {
        min-width: 620px;
    }

    .fact-grid {
        grid-template-columns: 1fr !important;
    }
}

@media (max-width: 560px) {
    .block-container {
        padding-left: .62rem !important;
        padding-right: .62rem !important;
    }

    .brand-card {
        padding: .78rem;
        border-radius: 16px;
    }

    .brand-title {
        font-size: 1.05rem;
    }

    .brand-sub {
        font-size: .78rem;
    }

    .model-status-card,
    .recent-card {
        border-radius: 12px;
    }

    .status-row {
        align-items: flex-start;
        flex-wrap: wrap;
        gap: .35rem .6rem;
    }

    .section-eyebrow {
        font-size: .66rem;
    }

    .section-title {
        font-size: 1.12rem;
    }

    .section-copy {
        font-size: .78rem;
    }

    .prompt-hint {
        margin-top: -.08rem;
        font-size: .75rem;
    }

    .empty-state {
        padding: 1rem .8rem;
        border-radius: 16px;
    }

    .empty-icon {
        font-size: 1.7rem;
    }

    .answer-shell {
        padding: .8rem;
        border-radius: 15px;
    }

    .source-box {
        padding: .68rem .72rem;
    }

    .workspace-aside-title {
        font-size: .9rem;
    }

    .workspace-aside-copy {
        font-size: .75rem;
    }

    .aside-item {
        padding: .54rem .04rem;
    }

    .aside-text strong {
        font-size: .75rem;
    }

    .aside-text span {
        font-size: .68rem;
    }
}

@media (max-width: 380px) {
    .block-container {
        padding-left: .5rem !important;
        padding-right: .5rem !important;
    }

    .condition-pill {
        font-size: .67rem;
        padding: .24rem .42rem;
    }

    .stButton > button,
    .stDownloadButton > button {
        font-size: .88rem !important;
    }
}

@media (hover: none) and (pointer: coarse) {
    .stButton > button:hover,
    .stDownloadButton > button:hover {
        transform: none !important;
        box-shadow: none !important;
    }
}
</style>
"""


def apply_mobile_styles() -> None:
    st.markdown(MOBILE_CSS, unsafe_allow_html=True)
