from __future__ import annotations

import streamlit as st

CSS = r"""
<style>
:root {
    --lingnan-teal: #159a9c;
    --lingnan-teal-dark: #0f6f72;
    --lion-orange: #f2763b;
    --canton-red: #c93c37;
    --paper: #faf7f0;
    --ink: #16324f;
    --muted: #64748b;
    --line: rgba(22, 50, 79, .10);
    --card: rgba(255, 255, 255, .90);
}

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
}

.stApp {
    color: var(--ink);
    background:
        radial-gradient(circle at 88% 2%, rgba(21, 154, 156, .11), transparent 24%),
        radial-gradient(circle at 5% 8%, rgba(242, 118, 59, .09), transparent 23%),
        linear-gradient(180deg, #fffdf8 0%, #f6fbfa 48%, #fffdf9 100%);
}

.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    opacity: .12;
    background-image:
        linear-gradient(45deg, transparent 46%, rgba(21, 154, 156, .10) 47%, rgba(21, 154, 156, .10) 53%, transparent 54%),
        linear-gradient(-45deg, transparent 46%, rgba(242, 118, 59, .08) 47%, rgba(242, 118, 59, .08) 53%, transparent 54%);
    background-size: 38px 38px;
    mask-image: linear-gradient(180deg, #000 0%, transparent 34%);
}

header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 1280px; padding-top: .65rem; padding-bottom: 4rem; }

section[data-testid="stSidebar"] {
    background:
        radial-gradient(circle at 15% 4%, rgba(242, 118, 59, .08), transparent 23%),
        linear-gradient(180deg, #f8fbf8 0%, #edf7f4 100%);
    border-right: 1px solid rgba(22, 50, 79, .08);
}
section[data-testid="stSidebar"] > div { padding-top: 1rem; }

.brand-card,
.recent-card,
.model-status-card,
.workspace-aside,
.empty-state,
.result-hero,
.fact-card {
    background: var(--card);
    border: 1px solid var(--line);
    box-shadow: 0 8px 24px rgba(22, 50, 79, .045);
}

.brand-card {
    position: relative;
    overflow: hidden;
    padding: .95rem;
    border-radius: 20px;
    margin-bottom: .75rem;
}
.brand-card::after {
    content: "粤";
    position: absolute;
    right: -.2rem;
    bottom: -1.3rem;
    color: rgba(21, 154, 156, .065);
    font-size: 5.4rem;
    font-weight: 950;
    transform: rotate(-9deg);
}
.brand-title { color: var(--ink); font-size: 1.18rem; font-weight: 950; }
.brand-sub { color: var(--muted); font-size: .82rem; line-height: 1.58; margin-top: .15rem; }
.brand-badge {
    display: inline-flex;
    margin-top: .58rem;
    padding: .25rem .54rem;
    color: var(--lingnan-teal-dark);
    background: rgba(21, 154, 156, .075);
    border: 1px solid rgba(21, 154, 156, .13);
    border-radius: 999px;
    font-size: .69rem;
    font-weight: 800;
}

.model-status-card {
    border-radius: 14px;
    padding: .68rem .76rem;
    margin: .28rem 0 .68rem;
}
.status-row { display: flex; align-items: center; justify-content: space-between; gap: .7rem; }
.status-title { color: var(--ink); font-size: .82rem; font-weight: 850; }
.status-value { color: var(--muted); font-size: .72rem; }
.status-dot { width: .48rem; height: .48rem; border-radius: 50%; display: inline-block; margin-right: .32rem; }
.status-dot.ready { background: #22a06b; box-shadow: 0 0 0 3px rgba(34,160,107,.09); }
.status-dot.waiting { background: #d97706; box-shadow: 0 0 0 3px rgba(217,119,6,.09); }

.recent-card { border-radius: 14px; padding: .68rem .76rem; margin-bottom: .34rem; }
.recent-title { color: var(--ink); font-size: .86rem; font-weight: 850; }
.recent-meta { color: var(--muted); font-size: .71rem; margin-top: .14rem; }

.topbar-left {
    display: flex;
    align-items: center;
    gap: .58rem;
    color: var(--ink);
    font-weight: 950;
    font-size: 1rem;
    min-height: 2.65rem;
}
.topbar-logo {
    width: 2rem;
    height: 2rem;
    border-radius: 11px 11px 11px 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    background: linear-gradient(135deg, var(--lingnan-teal), var(--lion-orange));
    box-shadow: 0 7px 18px rgba(21,154,156,.16);
}

.section-heading { margin: .12rem 0 .72rem; }
.section-eyebrow { color: var(--canton-red); font-size: .7rem; font-weight: 900; letter-spacing: .08em; text-transform: uppercase; }
.section-title { color: var(--ink); font-size: 1.3rem; font-weight: 950; margin-top: .13rem; }
.section-copy { color: var(--muted); font-size: .85rem; margin-top: .2rem; }

.scene-note {
    border-radius: 13px;
    padding: .7rem .82rem;
    background: rgba(21,154,156,.055);
    border: 1px solid rgba(21,154,156,.11);
    margin: .4rem 0 .78rem;
}
.scene-title { font-weight: 880; color: var(--lingnan-teal-dark); }
.scene-desc { color: #587080; font-size: .81rem; margin-top: .14rem; }

.prompt-hint { color: var(--muted); font-size: .78rem; margin: -.15rem 0 .42rem; }
.condition-strip { display: flex; flex-wrap: wrap; gap: .36rem; margin: .55rem 0 .12rem; }
.condition-pill {
    padding: .28rem .54rem;
    border-radius: 999px;
    background: rgba(21,154,156,.055);
    border: 1px solid rgba(21,154,156,.105);
    color: var(--lingnan-teal-dark);
    font-size: .72rem;
    font-weight: 780;
}

.workspace-aside { border-radius: 18px; padding: .9rem; }
.workspace-aside-title { color: var(--ink); font-weight: 930; font-size: .95rem; }
.workspace-aside-copy { color: var(--muted); font-size: .78rem; line-height: 1.58; margin-top: .18rem; }
.aside-list { display: grid; gap: 0; margin-top: .72rem; border-top: 1px solid rgba(22,50,79,.07); }
.aside-item {
    display: flex;
    gap: .52rem;
    align-items: flex-start;
    padding: .62rem .08rem;
    border-bottom: 1px solid rgba(22,50,79,.06);
}
.aside-icon {
    width: 1.42rem;
    height: 1.42rem;
    flex: 0 0 1.42rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 7px;
    color: var(--lingnan-teal-dark);
    background: rgba(21,154,156,.075);
    font-size: .62rem;
    font-weight: 900;
}
.aside-text strong { display: block; color: var(--ink); font-size: .77rem; }
.aside-text span { color: var(--muted); font-size: .7rem; line-height: 1.45; }
.aside-model-status {
    display: grid;
    gap: .12rem;
    margin-top: .72rem;
    padding-top: .68rem;
    border-top: 1px solid rgba(22,50,79,.07);
}
.aside-model-status span { color: var(--muted); font-size: .68rem; }
.aside-model-status strong { color: var(--lingnan-teal-dark); font-size: .75rem; font-weight: 850; }

.request-summary {
    display: flex;
    gap: .7rem;
    align-items: flex-start;
    border-radius: 16px;
    padding: .82rem .94rem;
    margin-bottom: .72rem;
    background: rgba(255,248,241,.88);
    border: 1px solid rgba(242,118,59,.15);
}
.request-icon { font-size: 1.2rem; }
.request-label { color: #a63c17; font-size: .72rem; font-weight: 900; }
.request-main { color: var(--ink); font-weight: 760; line-height: 1.58; }
.request-meta { color: var(--muted); font-size: .75rem; margin-top: .16rem; }

.empty-state { border-radius: 20px; padding: 1.25rem; text-align: center; margin-top: .45rem; }
.empty-icon { font-size: 2.05rem; }
.empty-title { color: var(--ink); font-size: 1.03rem; font-weight: 930; margin-top: .3rem; }
.empty-copy { color: var(--muted); font-size: .81rem; margin-top: .18rem; }

.result-hero { border-radius: 18px; padding: .92rem 1rem; margin-bottom: .72rem; }
.result-label { color: var(--canton-red); font-size: .7rem; font-weight: 900; }
.result-title { color: var(--ink); font-size: 1.12rem; font-weight: 930; margin-top: .16rem; }
.result-meta { color: var(--muted); font-size: .76rem; margin-top: .22rem; }

.answer-shell {
    background: rgba(255,255,255,.94);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: .95rem 1.05rem;
    box-shadow: 0 8px 24px rgba(22,50,79,.04);
}
.answer-header { display: flex; align-items: center; gap: .5rem; color: var(--lingnan-teal-dark); font-weight: 930; padding-bottom: .65rem; border-bottom: 1px solid rgba(22,50,79,.07); margin-bottom: .75rem; }
.source-box { margin-top: .9rem; padding: .76rem .88rem; background: #f7fbfa; border: 1px solid rgba(22,50,79,.07); border-radius: 13px; }

.fact-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: .58rem; margin: .58rem 0 .88rem; }
.fact-card { border-radius: 13px; padding: .66rem .72rem; }
.fact-label { color: var(--muted); font-size: .69rem; font-weight: 780; }
.fact-value { color: var(--ink); font-size: .86rem; font-weight: 880; margin-top: .1rem; }

.stButton > button,
.stDownloadButton > button {
    border-radius: 12px;
    font-weight: 800;
    min-height: 2.45rem;
    border-color: rgba(22,50,79,.105);
    box-shadow: none;
    transition: transform .13s ease, box-shadow .13s ease, border-color .13s ease;
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 7px 18px rgba(22,50,79,.065);
    border-color: rgba(21,154,156,.24);
}
.stButton > button[kind="primary"] {
    border: 0;
    min-height: 2.7rem;
    background: linear-gradient(92deg, var(--lingnan-teal), var(--lion-orange));
    box-shadow: 0 9px 22px rgba(21,154,156,.16);
    color: #fff;
    font-weight: 900;
}
.stDownloadButton > button { background: #fff; }

.stTextArea textarea,
.stTextInput input,
div[data-baseweb="select"] > div {
    border-radius: 12px !important;
    border-color: rgba(22,50,79,.105) !important;
}
.stTextArea textarea:focus,
.stTextInput input:focus {
    border-color: rgba(21,154,156,.42) !important;
    box-shadow: 0 0 0 3px rgba(21,154,156,.07) !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 18px !important;
    border-color: rgba(22,50,79,.085) !important;
    background: rgba(255,255,255,.76);
    box-shadow: 0 8px 24px rgba(22,50,79,.035);
}

button[data-baseweb="tab"] { font-weight: 830; }
div[data-baseweb="tab-list"] { gap: .35rem; border-bottom: 1px solid rgba(22,50,79,.08); }
button[data-baseweb="tab"][aria-selected="true"] { color: var(--lingnan-teal-dark); }

[data-testid="stExpander"] {
    border-radius: 12px !important;
    border-color: rgba(22,50,79,.085) !important;
    background: rgba(255,255,255,.52);
}

div[data-testid="stMarkdownContainer"] table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    border: 1px solid rgba(22,50,79,.08);
    border-radius: 12px;
    overflow: hidden;
    font-size: .86rem;
}
div[data-testid="stMarkdownContainer"] th { background: rgba(21,154,156,.07); padding: .58rem .66rem; }
div[data-testid="stMarkdownContainer"] td { padding: .58rem .66rem; border-top: 1px solid rgba(22,50,79,.06); }

@media (max-width: 920px) {
    .block-container { padding-left: .82rem; padding-right: .82rem; }
    .topbar-left { margin-bottom: .12rem; }
    .request-summary { flex-direction: column; }
    .fact-grid { grid-template-columns: 1fr; }
    .workspace-aside { margin-top: .1rem; }
}
</style>
"""


def apply_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
