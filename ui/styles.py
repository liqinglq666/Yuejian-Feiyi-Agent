from __future__ import annotations

import streamlit as st


CSS = r"""
<style>
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
}
.stApp {
    background:
        radial-gradient(circle at 88% 4%, rgba(18,184,178,.10), transparent 24%),
        radial-gradient(circle at 6% 10%, rgba(255,122,69,.10), transparent 26%),
        linear-gradient(180deg, #ffffff 0%, #f8fcfc 48%, #ffffff 100%);
}
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 1220px; padding-top: 1rem; padding-bottom: 3rem; }
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f7fbfc 0%, #edf7f6 100%);
    border-right: 1px solid rgba(16,24,40,.06);
}
.brand-card, .recent-card, .insight-card, .settings-card {
    background: rgba(255,255,255,.88);
    border: 1px solid rgba(16,24,40,.08);
    box-shadow: 0 12px 32px rgba(16,24,40,.045);
}
.brand-card { padding: .95rem 1rem; border-radius: 22px; margin-bottom: 1rem; }
.brand-title { color: #101828; font-size: 1.22rem; font-weight: 900; }
.brand-sub { color: #667085; font-size: .88rem; line-height: 1.6; }
.recent-card { border-radius: 16px; padding: .75rem .85rem; margin-bottom: .4rem; }
.recent-title { color: #101828; font-size: .9rem; font-weight: 850; }
.recent-meta { color: #667085; font-size: .76rem; }
.topbar { display:flex; justify-content:space-between; align-items:center; gap:1rem; margin-bottom:.85rem; }
.topbar-left { display:flex; align-items:center; gap:.65rem; color:#101828; font-weight:900; font-size:1.08rem; }
.topbar-logo { width:2.35rem; height:2.35rem; border-radius:15px; display:flex; align-items:center; justify-content:center;
    background:linear-gradient(135deg,#12b8b2,#ff7a45); color:#fff; box-shadow:0 12px 28px rgba(18,184,178,.22); }
.topbar-pill { color:#0f766e; background:rgba(18,184,178,.10); border:1px solid rgba(18,184,178,.18);
    border-radius:999px; padding:.42rem .75rem; font-size:.82rem; font-weight:800; }
.hero { position:relative; overflow:hidden; border-radius:30px; min-height:230px; padding:1.8rem 2rem; color:#fff;
    background:radial-gradient(circle at 12% 20%, rgba(18,184,178,.46), transparent 25%),
    radial-gradient(circle at 82% 16%, rgba(255,122,69,.34), transparent 27%),
    radial-gradient(circle at 72% 82%, rgba(47,128,237,.32), transparent 28%),
    linear-gradient(135deg,#07132b 0%,#10284b 54%,#073f46 100%);
    box-shadow:0 24px 60px rgba(15,23,42,.14); margin-bottom:1.35rem; }
.hero-kicker { display:inline-flex; padding:.38rem .72rem; border-radius:999px; background:rgba(255,255,255,.14); font-weight:750; }
.hero-title { color:#fff!important; font-size:3.7rem; line-height:1.05; font-weight:950; margin:.7rem 0 .4rem; letter-spacing:.03em; }
.hero-subtitle { max-width:700px; color:rgba(255,255,255,.95); font-size:1.05rem; line-height:1.75; font-weight:650; }
.hero-chips { display:flex; flex-wrap:wrap; gap:.45rem; margin-top:1rem; }
.hero-chip { padding:.35rem .68rem; border-radius:999px; background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.16); font-size:.82rem; }
.scene-note { border-radius:16px; padding:.82rem .9rem; background:#f2fbfa; border:1px solid rgba(18,184,178,.14); margin:.5rem 0 1rem; }
.scene-title { font-weight:850; color:#0f766e; }
.scene-desc { color:#506173; font-size:.88rem; margin-top:.2rem; }
.request-summary { display:flex; gap:.8rem; align-items:flex-start; border-radius:18px; padding:.9rem 1rem; margin-bottom:.8rem;
    background:#fff8f3; border:1px solid rgba(255,122,69,.16); }
.request-icon { font-size:1.35rem; }
.request-label { color:#b54708; font-size:.78rem; font-weight:850; }
.request-main { color:#101828; font-weight:750; line-height:1.65; }
.request-meta { color:#667085; font-size:.8rem; margin-top:.2rem; }
.answer-shell { background:#fff; border:1px solid rgba(16,24,40,.08); border-radius:22px; padding:1rem 1.15rem;
    box-shadow:0 16px 38px rgba(16,24,40,.05); }
.answer-header { display:flex; align-items:center; gap:.5rem; color:#0f766e; font-weight:900; padding-bottom:.7rem; border-bottom:1px solid rgba(16,24,40,.06); margin-bottom:.8rem; }
.source-box { margin-top:1rem; padding:.85rem 1rem; background:#f7fbfc; border:1px solid rgba(16,24,40,.07); border-radius:16px; }
.stButton > button { border-radius:15px; font-weight:800; min-height:2.55rem; transition:transform .12s ease,box-shadow .12s ease; }
.stButton > button:hover { transform:translateY(-1px); box-shadow:0 10px 22px rgba(16,24,40,.08); }
.stButton > button[kind="primary"] { border:0; min-height:3rem; border-radius:17px;
    background:linear-gradient(90deg,#12b8b2,#ff7a45); box-shadow:0 16px 34px rgba(18,184,178,.23); font-weight:900; }
.stTextArea textarea, div[data-baseweb="select"] > div { border-radius:15px; }
div[data-testid="stMarkdownContainer"] table { width:100%; border-collapse:separate; border-spacing:0; border:1px solid rgba(16,24,40,.08);
    border-radius:14px; overflow:hidden; font-size:.9rem; }
div[data-testid="stMarkdownContainer"] th { background:#f2fbfa; padding:.65rem .72rem; }
div[data-testid="stMarkdownContainer"] td { padding:.65rem .72rem; border-top:1px solid rgba(16,24,40,.06); }
@media (max-width: 920px) {
    .topbar { align-items:flex-start; flex-direction:column; }
    .hero { min-height:250px; padding:1.5rem 1.2rem; }
    .hero-title { font-size:3rem; }
    .request-summary { flex-direction:column; }
}
</style>
"""


def apply_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
