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
        radial-gradient(circle at 88% 2%, rgba(21, 154, 156, .14), transparent 24%),
        radial-gradient(circle at 5% 8%, rgba(242, 118, 59, .12), transparent 23%),
        linear-gradient(180deg, #fffdf8 0%, #f6fbfa 48%, #fffdf9 100%);
}

.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    opacity: .18;
    background-image:
        linear-gradient(45deg, transparent 46%, rgba(21, 154, 156, .10) 47%, rgba(21, 154, 156, .10) 53%, transparent 54%),
        linear-gradient(-45deg, transparent 46%, rgba(242, 118, 59, .08) 47%, rgba(242, 118, 59, .08) 53%, transparent 54%);
    background-size: 38px 38px;
    mask-image: linear-gradient(180deg, #000 0%, transparent 38%);
}

header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 1280px; padding-top: .8rem; padding-bottom: 4rem; }

section[data-testid="stSidebar"] {
    background:
        radial-gradient(circle at 15% 4%, rgba(242, 118, 59, .11), transparent 23%),
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
    box-shadow: 0 16px 42px rgba(22, 50, 79, .06);
    backdrop-filter: blur(14px);
}

.brand-card {
    position: relative;
    overflow: hidden;
    padding: 1rem;
    border-radius: 24px;
    margin-bottom: .85rem;
}
.brand-card::after {
    content: "粤";
    position: absolute;
    right: -.2rem;
    bottom: -1.3rem;
    color: rgba(21, 154, 156, .08);
    font-size: 5.8rem;
    font-weight: 950;
    transform: rotate(-9deg);
}
.brand-title { color: var(--ink); font-size: 1.25rem; font-weight: 950; }
.brand-sub { color: var(--muted); font-size: .84rem; line-height: 1.65; margin-top: .15rem; }
.brand-badge {
    display: inline-flex;
    margin-top: .65rem;
    padding: .28rem .58rem;
    color: var(--lingnan-teal-dark);
    background: rgba(21, 154, 156, .09);
    border: 1px solid rgba(21, 154, 156, .15);
    border-radius: 999px;
    font-size: .72rem;
    font-weight: 800;
}

