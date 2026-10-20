"""Editorial visual system for the Lingnan heritage experience.

Pure presentation: application logic and Streamlit widget keys remain untouched.
"""

from __future__ import annotations

import streamlit as st

EDITORIAL_CSS = r"""
<style>
:root {
  --ink: #202d29;
  --ink-soft: #46544b;
  --forest: #24493d;
  --forest-strong: #17372e;
  --cinnabar: #a84937;
  --ochre: #bb9861;
  --ivory: #f7f5ef;
  --paper: #fdfcf8;
  --line: #dfdfd4;
  --line-deep: #c8c9bb;
  --muted: #7b8278;
  --serif: "Noto Serif SC", "Source Han Serif SC", "Songti SC", "STSong", "SimSun", serif;
  --sans: "Inter", "PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif;
  --lingnan-teal: var(--forest);
  --lingnan-teal-dark: var(--forest-strong);
  --lion-orange: var(--cinnabar);
  --canton-red: var(--cinnabar);
}
html, body, .stApp, button, input, textarea, select {
  font-family: var(--sans) !important;
}
html { scroll-behavior: smooth; }
.stApp {
  background: #f7f5ef !important;
  background-image: none !important;
  color: var(--ink);
}
.stApp::before { display:none !important; }
header[data-testid="stHeader"] { background: rgba(247,245,239,.95) !important; }
#MainMenu, footer { visibility: hidden; }
.block-container {
  max-width: 1420px !important;
  padding: 1.05rem clamp(1rem, 3vw, 3.4rem) 6rem !important;
}
[data-testid="stAppViewContainer"] { background: transparent; }
[data-testid="stSidebar"] {
  background: #efeee6 !important;
  border-right: 1px solid #dadbce !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 1.2rem; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { line-height:1.68; }
[data-testid="stSidebar"] h3 {
  color: var(--ink);
  letter-spacing: .035em;
  font-size: .94rem !important;
  margin: 1.25rem 0 .5rem !important;
}
.brand-card {
  background: none !important;
  border: 0 !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  border-bottom: 1px solid var(--line-deep) !important;
  padding: .7rem 0 1.3rem !important;
  margin-bottom: 1.2rem !important;
}
.brand-card::after { display:none !important; }
.brand-title { font: 700 1.38rem var(--serif) !important; letter-spacing: .09em; color: var(--forest) !important; }
.brand-sub { margin-top: .56rem !important; line-height:1.8 !important; font-size:.78rem !important; color: var(--ink-soft) !important; }
.brand-badge {
  border:0 !important;
  border-radius:0 !important;
  margin-top:.8rem !important; padding:0 !important;
  background:none !important; color:var(--cinnabar) !important;
  font: 700 .6rem var(--sans) !important; letter-spacing:.17em;
}
.model-status-card {
  background:#e4eadf !important;
  border:1px solid #d5dfd3 !important;
  box-shadow:none !important; border-radius:5px !important;
  padding:.85rem 1rem !important;
}
.status-title { color:var(--forest) !important; font-size:.76rem !important; }
.status-value { color:#65776a !important; font-size:.7rem !important; margin-top:.22rem; }
.status-dot.ready { background:#397856 !important; }
.status-dot.waiting { background:var(--cinnabar) !important; }
.recent-card { border:1px solid var(--line) !important; background:var(--paper) !important; box-shadow:none !important; border-radius:4px !important; padding:.72rem .86rem !important; }
.recent-title { font-size:.78rem !important; font-weight:700 !important; }
.recent-meta { font-size:.68rem !important; line-height:1.6; }
.topbar-left {
  min-height:3.2rem !important; gap:.8rem !important;
  color:var(--forest) !important;
  font-size:1.14rem !important; font-weight:800 !important; letter-spacing:.08em;
}
.topbar-logo {
  background:var(--forest) !important; border-radius:3px !important;
  width:2.45rem !important; height:2.45rem !important;
  box-shadow:none !important; font:700 1.26rem var(--serif);
}
.editorial-brand-copy { display:flex; flex-direction:column; gap:.13rem; }
.editorial-brand-sub { display:block; color:#81867e; font-size:.55rem; letter-spacing:.18em; font-weight:650; }
.editorial-top-tag {
  font-size:.62rem; color:var(--cinnabar); letter-spacing:.16em;
  font-weight:700; padding-top:.8rem; text-align:right;
}
.topbar-nav-label { font-size:.62rem; letter-spacing:.16em; color:var(--muted); text-align:right; margin-bottom:.2rem; }
.stButton > button, .stDownloadButton > button {
  font-family:var(--sans) !important;
  border-radius:4px !important; border:1px solid var(--line-deep) !important;
  background:transparent !important; color:var(--ink) !important;
  font-weight:650 !important; box-shadow:none !important;
  min-height:2.65rem !important; transition: background .18s, border-color .18s, color .18s, transform .18s !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  transform:translateY(-1px) !important; border-color:var(--forest) !important;
  background:#e8eee7 !important; color:var(--forest) !important; box-shadow:none !important;
}
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible {
  outline:3px solid rgba(168,73,55,.35) !important; outline-offset:2px;
}
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
  background:var(--forest) !important; color:#fffdf8 !important;
  border:1px solid var(--forest) !important; border-radius:4px !important;
  box-shadow:none !important; font-weight:750 !important;
}
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover {
  background:var(--forest-strong) !important; color:#fff !important; border-color:var(--forest-strong) !important;
}
.stButton > button:disabled { opacity:.48 !important; cursor:not-allowed !important; transform:none !important; }
div[data-testid="stHorizontalBlock"]:has(.topbar-left) { padding-bottom:.52rem; }
.editorial-hero {
  position:relative;
  isolation:isolate;
  display:grid;
  grid-template-columns: .96fr 1.04fr;
  background:#e9e8dd;
  min-height:430px;
  overflow:hidden;
  border:1px solid #d7d7c9;
  border-radius:5px;
  margin:.25rem 0 1.8rem;
}
.editorial-hero-art { position:relative; grid-column:2; grid-row:1; min-height:430px; overflow:hidden; }
.editorial-hero-art img { width:100%; height:100%; object-fit:cover; object-position:70% center; position:absolute; inset:0; }
.editorial-hero-art::before { content:""; position:absolute; z-index:2; inset:0; background:linear-gradient(90deg,#e9e8dd 0%,rgba(233,232,221,.08) 34%,transparent 100%); }
.editorial-hero-art::after {
  content:"岭南印象 / CULTURAL HERITAGE";
  position:absolute; bottom:1.3rem; right:1.45rem; z-index:3;
  padding:.42rem .65rem; background:rgba(255,253,248,.9); color:var(--forest);
  font-size:.6rem; letter-spacing:.13em; font-weight:750;
}
.editorial-hero-content {
  grid-column:1;grid-row:1; z-index:3; padding:clamp(1.8rem,4vw,4.25rem) 1rem 2.5rem clamp(1.6rem,4.1vw,4.3rem);
  display:flex; flex-direction:column; align-items:flex-start; justify-content:center;
}
.editorial-hero-eyebrow { display:flex; gap:.85rem; align-items:center; font-size:.68rem; font-weight:800; letter-spacing:.17em; color:var(--cinnabar); }
.editorial-hero-eyebrow::before { content:""; width:25px; height:1px; background:var(--cinnabar); }
.editorial-hero h1 { margin:1.05rem 0 0 !important; color:var(--forest) !important; font:700 clamp(2.65rem,4.5vw,4.9rem)/1.24 var(--serif) !important; letter-spacing:.035em; }
.editorial-hero h1 span { color:var(--cinnabar); }
.editorial-hero-desc { max-width:480px; margin:1.15rem 0 1.5rem; font-size:.91rem; line-height:2.05; color:#55645a; }
.editorial-hero-foot { display:flex; align-items:center; gap:.9rem; border-top:1px solid #c9cbbd; padding-top:1.12rem; width:100%; max-width:390px; }
.editorial-hero-seal { color:var(--cinnabar); border:1px solid var(--cinnabar); width:2.85rem; height:2.85rem; display:flex; align-items:center; justify-content:center; text-align:center; font:700 .92rem/1.1 var(--serif); transform:rotate(-5deg); }
.editorial-hero-meta { color:#667267; font-size:.66rem; line-height:1.65; letter-spacing:.065em; }
.editorial-hero-meta strong { color:var(--ink); font-size:.78rem; letter-spacing:.03em; }
.editorial-ribbon { display:flex; align-items:center; justify-content:space-between; padding:0 0 1.25rem; border-bottom:1px solid var(--line); gap:1rem; flex-wrap:wrap; margin-bottom:1.75rem; }
.editorial-ribbon > div { color:var(--muted); font-size:.7rem; letter-spacing:.1em; }
.editorial-ribbon span { color:var(--cinnabar); font-weight:800; margin-right:.55rem; }
.section-heading { margin:1.05rem 0 1.05rem !important; }
.section-eyebrow { font-size:.7rem !important; color:var(--cinnabar) !important; font-weight:800 !important; letter-spacing:.18em !important; }
.section-title { margin:.46rem 0 .25rem !important; color:var(--forest) !important; font:700 clamp(1.45rem,2.2vw,2.05rem)/1.42 var(--serif) !important; letter-spacing:.03em; }
.section-copy { color:#798076 !important; font-size:.78rem !important; line-height:1.8; }
.scene-card-index { display:block; text-align:left; padding:.1rem .05rem .52rem; color:var(--cinnabar); font:700 .68rem var(--sans); letter-spacing:.16em; }
.scene-card-caption { color:#85877e; font-size:.69rem; line-height:1.55; min-height:2.4rem; padding:.48rem .22rem .1rem; }
.scene-note {
  background:none !important; border:0 !important; border-bottom:1px solid var(--line) !important;
  padding:.52rem .15rem 1rem !important; margin:.15rem 0 1.6rem !important; border-radius:0 !important;
}
.scene-title { color:var(--forest) !important; font-size:.85rem; font-weight:750; }
.scene-desc { color:#85897e !important; font-size:.75rem; margin-top:.25rem; }
[data-testid="stVerticalBlockBorderWrapper"] {
  border:1px solid var(--line) !important; box-shadow:none !important; border-radius:4px !important;
  background:var(--paper) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div { padding:1.2rem !important; }
.stTextArea textarea, .stTextInput input, div[data-baseweb="select"] > div {
  background:#fffefb !important; border:1px solid #d8d9cd !important; border-radius:3px !important; color:var(--ink) !important; box-shadow:none !important;
}
.stTextArea textarea { line-height:1.8 !important; padding:.85rem 1rem !important; }
.stTextArea textarea:focus, .stTextInput input:focus { box-shadow:0 0 0 3px rgba(36,73,61,.12) !important; border-color:var(--forest) !important; }
.stSelectbox label, .stTextArea label, .stMultiSelect label { color:var(--ink-soft) !important; font-size:.76rem; }
.prompt-hint { color:var(--muted) !important; margin:.3rem 0 .5rem !important; font-size:.7rem !important; }
.editorial-input-label { display:flex; align-items:center; justify-content:space-between; gap:1rem; margin-bottom:.55rem; }
.editorial-input-label strong { color:var(--forest); font-size:.83rem; }
.editorial-input-label span { color:#90948a; font-size:.65rem; }
.editorial-subheading { display:flex; align-items:center; justify-content:space-between; border-top:1px solid var(--line); margin-top:1.3rem; padding-top:1.2rem; margin-bottom:.6rem; }
.editorial-subheading strong { color:var(--forest); font-size:.85rem; }
.editorial-subheading small { color:var(--muted); font-size:.68rem; }
.condition-strip { margin:.86rem 0 .56rem !important; gap:.43rem !important; }
.condition-pill {
  color:#526a58 !important; background:#eef1e9 !important; border:1px solid #dce4d9 !important;
  border-radius:2px !important; padding:.36rem .55rem !important; font-size:.69rem !important; font-weight:650 !important;
}
.workspace-aside {
  position:relative; padding:1.55rem 1.25rem !important; border-radius:4px !important; background:#e9eee6 !important;
  border:1px solid #d8e1d4 !important; box-shadow:none !important;
}
.workspace-aside::before { content:"CURATED BY YUEJIAN"; display:block; font-size:.57rem; letter-spacing:.18em; color:var(--cinnabar); font-weight:800; margin-bottom:1rem; }
.workspace-aside-title { color:var(--forest) !important; font:700 1.16rem/1.6 var(--serif) !important; }
.workspace-aside-copy { color:#687568 !important; font-size:.76rem !important; line-height:1.8 !important; margin-top:.45rem !important; }
.aside-list { border-top:1px solid #d5dfd3 !important; margin-top:1.25rem !important; }
.aside-item { gap:.85rem !important; padding:.9rem 0 !important; border-bottom:1px solid #d5dfd3 !important; }
.aside-icon { border:1px solid #a9bca9 !important; background:none !important; color:var(--forest) !important; border-radius:50% !important; width:1.75rem !important; height:1.75rem !important; flex:0 0 1.75rem !important; font-size:.62rem !important; }
.aside-text strong { color:var(--forest) !important; font-size:.77rem !important; }
.aside-text span { color:#7a8879 !important; font-size:.68rem !important; line-height:1.65 !important; }
.aside-model-status { border:0 !important; margin-top:1rem !important; }
.aside-model-status strong { color:var(--forest) !important; font-size:.69rem !important; }
.editorial-aside-bottom { font:700 1.65rem var(--serif); color:#c9d4c5; margin-top:1.8rem; letter-spacing:.15em; text-align:right; }
.request-summary { border-radius:3px !important; background:#eef1e9 !important; border:1px solid #d4dfd0 !important; padding:1rem 1.2rem !important; }
.request-icon { font-size:1.4rem !important; }
.request-label { color:var(--cinnabar) !important; letter-spacing:.12em; text-transform:uppercase; }
.request-main { color:var(--forest) !important; font-size:.94rem !important; }
.empty-state {
  text-align:left !important; background:var(--paper) !important; border:1px solid var(--line) !important; box-shadow:none !important;
  border-radius:4px !important; padding:2rem clamp(1.2rem,3vw,3rem) !important; margin-top:.7rem !important;
}
.empty-icon { display:inline-flex; font-size:1.2rem !important; color:var(--cinnabar); border:1px solid #d8bfb2; width:3rem; height:3rem; justify-content:center; align-items:center; }
.empty-title { font:700 1.65rem/1.45 var(--serif) !important; color:var(--forest) !important; margin:1rem 0 .4rem !important; }
.empty-copy { font-size:.82rem !important; line-height:1.85; max-width:560px; }
.empty-features { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.9rem; margin-top:1.45rem; border-top:1px solid var(--line); padding-top:1.25rem; }
.empty-feature { color:var(--ink); font-weight:750; font-size:.76rem; }
.empty-feature span { display:block; color:var(--cinnabar); font-size:.63rem; letter-spacing:.14em; font-weight:800; margin-bottom:.4rem; }
.empty-feature small { display:block; font-size:.69rem; color:var(--muted); font-weight:400; margin-top:.36rem; line-height:1.7; }
.result-hero { background:var(--forest) !important; color:#fff !important; border:0 !important; border-radius:4px !important; padding:1.6rem 1.8rem !important; box-shadow:none !important; }
.result-label { color:#d4bba3 !important; letter-spacing:.15em; font-size:.65rem !important; }
.result-title { color:#fffdf6 !important; font:700 1.46rem/1.5 var(--serif) !important; margin-top:.55rem !important; }
.result-meta { color:#c3d0c3 !important; font-size:.72rem !important; margin-top:.9rem !important; }
.fact-grid { gap:.7rem !important; margin-bottom:1.35rem !important; }
.fact-card { padding:.9rem 1rem !important; background:#eeeee5 !important; border:1px solid var(--line) !important; border-radius:3px !important; box-shadow:none !important; }
.fact-label { color:#788076 !important; font-size:.68rem !important; }
.fact-value { color:var(--forest) !important; font-size:.87rem !important; }
button[data-baseweb="tab"] { color:#777e74 !important; font-weight:700 !important; font-size:.78rem !important; padding:.78rem .65rem !important; }
button[data-baseweb="tab"][aria-selected="true"] { color:var(--forest) !important; border-bottom-color:var(--cinnabar) !important; }
div[data-baseweb="tab-list"] { border-bottom:1px solid #dddcd1 !important; gap:.3rem !important; }
[data-testid="stExpander"] { border-radius:3px !important; border:1px solid var(--line) !important; background:#fdfcf8 !important; }
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 { color:var(--forest); letter-spacing:.015em; }
[data-testid="stMarkdownContainer"] h2 { font-family:var(--serif) !important; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { line-height:1.9; }
[data-testid="stMarkdownContainer"] table { border-radius:3px !important; }
[data-testid="stMarkdownContainer"] th { background:#e8ede5 !important; }
.editorial-footer { display:flex; justify-content:space-between; gap:.8rem; flex-wrap:wrap; padding:1.7rem 0 .2rem; border-top:1px solid var(--line); margin-top:2.8rem; color:#8b8f86; font-size:.66rem; letter-spacing:.05em; }
.editorial-footer strong { color:var(--forest); letter-spacing:.08em; }
@media(max-width:1100px) {
 .editorial-hero { min-height:380px; grid-template-columns:1.05fr .95fr; }
 .editorial-hero-art { min-height:380px; }
 .editorial-hero-content { padding:2.2rem 0 2.2rem 2rem; }
 .editorial-hero h1 { font-size:3.1rem !important; }
}
@media(max-width:900px) {
 .block-container { padding:.65rem 1.1rem 5rem !important; }
 .editorial-hero { min-height:355px; }
 .editorial-hero-content { padding:1.5rem 0 1.5rem 1.5rem; }
 .editorial-hero h1 { font-size:2.6rem !important; }
 .editorial-hero-desc { font-size:.8rem; line-height:1.85; }
 .editorial-hero-art { min-height:355px; }
 .workspace-aside { margin-top:.55rem; }
 .empty-features { grid-template-columns:1fr 1fr; }
}
@media(max-width:640px) {
 .block-container { padding:.45rem .75rem 4.5rem !important; }
 .topbar-left { min-height:2.5rem !important; font-size:.98rem !important; }
 .topbar-logo { width:2.1rem !important; height:2.1rem !important; }
 .editorial-hero { display:block; min-height:520px; margin-top:.65rem; }
 .editorial-hero-art { position:absolute; inset:auto 0 0; height:56%; min-height:0; }
 .editorial-hero-art img { object-position:65% 60%; }
 .editorial-hero-art::before { background:linear-gradient(180deg,#e9e8dd 0%,rgba(233,232,221,.05) 52%,transparent 100%); }
 .editorial-hero-art::after { right:.7rem; bottom:.7rem; font-size:.48rem; }
 .editorial-hero-content { position:relative; z-index:4; padding:1.6rem 1.3rem; min-height:255px; justify-content:flex-start; }
 .editorial-hero h1 { font-size:2.45rem !important; margin:.55rem 0 0 !important; }
 .editorial-hero-desc { margin:.7rem 0; max-width:340px; font-size:.77rem; line-height:1.72; }
 .editorial-hero-foot { display:none; }
 .editorial-ribbon { margin-bottom:1rem; }
 .editorial-ribbon > div { font-size:.6rem; }
 .section-title { font-size:1.48rem !important; }
 .scene-card-index { font-size:.62rem; padding-top:.45rem; }
 .scene-card-caption { min-height:0; font-size:.67rem; }
 .empty-features { grid-template-columns:1fr; }
 .fact-grid { grid-template-columns:1fr !important; }
 .result-hero { padding:1.3rem !important; }
 .editorial-footer { margin-top:1.5rem; }
 [data-testid="stVerticalBlockBorderWrapper"] > div { padding:.85rem !important; }
}
@media(prefers-reduced-motion:reduce) {
 *, *::before, *::after { scroll-behavior:auto !important; transition:none !important; animation:none !important; }
}
</style>
"""

def apply_editorial_styles() -> None:
    st.markdown(EDITORIAL_CSS, unsafe_allow_html=True)