.model-status-card {
    border-radius: 16px;
    padding: .72rem .8rem;
    margin: .3rem 0 .75rem;
}
.status-row { display: flex; align-items: center; justify-content: space-between; gap: .7rem; }
.status-title { color: var(--ink); font-size: .84rem; font-weight: 850; }
.status-value { color: var(--muted); font-size: .74rem; }
.status-dot { width: .52rem; height: .52rem; border-radius: 50%; display: inline-block; margin-right: .35rem; }
.status-dot.ready { background: #22a06b; box-shadow: 0 0 0 4px rgba(34,160,107,.10); }
.status-dot.waiting { background: #d97706; box-shadow: 0 0 0 4px rgba(217,119,6,.10); }

.recent-card { border-radius: 17px; padding: .72rem .8rem; margin-bottom: .38rem; }
.recent-title { color: var(--ink); font-size: .88rem; font-weight: 850; }
.recent-meta { color: var(--muted); font-size: .73rem; margin-top: .15rem; }

.topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin-bottom: .72rem;
}
.topbar-left { display: flex; align-items: center; gap: .62rem; color: var(--ink); font-weight: 950; font-size: 1.04rem; }
.topbar-logo {
    width: 2.2rem;
    height: 2.2rem;
    border-radius: 14px 14px 14px 5px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    background: linear-gradient(135deg, var(--lingnan-teal), var(--lion-orange));
    box-shadow: 0 11px 25px rgba(21,154,156,.20);
}
.topbar-nav { display: flex; flex-wrap: wrap; gap: .42rem; }
.topbar-pill {
    color: var(--lingnan-teal-dark);
    background: rgba(255,255,255,.72);
    border: 1px solid rgba(21,154,156,.14);
    border-radius: 999px;
    padding: .38rem .68rem;
    font-size: .78rem;
    font-weight: 800;
}

.hero {
    position: relative;
    overflow: hidden;
    border-radius: 30px;
    padding: 1.45rem 1.7rem;
    color: #fff;
    background:
        radial-gradient(circle at 12% 20%, rgba(21,154,156,.42), transparent 24%),
        radial-gradient(circle at 82% 18%, rgba(242,118,59,.36), transparent 27%),
        linear-gradient(132deg, #102c43 0%, #143f4e 53%, #0a5c5e 100%);
    box-shadow: 0 26px 62px rgba(22,50,79,.16);
    margin-bottom: 1.25rem;
}
.hero::before {
    content: "";
    position: absolute;
    inset: 0;
    opacity: .18;
    background-image:
        linear-gradient(45deg, transparent 46%, #fff 47%, #fff 50%, transparent 51%),
        linear-gradient(-45deg, transparent 46%, #fff 47%, #fff 50%, transparent 51%);
    background-size: 42px 42px;
    mask-image: linear-gradient(90deg, transparent 0%, #000 55%, #000 100%);
}
.hero-grid { position: relative; display: grid; grid-template-columns: 1.6fr .72fr; gap: 1.5rem; align-items: center; }
.hero-kicker {
    display: inline-flex;
    padding: .35rem .68rem;
    border-radius: 999px;
    background: rgba(255,255,255,.13);
    border: 1px solid rgba(255,255,255,.13);
    font-size: .8rem;
    font-weight: 800;
}
.hero-title { color: #fff !important; font-size: 2.75rem; line-height: 1.08; font-weight: 950; margin: .58rem 0 .35rem; letter-spacing: .025em; }
.hero-subtitle { max-width: 690px; color: rgba(255,255,255,.93); font-size: 1rem; line-height: 1.72; font-weight: 620; }
.hero-chips { display: flex; flex-wrap: wrap; gap: .42rem; margin-top: .85rem; }
.hero-chip { padding: .32rem .62rem; border-radius: 999px; background: rgba(255,255,255,.10); border: 1px solid rgba(255,255,255,.14); font-size: .76rem; }
.hero-art { display: flex; align-items: center; justify-content: center; min-height: 145px; }
.hero-seal {
    position: relative;
    width: 132px;
    height: 132px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 42% 42% 48% 48%;
    color: #fff8e9;
    background: linear-gradient(145deg, rgba(242,118,59,.98), rgba(201,60,55,.90));
    border: 7px solid rgba(255,255,255,.14);
    box-shadow: 0 22px 42px rgba(0,0,0,.20), inset 0 0 0 2px rgba(255,255,255,.18);
    font-size: 3.8rem;
    font-weight: 950;
    transform: rotate(3deg);
}
.hero-seal::before,
.hero-seal::after {
    content: "";
    position: absolute;
    top: -15px;
    width: 42px;
    height: 42px;
    border-radius: 50% 50% 45% 45%;
    background: var(--lion-orange);
    border: 5px solid rgba(255,255,255,.12);
}
.hero-seal::before { left: 5px; transform: rotate(-24deg); }
.hero-seal::after { right: 5px; transform: rotate(24deg); }

.section-heading { margin: .15rem 0 .8rem; }
.section-eyebrow { color: var(--canton-red); font-size: .74rem; font-weight: 900; letter-spacing: .08em; text-transform: uppercase; }
.section-title { color: var(--ink); font-size: 1.35rem; font-weight: 950; margin-top: .15rem; }
.section-copy { color: var(--muted); font-size: .88rem; margin-top: .22rem; }

.scene-note { border-radius: 16px; padding: .78rem .88rem; background: rgba(21,154,156,.07); border: 1px solid rgba(21,154,156,.12); margin: .45rem 0 .85rem; }
.scene-title { font-weight: 880; color: var(--lingnan-teal-dark); }
.scene-desc { color: #587080; font-size: .84rem; margin-top: .16rem; }

.prompt-hint { color: var(--muted); font-size: .8rem; margin: -.2rem 0 .45rem; }
.condition-strip { display: flex; flex-wrap: wrap; gap: .42rem; margin: .6rem 0 .15rem; }
.condition-pill { padding: .32rem .6rem; border-radius: 999px; background: rgba(21,154,156,.07); border: 1px solid rgba(21,154,156,.12); color: var(--lingnan-teal-dark); font-size: .76rem; font-weight: 800; }

.workspace-aside { border-radius: 22px; padding: 1rem; }
.workspace-aside-title { color: var(--ink); font-weight: 950; font-size: 1rem; }
.workspace-aside-copy { color: var(--muted); font-size: .82rem; line-height: 1.65; margin-top: .2rem; }
.aside-list { display: grid; gap: .48rem; margin-top: .85rem; }
.aside-item { display: flex; gap: .55rem; align-items: flex-start; padding: .58rem .62rem; border-radius: 14px; background: rgba(250,247,240,.76); border: 1px solid rgba(22,50,79,.07); }
.aside-icon { width: 1.75rem; height: 1.75rem; display: flex; align-items: center; justify-content: center; border-radius: 10px; background: rgba(21,154,156,.10); }
.aside-text strong { display: block; color: var(--ink); font-size: .8rem; }
.aside-text span { color: var(--muted); font-size: .73rem; }

.request-summary { display: flex; gap: .75rem; align-items: flex-start; border-radius: 19px; padding: .88rem 1rem; margin-bottom: .8rem; background: rgba(255,248,241,.90); border: 1px solid rgba(242,118,59,.17); }
.request-icon { font-size: 1.3rem; }
.request-label { color: #a63c17; font-size: .75rem; font-weight: 900; }
.request-main { color: var(--ink); font-weight: 760; line-height: 1.62; }
.request-meta { color: var(--muted); font-size: .78rem; margin-top: .18rem; }

.empty-state { border-radius: 24px; padding: 1.35rem; text-align: center; margin-top: .5rem; }
.empty-icon { font-size: 2.3rem; }
.empty-title { color: var(--ink); font-size: 1.08rem; font-weight: 950; margin-top: .35rem; }
.empty-copy { color: var(--muted); font-size: .84rem; margin-top: .2rem; }

.result-hero { border-radius: 22px; padding: 1rem 1.05rem; margin-bottom: .8rem; }
.result-label { color: var(--canton-red); font-size: .74rem; font-weight: 900; }
.result-title { color: var(--ink); font-size: 1.18rem; font-weight: 950; margin-top: .18rem; }
.result-meta { color: var(--muted); font-size: .79rem; margin-top: .25rem; }

.answer-shell { background: rgba(255,255,255,.94); border: 1px solid var(--line); border-radius: 22px; padding: 1rem 1.12rem; box-shadow: 0 16px 38px rgba(22,50,79,.05); }
.answer-header { display: flex; align-items: center; gap: .5rem; color: var(--lingnan-teal-dark); font-weight: 950; padding-bottom: .7rem; border-bottom: 1px solid rgba(22,50,79,.07); margin-bottom: .8rem; }
.source-box { margin-top: 1rem; padding: .82rem .95rem; background: #f7fbfa; border: 1px solid rgba(22,50,79,.07); border-radius: 16px; }

.fact-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: .65rem; margin: .65rem 0 .95rem; }
.fact-card { border-radius: 16px; padding: .72rem .78rem; }
.fact-label { color: var(--muted); font-size: .72rem; font-weight: 780; }
.fact-value { color: var(--ink); font-size: .9rem; font-weight: 900; margin-top: .12rem; }

.stButton > button,
.stDownloadButton > button {
    border-radius: 15px;
    font-weight: 820;
    min-height: 2.55rem;
    border-color: rgba(22,50,79,.11);
    transition: transform .13s ease, box-shadow .13s ease, border-color .13s ease;
}
.stButton > button:hover,
.stDownloadButton > button:hover { transform: translateY(-1px); box-shadow: 0 10px 22px rgba(22,50,79,.09); border-color: rgba(21,154,156,.26); }
.stButton > button[kind="primary"] { border: 0; min-height: 2.85rem; background: linear-gradient(92deg, var(--lingnan-teal), var(--lion-orange)); box-shadow: 0 15px 32px rgba(21,154,156,.21); color: #fff; font-weight: 920; }
.stDownloadButton > button { background: #fff; }

.stTextArea textarea,
.stTextInput input,
div[data-baseweb="select"] > div { border-radius: 15px !important; border-color: rgba(22,50,79,.11) !important; }
.stTextArea textarea:focus,
.stTextInput input:focus { border-color: rgba(21,154,156,.45) !important; box-shadow: 0 0 0 3px rgba(21,154,156,.08) !important; }

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 23px !important;
    border-color: rgba(22,50,79,.09) !important;
    background: rgba(255,255,255,.76);
    box-shadow: 0 16px 40px rgba(22,50,79,.045);
}

button[data-baseweb="tab"] { font-weight: 850; }
div[data-baseweb="tab-list"] { gap: .35rem; border-bottom: 1px solid rgba(22,50,79,.08); }
button[data-baseweb="tab"][aria-selected="true"] { color: var(--lingnan-teal-dark); }

[data-testid="stExpander"] { border-radius: 16px !important; border-color: rgba(22,50,79,.09) !important; background: rgba(255,255,255,.58); }

div[data-testid="stMarkdownContainer"] table { width: 100%; border-collapse: separate; border-spacing: 0; border: 1px solid rgba(22,50,79,.08); border-radius: 14px; overflow: hidden; font-size: .88rem; }
div[data-testid="stMarkdownContainer"] th { background: rgba(21,154,156,.08); padding: .62rem .7rem; }
div[data-testid="stMarkdownContainer"] td { padding: .62rem .7rem; border-top: 1px solid rgba(22,50,79,.06); }

@media (max-width: 920px) {
    .block-container { padding-left: .9rem; padding-right: .9rem; }
    .topbar { align-items: flex-start; flex-direction: column; }
    .hero { padding: 1.25rem 1.05rem; }
    .hero-grid { grid-template-columns: 1fr; }
    .hero-art { display: none; }
    .hero-title { font-size: 2.3rem; }
    .request-summary { flex-direction: column; }
    .fact-grid { grid-template-columns: 1fr; }
}
</style>
"""


def apply_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
