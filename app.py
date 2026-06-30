from __future__ import annotations

from datetime import datetime
from pathlib import Path
import base64
import html
import re
import time

import streamlit as st

from agent import ask_agent

try:
    from agent import ask_agent_stream
except Exception:
    ask_agent_stream = None

from rag import load_knowledge_base


# =========================================================
# 页面配置
# =========================================================
st.set_page_config(
    page_title="粤见非遗｜广东非遗体验工作台",
    page_icon="🦁",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# 基础工具
# =========================================================
def image_to_base64(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def find_first_existing_image(paths: list[str]) -> str:
    for path in paths:
        if Path(path).exists():
            return path
    return ""


@st.cache_data(show_spinner=False)
def preload_knowledge_base() -> str:
    try:
        return load_knowledge_base()
    except Exception:
        return ""


def scene_example(scene: str) -> str:
    return {
        "游客路线": "我第一次来广州，有一天时间，想体验岭南非遗文化，最好适合拍照和写研学记录。",
        "学生研学": "我是高中生，要做一份广东非遗研学报告，请帮我设计任务卡，主题围绕粤剧、醒狮和广绣。",
        "亲子体验": "我周末带孩子去佛山，想体验醒狮和石湾陶塑，节奏轻松一点，最好有互动任务。",
        "内容创作": "帮我写一条介绍潮汕英歌舞的 60 秒短视频脚本，风格有画面感，适合抖音发布。",
    }.get(scene, "")


def scene_desc(scene: str) -> str:
    return {
        "游客路线": "生成城市文化路线、每站看点、拍照建议与出发提醒。",
        "学生研学": "生成研学主题、观察任务、采访问题、记录表和报告提纲。",
        "亲子体验": "生成轻松路线、孩子互动任务、休息节奏和安全提醒。",
        "内容创作": "生成标题、正文、短视频分镜、旁白、配图建议和标签。",
    }.get(scene, "")


def scene_icon(scene: str) -> str:
    return {
        "游客路线": "🧭",
        "学生研学": "📚",
        "亲子体验": "👨‍👩‍👧",
        "内容创作": "🎬",
    }.get(scene, "🦁")


def scene_result_title(scene: str) -> str:
    return {
        "游客路线": "非遗体验路线",
        "学生研学": "研学任务方案",
        "亲子体验": "亲子非遗方案",
        "内容创作": "传播内容方案",
    }.get(scene, "广东非遗方案")


def default_identity(scene: str) -> str:
    return {
        "游客路线": "外地游客",
        "学生研学": "学生研学",
        "亲子体验": "亲子家庭",
        "内容创作": "内容创作者",
    }.get(scene, "用户")


def build_scene_prompt(scene: str) -> str:
    base = {
        "游客路线": """
请生成一份广东非遗体验路线方案。
输出结构请包含：
## 方案总览
- 路线主题
- 适合人群
- 推荐节奏
- 路线亮点

## 行程时间轴
用表格展示：时间段、地点、体验重点、建议停留时间。

## 节点详情
每个地点包含：为什么去、看什么、怎么体验、适合拍什么、注意事项。

## 可选延展
给出可继续改成半天、亲子版、研学版或内容创作版的建议。
""",
        "学生研学": """
请生成一份广东非遗研学任务方案。
输出结构请包含：
## 研学主题
给出一个明确、有研究价值的主题。

## 学习目标
列出 3-5 个目标。

## 行前准备
说明要提前了解什么、准备什么。

## 现场任务卡
用表格展示：任务、观察对象、记录方式、思考问题。

## 采访问题
给出适合采访讲解员、游客、同学或传承人的问题。

## 报告提纲
给出可直接写作的报告结构。
""",
        "亲子体验": """
请生成一份适合亲子家庭的广东非遗体验方案。
输出结构请包含：
## 方案总览
- 主题名
- 适合年龄
- 节奏建议
- 亲子亮点

## 轻松行程
用表格展示：时间段、地点、孩子能做什么、家长注意事项。

## 互动任务
设计 4-6 个“找一找、听一听、拍一拍、画一画、问一问”的互动任务。

## 休息与安全提醒
给出轻松出行建议，不要安排过密。
""",
        "内容创作": """
请生成一份广东非遗内容创作方案。
输出结构请包含：
## 内容定位
说明适合平台、受众和风格。

## 标题候选
给出 5 个标题。

## 正文文案
给出一版可直接发布的图文文案。

## 60 秒短视频脚本
用表格展示：时间、画面、旁白、字幕、拍摄建议。

## 标签与配图建议
给出标签和画面建议。
""",
    }.get(scene, "请生成一份广东非遗文化方案。")

    return base.strip()


def build_final_input(
    scene: str,
    city: str,
    duration: str,
    user_input: str,
    output_style: str,
    identity: str,
    interests: list[str],
) -> str:
    parts = [
        f"用途：{scene}",
        f"输出风格：{output_style}",
    ]

    if city != "自动判断":
        parts.append(f"城市：{city}")

    if duration != "自动判断":
        parts.append(f"时间：{duration}")

    if identity != "自动匹配":
        parts.append(f"身份：{identity}")
    else:
        parts.append(f"身份：{default_identity(scene)}")

    if interests:
        parts.append("特别想包含：" + "、".join(interests))

    layout_rule = """
【网页输出要求】
1. 不要使用一级标题 #，只使用二级标题 ## 和三级标题 ###。
2. 不要在正文或表格中使用 HTML 标签，尤其不要输出 <br>、<br/>、<br />。
3. 表格单元格里不要换行；多个动作请用“；”分隔。
4. 不要输出空编号、空列表项，例如不要单独输出“4”“5”“-”。
5. 内容要适合网页阅读：短段落、清晰表格、可执行建议。
6. 不要写成论文，不要过度堆砌形容词。
7. 涉及开放时间、票价、预约、演出和交通，请提醒以官方平台为准。
""".strip()

    return (
        f"{build_scene_prompt(scene)}\n\n"
        f"【用户需求】\n{user_input.strip()}\n\n"
        f"【补充条件】" + "；".join(parts) + "\n\n" +
        layout_rule
    ).strip()


def clean_request_text(raw_input: str) -> tuple[str, str]:
    main = raw_input
    meta = ""

    if "【用户需求】" in raw_input:
        main = raw_input.split("【用户需求】", 1)[1]
        if "【补充条件】" in main:
            main, meta = main.split("【补充条件】", 1)

    if "【网页输出要求】" in meta:
        meta = meta.split("【网页输出要求】", 1)[0]

    main = re.sub(r"\n{2,}", "\n", main).strip()
    meta = meta.replace("；", " · ").strip()

    return main, meta



def sanitize_model_output(text: str) -> str:
    """
    清理模型输出中常见的网页排版问题：
    1. 把 <br> / <br/> / &lt;br&gt; 这类标签替换成中文分号，避免在表格中原样显示。
    2. 删除单独成行的空编号，例如“4”“5.”“6、”。
    3. 删除空列表项。
    4. 合并过多空行，保证网页阅读更干净。
    """
    if not text:
        return ""

    cleaned = str(text)

    # 处理模型误输出的 HTML 换行标签
    cleaned = re.sub(r"(?i)&lt;\s*br\s*/?\s*&gt;", "；", cleaned)
    cleaned = re.sub(r"(?i)<\s*br\s*/?\s*>", "；", cleaned)

    # 处理常见 HTML 实体
    cleaned = cleaned.replace("&nbsp;", " ")
    cleaned = cleaned.replace("&amp;", "&")
    cleaned = cleaned.replace("&lt;", "<").replace("&gt;", ">")

    # 清理连续分号 / 空格
    cleaned = re.sub(r"\s*；\s*；+\s*", "；", cleaned)
    cleaned = re.sub(r"；\s*", "；", cleaned)

    # 删除空编号、空 bullet
    lines: list[str] = []
    for line in cleaned.splitlines():
        stripped = line.strip()

        if re.fullmatch(r"\d+\s*[.)、．]?", stripped):
            continue

        if re.fullmatch(r"[-*+•]\s*", stripped):
            continue

        lines.append(line.rstrip())

    cleaned = "\n".join(lines)

    # 轻微规范 bullet
    cleaned = cleaned.replace("• ", "- ")

    # 合并过多空行
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


def guess_plan_title(raw_input: str, scene: str = "") -> str:
    main, _ = clean_request_text(raw_input)

    city_match = re.search(r"(广州|佛山|潮州|汕头|深圳|梅州|江门|珠海|东莞)", raw_input)
    city = city_match.group(1) if city_match else ""

    scene = scene or "方案"
    short_scene = scene.replace("游客", "").replace("学生", "")

    if city:
        return f"{city}{short_scene}"

    if len(main) > 14:
        return main[:14] + "…"

    return main or "当前方案"


def add_recent_plan(title: str, prompt: str, answer: str, scene: str) -> None:
    item = {
        "title": title,
        "prompt": prompt,
        "answer": answer,
        "scene": scene,
        "time": datetime.now().strftime("%H:%M"),
    }

    recent = st.session_state.get("recent_plans", [])
    recent = [x for x in recent if x.get("answer") != answer]
    recent.insert(0, item)
    st.session_state.recent_plans = recent[:3]


def set_toast(message: str, icon: str = "🦁") -> None:
    st.session_state.toast_message = message
    st.session_state.toast_icon = icon


def show_pending_toast() -> None:
    message = st.session_state.get("toast_message", "")
    icon = st.session_state.get("toast_icon", "🦁")

    if message:
        st.toast(message, icon=icon)
        st.session_state.toast_message = ""
        st.session_state.toast_icon = "🦁"



def get_runtime_api_config() -> dict:
    """
    获取当前会话使用的模型配置。

    本版本为“仅用户自填 API Key 版”：
    - 使用用户在页面中填写的 API Key
    - 不读取公开部署环境中的默认模型 Key
    - 生成请求通过用户侧模型服务完成
    """
    api_key = st.session_state.get("user_api_key", "").strip()
    base_url = st.session_state.get(
        "user_base_url",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ).strip()
    model_name = st.session_state.get("user_model_name", "qwen-turbo").strip()

    if not api_key:
        raise RuntimeError("请先在左侧「模型接入」中填写 API Key 后再生成。")

    return {
        "api_key": api_key,
        "base_url": base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model_name": model_name or "qwen-turbo",
    }


def generate_answer(final_input: str, temperature: float, action_label: str) -> str:
    placeholder = st.empty()

    progress_steps = {
        "正在生成你的非遗方案…": [
            "正在理解你的需求",
            "正在匹配广东非遗知识",
            "正在整理方案结构",
            "正在生成可复制结果",
        ],
        "正在压缩成半天路线…": [
            "正在保留最值得去的节点",
            "正在压缩时间安排",
            "正在优化路线节奏",
            "正在生成半天版本",
        ],
        "正在改成亲子友好版…": [
            "正在降低行程强度",
            "正在设计孩子能参与的任务",
            "正在补充休息与安全提醒",
            "正在生成亲子版本",
        ],
        "正在生成小红书文案…": [
            "正在提炼内容亮点",
            "正在生成标题和正文",
            "正在补充配图建议",
            "正在整理话题标签",
        ],
        "正在生成短视频脚本…": [
            "正在提炼开头钩子",
            "正在拆分 60 秒分镜",
            "正在生成旁白字幕",
            "正在补充拍摄建议",
        ],
        "正在补充研学记录表…": [
            "正在提炼研学主题",
            "正在设计观察任务",
            "正在补充采访问题",
            "正在生成记录表",
        ],
    }

    steps = progress_steps.get(action_label, progress_steps["正在生成你的非遗方案…"])

    if ask_agent_stream is not None:
        full_answer = ""
        try:
            with st.status(action_label, expanded=True) as status:
                for step in steps:
                    st.write(step)
                    time.sleep(0.12)

                for chunk in ask_agent_stream(final_input, temperature=temperature, **get_runtime_api_config()):
                    full_answer += chunk
                    placeholder.markdown(sanitize_model_output(full_answer) + "▌")

                status.update(label="方案已生成", state="complete", expanded=False)

            full_answer = sanitize_model_output(full_answer)
            if full_answer:
                placeholder.markdown(full_answer)
                return full_answer

        except Exception:
            placeholder.warning("流式输出暂时不可用，正在自动切换为普通生成……")

    try:
        with st.status(action_label, expanded=True) as status:
            for step in steps:
                st.write(step)
                time.sleep(0.08)

            answer = ask_agent(final_input, temperature=temperature, **get_runtime_api_config())
            status.update(label="方案已生成", state="complete", expanded=False)

        answer = sanitize_model_output(answer)
        placeholder.markdown(answer)
        return answer

    except Exception as exc:
        error_text = (
            f"生成失败：{exc}\n\n"
            "请检查 `.env`、API Key、OPENAI_BASE_URL、MODEL_NAME 和网络连接。"
        )
        placeholder.error(error_text)
        return error_text


def render_request_summary(raw_input: str) -> None:
    main, meta = clean_request_text(raw_input)
    main = html.escape(main)
    meta = html.escape(meta)

    st.markdown(
        f"""
        <div class="request-summary">
            <div class="request-icon">🍊</div>
            <div class="request-body">
                <div class="request-label">本次需求</div>
                <div class="request-main">{main}</div>
                <div class="request-meta">{meta}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def queue_generation(prompt: str, temperature: float, action_label: str = "正在生成你的非遗方案…") -> None:
    st.session_state.pending_input = prompt
    st.session_state.pending_temperature = temperature
    st.session_state.pending_generate = True
    st.session_state.pending_action_label = action_label
    st.rerun()


def make_followup_prompt(instruction: str) -> str:
    base = st.session_state.get("last_answer", "")
    last_user = ""
    if len(st.session_state.get("messages", [])) >= 2:
        last_user = st.session_state.messages[-2]["content"]

    return f"""
请基于上一版结果继续优化。

【原始需求】
{last_user}

【上一版结果】
{base}

【本次修改要求】
{instruction}

【输出要求】
不要使用一级标题。不要使用 <br>、<br/>、<br /> 等 HTML 标签。不要输出空编号或空列表项。请直接给出优化后的完整结果，不要解释你做了什么。
""".strip()


preload_knowledge_base()


# =========================================================
# CSS
# =========================================================
st.markdown(
    """
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

    header[data-testid="stHeader"] { background: rgba(255,255,255,0); }
    #MainMenu, footer { visibility: hidden; }
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"] {
        display: none !important;
        visibility: hidden !important;
    }

    .block-container {
        max-width: 1200px;
        padding-top: 1rem;
        padding-bottom: 3rem;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f7fbfc 0%, #edf7f6 100%);
        border-right: 1px solid rgba(16,24,40,.06);
    }

    .brand-card {
        padding: .95rem 1rem;
        border-radius: 22px;
        background: rgba(255,255,255,.88);
        border: 1px solid rgba(16,24,40,.08);
        box-shadow: 0 12px 32px rgba(16,24,40,.045);
        margin-bottom: 1rem;
    }

    .brand-title {
        color: #101828;
        font-size: 1.22rem;
        font-weight: 950;
        letter-spacing: -.04em;
        margin-bottom: .18rem;
    }

    .brand-sub {
        color: #667085;
        font-size: .88rem;
        line-height: 1.6;
    }

    .recent-card {
        background: rgba(255,255,255,.76);
        border: 1px solid rgba(16,24,40,.08);
        border-radius: 18px;
        padding: .8rem .88rem;
        margin-bottom: .65rem;
        box-shadow: 0 10px 24px rgba(16,24,40,.035);
    }

    .recent-title {
        color: #101828;
        font-size: .92rem;
        font-weight: 900;
        margin-bottom: .15rem;
    }

    .recent-meta {
        color: #667085;
        font-size: .78rem;
        line-height: 1.45;
    }

    .tip-card {
        background: rgba(255,255,255,.88);
        border: 1px solid rgba(16,24,40,.08);
        border-radius: 18px;
        padding: .92rem .98rem;
        color: #24506b;
        font-size: .9rem;
        line-height: 1.72;
        box-shadow: 0 10px 26px rgba(16,24,40,.04);
    }

    .topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        margin-bottom: .85rem;
    }

    .topbar-left {
        display: flex;
        align-items: center;
        gap: .65rem;
        color: #101828;
        font-weight: 950;
        letter-spacing: -.04em;
        font-size: 1.08rem;
    }

    .topbar-logo {
        width: 2.35rem;
        height: 2.35rem;
        border-radius: 15px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #12b8b2, #ff7a45);
        color: white;
        box-shadow: 0 12px 28px rgba(18,184,178,.22);
    }

    .topbar-pill {
        color: #0f766e;
        background: rgba(18,184,178,.10);
        border: 1px solid rgba(18,184,178,.18);
        border-radius: 999px;
        padding: .42rem .75rem;
        font-size: .82rem;
        font-weight: 850;
        white-space: nowrap;
    }

    .hero {
        position: relative;
        overflow: hidden;
        border-radius: 30px;
        min-height: 225px;
        padding: 1.72rem 2rem;
        color: white;
        box-shadow: 0 24px 60px rgba(15,23,42,.14), inset 0 0 0 1px rgba(255,255,255,.12);
        isolation: isolate;
    }

    .hero::before {
        content: "";
        position: absolute;
        inset: 0;
        z-index: 0;
        background:
            radial-gradient(circle at 14% 20%, rgba(18,184,178,.32), transparent 25%),
            radial-gradient(circle at 88% 70%, rgba(255,122,69,.18), transparent 25%),
            linear-gradient(90deg, rgba(4,13,32,.98) 0%, rgba(7,23,51,.92) 42%, rgba(7,23,51,.54) 70%, rgba(7,23,51,.22) 100%);
    }

    .hero-inner { position: relative; z-index: 1; max-width: 720px; }

    .hero-kicker {
        display: inline-flex;
        padding: .38rem .72rem;
        border-radius: 999px;
        background: rgba(255,255,255,.14);
        border: 1px solid rgba(255,255,255,.22);
        color: rgba(255,255,255,.95);
        font-size: .82rem;
        font-weight: 850;
        margin-bottom: .68rem;
    }

    .hero-title {
        color: #ffffff !important;
        font-family:
            "华文行楷",
            "STXingkai",
            "方正姚体",
            "FZYaoti",
            "KaiTi",
            "楷体",
            "STKaiti",
            "Microsoft YaHei",
            sans-serif;
        display: inline-block;
        font-size: 3.75rem;
        line-height: 1.05;
        font-weight: 800;
        letter-spacing: .045em;
        margin: 0 0 .72rem 0;
        padding: .08rem .2rem .14rem .02rem;
        opacity: 1 !important;
        mix-blend-mode: normal !important;
        text-shadow:
            0 2px 0 rgba(255,255,255,.20),
            0 7px 18px rgba(0,0,0,.70),
            0 0 18px rgba(255,255,255,.40),
            0 0 36px rgba(18,184,178,.34);
        -webkit-text-stroke: .75px rgba(255,255,255,.62);
        filter: drop-shadow(0 10px 22px rgba(0,0,0,.42));
    }

    .hero-subtitle {
        max-width: 650px;
        color: rgba(255,255,255,.92);
        font-size: .98rem;
        line-height: 1.7;
        margin-bottom: .72rem;
    }

    .hero-chips {
        display: flex;
        flex-wrap: wrap;
        gap: .5rem;
        margin-top: .7rem;
    }

    .hero-chip {
        padding: .4rem .68rem;
        border-radius: 999px;
        background: rgba(255,255,255,.12);
        border: 1px solid rgba(255,255,255,.20);
        color: rgba(255,255,255,.94);
        font-weight: 820;
        font-size: .82rem;
    }

    .workspace {
        margin-top: 1rem;
    }

    .form-title {
        color: #101828;
        font-size: 1.32rem;
        font-weight: 950;
        letter-spacing: -.045em;
        margin: .1rem 0 .34rem;
    }

    .form-desc {
        color: #667085;
        line-height: 1.62;
        font-size: .92rem;
        margin-bottom: .85rem;
    }

    .scene-note {
        border-radius: 18px;
        padding: .82rem .9rem;
        background: linear-gradient(135deg, rgba(18,184,178,.10), rgba(255,122,69,.07));
        border: 1px solid rgba(18,184,178,.16);
        margin: .7rem 0 .95rem;
    }

    .scene-title {
        color: #101828;
        font-weight: 930;
        margin-bottom: .22rem;
    }

    .scene-desc {
        color: #667085;
        line-height: 1.56;
        font-size: .9rem;
    }

    .insight-card, .action-card, .guide-card {
        background: rgba(255,255,255,.96);
        border: 1px solid rgba(16,24,40,.08);
        border-radius: 24px;
        padding: 1rem 1.05rem;
        box-shadow: 0 16px 42px rgba(16,24,40,.055);
        margin-bottom: .85rem;
    }

    .card-kicker {
        color: #0f766e;
        font-size: .80rem;
        font-weight: 900;
        margin-bottom: .28rem;
    }

    .card-title {
        color: #101828;
        font-size: 1.1rem;
        line-height: 1.46;
        font-weight: 950;
        margin-bottom: .45rem;
    }

    .card-desc {
        color: #667085;
        line-height: 1.62;
        font-size: .9rem;
    }

    .settings-card {
        background: #fffaf7;
        border: 1px solid rgba(255,122,69,.16);
        border-radius: 22px;
        padding: .95rem 1rem;
        color: #7a3d20;
        line-height: 1.7;
        font-size: .88rem;
        margin-bottom: .85rem;
    }

    .result-title-row {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 1rem;
        margin: 1.35rem 0 .85rem;
    }

    .result-title-row h2 {
        color: #101828;
        font-size: 1.3rem;
        font-weight: 950;
        letter-spacing: -.045em;
        margin: 0;
    }

    .result-title-row span {
        color: #667085;
        font-size: .9rem;
    }

    .request-summary {
        display: flex;
        gap: .9rem;
        align-items: flex-start;
        background: rgba(255,255,255,.96);
        border: 1px solid rgba(16,24,40,.08);
        border-radius: 22px;
        padding: 1rem 1.1rem;
        box-shadow: 0 12px 32px rgba(16,24,40,.045);
        margin-bottom: .95rem;
    }

    .request-icon {
        flex: 0 0 auto;
        width: 2.3rem;
        height: 2.3rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 14px;
        background: linear-gradient(135deg, #ff7a45, #ff4d4f);
        color: white;
        font-size: 1.12rem;
    }

    .request-label {
        color: #0f766e;
        font-size: .82rem;
        font-weight: 900;
        margin-bottom: .25rem;
    }

    .request-main {
        color: #101828;
        font-size: 1rem;
        line-height: 1.72;
        font-weight: 680;
        margin-bottom: .45rem;
    }

    .request-meta {
        color: #667085;
        font-size: .88rem;
        line-height: 1.55;
    }

    .answer-shell {
        background: rgba(255,255,255,.98);
        border: 1px solid rgba(16,24,40,.08);
        border-radius: 24px;
        padding: 1rem 1.08rem;
        box-shadow: 0 18px 45px rgba(16,24,40,.055);
        margin-bottom: 1rem;
    }

    .answer-header {
        display: flex;
        align-items: center;
        gap: .55rem;
        color: #101828;
        font-weight: 950;
        font-size: 1rem;
        margin-bottom: .75rem;
    }

    .answer-icon {
        width: 2rem;
        height: 2rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 12px;
        background: #f2fbfa;
        border: 1px solid rgba(18,184,178,.18);
    }

    /* Markdown 输出美化 */
    div[data-testid="stMarkdownContainer"] h1 {
        font-size: 1.55rem !important;
        line-height: 1.28 !important;
        letter-spacing: -.04em !important;
        margin: .9rem 0 .65rem !important;
        color: #101828 !important;
    }

    div[data-testid="stMarkdownContainer"] h2 {
        font-size: 1.25rem !important;
        line-height: 1.35 !important;
        letter-spacing: -.035em !important;
        margin: 1.15rem 0 .55rem !important;
        color: #101828 !important;
    }

    div[data-testid="stMarkdownContainer"] h3 {
        font-size: 1.02rem !important;
        line-height: 1.45 !important;
        margin: .95rem 0 .38rem !important;
        color: #101828 !important;
    }

    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] li {
        font-size: .94rem !important;
        line-height: 1.76 !important;
        color: #344054 !important;
    }

    div[data-testid="stMarkdownContainer"] blockquote {
        border-left: 4px solid rgba(18,184,178,.35) !important;
        background: #f7fbfc !important;
        padding: .72rem 1rem !important;
        border-radius: 0 14px 14px 0 !important;
        margin: .8rem 0 !important;
    }

    div[data-testid="stMarkdownContainer"] table {
        width: 100% !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
        border: 1px solid rgba(16,24,40,.08) !important;
        border-radius: 16px !important;
        overflow: hidden !important;
        font-size: .9rem !important;
        margin: .7rem 0 .9rem !important;
    }

    div[data-testid="stMarkdownContainer"] th {
        background: #f2fbfa !important;
        color: #101828 !important;
        font-weight: 850 !important;
        padding: .68rem .76rem !important;
        border-bottom: 1px solid rgba(16,24,40,.08) !important;
    }

    div[data-testid="stMarkdownContainer"] td {
        padding: .68rem .76rem !important;
        border-bottom: 1px solid rgba(16,24,40,.06) !important;
        color: #344054 !important;
    }

    div[data-testid="stMarkdownContainer"] tr:last-child td {
        border-bottom: none !important;
    }

    div[data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    .stButton > button {
        border-radius: 15px;
        font-weight: 850;
        min-height: 2.55rem;
        transition: transform .12s ease, box-shadow .12s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 22px rgba(16,24,40,.08);
    }

    .stButton > button[kind="primary"] {
        border: 0;
        min-height: 3rem;
        border-radius: 17px;
        background: linear-gradient(90deg, #12b8b2, #ff7a45);
        box-shadow: 0 16px 34px rgba(18,184,178,.23);
        font-weight: 950;
    }

    .stTextArea textarea,
    div[data-baseweb="select"] > div { border-radius: 15px; }

    @media (max-width: 920px) {
        .topbar { align-items: flex-start; flex-direction: column; }
        .hero { min-height: 250px; padding: 1.55rem 1.25rem; }
        .hero-title { font-size: 3rem; letter-spacing: .025em; }
        .request-summary { flex-direction: column; }
    }
    
    /* Hero 标题强制覆盖：防止 Markdown 全局 h1 样式把标题改成深色 */
    .hero .hero-title,
    .hero h1.hero-title,
    div[data-testid="stMarkdownContainer"] .hero h1.hero-title {
        color: #ffffff !important;
        opacity: 1 !important;
        -webkit-text-fill-color: #ffffff !important;
        text-shadow:
            0 2px 0 rgba(255,255,255,.18),
            0 7px 18px rgba(0,0,0,.75),
            0 0 20px rgba(255,255,255,.42),
            0 0 42px rgba(18,184,178,.40) !important;
    }

    .hero .hero-subtitle {
        color: rgba(255,255,255,.96) !important;
        text-shadow: 0 8px 20px rgba(0,0,0,.45);
        font-weight: 780;
    }
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 状态
# =========================================================
SCENES = ["游客路线", "学生研学", "亲子体验", "内容创作"]

EXAMPLES = {
    "广州一日路线": {"scene": "游客路线", "text": scene_example("游客路线")},
    "高中研学任务": {"scene": "学生研学", "text": scene_example("学生研学")},
    "佛山亲子体验": {"scene": "亲子体验", "text": scene_example("亲子体验")},
    "英歌舞短视频": {"scene": "内容创作", "text": scene_example("内容创作")},
}

DEFAULTS = {
    "messages": [],
    "last_answer": "",
    "selected_scene": "游客路线",
    "last_scene": "游客路线",
    "user_input": scene_example("游客路线"),
    "pending_generate": False,
    "pending_input": "",
    "pending_temperature": 0.62,
    "pending_action_label": "正在生成你的非遗方案…",
    "recent_plans": [],
    "toast_message": "",
    "toast_icon": "🦁",
    "user_api_key": "",
    "user_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "user_model_name": "qwen-turbo",
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

show_pending_toast()


# =========================================================
# 侧边栏：轻量辅助区
# =========================================================
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

    st.markdown("### 最近生成")

    if st.session_state.recent_plans:
        for idx, item in enumerate(st.session_state.recent_plans):
            title = html.escape(item.get("title", "未命名方案"))
            meta = html.escape(f'{item.get("scene", "方案")} · {item.get("time", "")}')
            st.markdown(
                f"""
                <div class="recent-card">
                    <div class="recent-title">{title}</div>
                    <div class="recent-meta">{meta}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("查看", key=f"load_recent_{idx}", use_container_width=True):
                st.session_state.messages = [
                    {"role": "user", "content": item.get("prompt", "")},
                    {"role": "assistant", "content": item.get("answer", "")},
                ]
                st.session_state.last_answer = item.get("answer", "")
                st.session_state.pending_generate = False
                set_toast(f"已载入：{item.get('title', '方案')}", "📌")
                st.rerun()
    else:
        st.caption("你生成过的方案会显示在这里，方便回看。")

    st.divider()

    with st.expander("更多偏好", expanded=False):
        output_style = st.selectbox(
            "输出风格",
            ["清晰实用", "游客友好", "研学报告", "小红书风格", "专业讲解"],
            index=0,
        )
        temperature = st.slider(
            "表达灵活度",
            min_value=0.1,
            max_value=1.0,
            value=0.62,
            step=0.05,
            help="数值越高，文字更活泼；数值越低，方案更稳妥。",
        )

    st.divider()

    with st.expander("模型接入", expanded=True):
        st.caption("请配置 OpenAI 兼容模型服务。API Key 仅用于当前会话调用，不会写入项目文件。")

        st.text_input(
            "API Key",
            type="password",
            key="user_api_key",
            placeholder="请输入 API Key",
            help="密钥仅用于当前会话中的模型调用，不会写入代码文件或公开仓库。",
        )

        provider = st.selectbox(
            "接口服务",
            ["阿里云百炼 Qwen", "DeepSeek", "自定义 OpenAI 兼容接口"],
            index=0,
        )

        default_base_url = {
            "阿里云百炼 Qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "DeepSeek": "https://api.deepseek.com",
            "自定义 OpenAI 兼容接口": st.session_state.get(
                "user_base_url",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
        }[provider]

        st.text_input(
            "Base URL",
            key="user_base_url",
            value=default_base_url,
        )

        model_options = {
            "阿里云百炼 Qwen": ["qwen-turbo", "qwen-plus", "qwen-max"],
            "DeepSeek": ["deepseek-chat"],
            "自定义 OpenAI 兼容接口": [
                st.session_state.get("user_model_name", "qwen-turbo")
            ],
        }[provider]

        selected_model = st.selectbox(
            "模型名称",
            model_options,
            index=0,
        )

        if provider == "自定义 OpenAI 兼容接口":
            st.text_input(
                "自定义模型名称",
                key="user_model_name",
                value=selected_model,
            )
        else:
            st.session_state.user_model_name = selected_model

        st.info("已启用用户侧模型接入：本次生成将通过你填写的接口配置完成。", icon="🔐")

    st.divider()

    if st.button("重新开始", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_answer = ""
        st.session_state.pending_generate = False
        set_toast("已清空当前方案，可以重新开始", "🧹")
        st.rerun()

    with st.expander("如何写得更准？", expanded=False):
        st.markdown(
            """
            写清楚四件事就够了：

            - 去哪里
            - 多久
            - 和谁
            - 想体验什么

            例如：广州，一天，想看非遗、拍照和写研学记录。
            """
        )


# =========================================================
# 顶部和 Hero
# =========================================================
st.markdown(
    """
    <div class="topbar">
        <div class="topbar-left">
            <div class="topbar-logo">粤</div>
            <div>粤见非遗</div>
        </div>
        <div class="topbar-pill">广东非遗体验工作台</div>
    </div>
    """,
    unsafe_allow_html=True,
)

hero_image_path = find_first_existing_image(
    [
        "assets/hero_feiyi.png",
        "assets/hero.png",
        "assets/banner.png",
        "assets/home_hero.png",
    ]
)

hero_img_base64 = image_to_base64(hero_image_path) if hero_image_path else ""

if hero_img_base64:
    hero_style = f"""
        background-image: url('data:image/png;base64,{hero_img_base64}');
        background-size: cover;
        background-position: center right;
    """
else:
    hero_style = """
        background:
        radial-gradient(circle at 12% 20%, rgba(18,184,178,.46), transparent 25%),
        radial-gradient(circle at 82% 16%, rgba(255,122,69,.34), transparent 27%),
        radial-gradient(circle at 72% 82%, rgba(47,128,237,.32), transparent 28%),
        linear-gradient(135deg, #07132b 0%, #10284b 54%, #073f46 100%);
    """

st.markdown(
    f"""
    <div class="hero" style="{hero_style}">
        <div class="hero-inner">
            <div class="hero-kicker">🦁 广东非遗体验工作台</div>
            <h1 class="hero-title">粤见非遗</h1>
            <div class="hero-subtitle">
                从一句需求开始，生成可出发、可研学、可发布的广东非遗体验方案。
            </div>
            <div class="hero-chips">
                <span class="hero-chip">路线</span>
                <span class="hero-chip">研学</span>
                <span class="hero-chip">亲子</span>
                <span class="hero-chip">图文 / 短视频</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 工作台
# =========================================================
left, right = st.columns([2.1, 1], gap="large")

with left:
    st.markdown('<div class="workspace">', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="form-title">创建方案</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="form-desc">选择用途，补充城市和时间，然后用一句话描述你的需求。</div>',
            unsafe_allow_html=True,
        )

        scene_choice = st.radio(
            "用途",
            SCENES,
            horizontal=True,
            index=SCENES.index(st.session_state.selected_scene)
            if st.session_state.selected_scene in SCENES
            else 0,
            disabled=st.session_state.pending_generate,
        )

        if scene_choice != st.session_state.last_scene:
            st.session_state.selected_scene = scene_choice
            st.session_state.last_scene = scene_choice
            st.session_state.user_input = scene_example(scene_choice)
            set_toast(f"已切换到：{scene_choice}", scene_icon(scene_choice))
            st.rerun()

        st.markdown(
            f"""
            <div class="scene-note">
                <div class="scene-title">{scene_icon(scene_choice)} 当前用途：{scene_choice}</div>
                <div class="scene-desc">{scene_desc(scene_choice)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)

        with c1:
            city = st.selectbox(
                "城市",
                ["自动判断", "广州", "佛山", "潮州", "汕头", "深圳", "梅州", "江门", "珠海", "东莞"],
                index=0,
                disabled=st.session_state.pending_generate,
            )

        with c2:
            duration = st.selectbox(
                "时间",
                ["自动判断", "半天", "一天", "两天", "周末", "不限"],
                index=0,
                disabled=st.session_state.pending_generate,
            )

        st.caption("试试这些：")
        ex_cols = st.columns(4)
        for col, (label, item) in zip(ex_cols, EXAMPLES.items()):
            with col:
                if st.button(
                    label,
                    key=f"main_example_{label}",
                    use_container_width=True,
                    disabled=st.session_state.pending_generate,
                ):
                    st.session_state.selected_scene = item["scene"]
                    st.session_state.last_scene = item["scene"]
                    st.session_state.user_input = item["text"]
                    set_toast(f"已填入示例：{label}", "✨")
                    st.rerun()

        user_input = st.text_area(
            "一句话需求",
            key="user_input",
            height=145,
            placeholder="例如：我第一次来广州，有一天时间，想体验岭南非遗文化，最好适合拍照和写研学记录。",
            disabled=st.session_state.pending_generate,
        )

        with st.expander("补充设置，可不填"):
            identity = st.selectbox(
                "身份",
                ["自动匹配", "外地游客", "学生研学", "亲子家庭", "本地居民", "内容创作者"],
                index=0,
                disabled=st.session_state.pending_generate,
            )

            interests = st.multiselect(
                "特别想包含",
                ["非遗", "岭南建筑", "粤剧", "醒狮", "广绣", "龙舟", "潮汕工夫茶", "美食", "拍照", "研学", "短视频"],
                default=[],
                disabled=st.session_state.pending_generate,
            )

        final_input = build_final_input(
            scene=scene_choice,
            city=city,
            duration=duration,
            user_input=user_input,
            output_style=output_style,
            identity=identity,
            interests=interests,
        )

        button_text = "正在生成中…" if st.session_state.pending_generate else "✨ 生成方案"

        if st.button(
            button_text,
            type="primary",
            use_container_width=True,
            disabled=st.session_state.pending_generate,
        ):
            if not user_input.strip():
                st.warning("请先输入你的需求。")
            else:
                set_toast("已收到需求，正在生成方案…", "🦁")
                queue_generation(final_input, temperature, "正在生成你的非遗方案…")

        st.caption("写完后点击生成方案。生成后可以继续改短、改成亲子版或生成文案。")

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="workspace">', unsafe_allow_html=True)

    city_show = city if city != "自动判断" else "自动判断"
    duration_show = duration if duration != "自动判断" else "自动判断"

    st.markdown(
        f"""
        <div class="insight-card">
            <div class="card-kicker">本次将生成</div>
            <div class="card-title">{scene_result_title(scene_choice)}</div>
            <div class="card-desc">{scene_desc(scene_choice)}</div>
        </div>
        <div class="settings-card">
            <strong>当前理解</strong><br>
            用途：{scene_choice}<br>
            城市：{city_show}<br>
            时间：{duration_show}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown("#### 下一步可以做")
    if st.session_state.last_answer:
        st.caption("右侧结果区已经提供一键优化按钮。")
        st.markdown("- 压缩成半天\n- 改成亲子版\n- 生成小红书文案\n- 生成短视频脚本")
    else:
        st.caption("生成结果后，这里会变成继续调整区。")
        st.markdown("- 改成半天路线\n- 更适合亲子\n- 生成小红书文案\n- 加上研学记录表")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# 结果区
# =========================================================
st.markdown(
    """
    <div class="result-title-row">
        <h2>方案结果</h2>
        <span>像工作台一样继续修改，而不是一次性结束</span>
    </div>
    """,
    unsafe_allow_html=True,
)

result_left, result_right = st.columns([2.25, .9], gap="large")

with result_left:
    if st.session_state.pending_generate and st.session_state.pending_input:
        final_pending_input = st.session_state.pending_input
        final_pending_temperature = st.session_state.pending_temperature
        action_label = st.session_state.get("pending_action_label", "正在生成你的非遗方案…")

        render_request_summary(final_pending_input)

        st.markdown(
            """
            <div class="answer-shell">
                <div class="answer-header">
                    <span class="answer-icon">🦁</span>
                    <span>粤见非遗为你生成</span>
                </div>
            """,
            unsafe_allow_html=True,
        )

        answer = generate_answer(
            final_pending_input,
            temperature=final_pending_temperature,
            action_label=action_label,
        )

        st.markdown("</div>", unsafe_allow_html=True)

        title = guess_plan_title(final_pending_input, st.session_state.selected_scene)

        st.session_state.messages = [
            {"role": "user", "content": final_pending_input},
            {"role": "assistant", "content": answer},
        ]
        st.session_state.last_answer = answer
        add_recent_plan(title, final_pending_input, answer, st.session_state.selected_scene)
        st.session_state.pending_generate = False
        st.session_state.pending_input = ""
        st.session_state.pending_action_label = "正在生成你的非遗方案…"
        set_toast("方案已生成，可以继续优化或下载方案", "✅")
        st.rerun()

    elif not st.session_state.messages:
        st.info("还没有生成内容。填写需求后点击“生成方案”。")
    else:
        last_user = ""
        last_answer = ""

        if len(st.session_state.messages) >= 2:
            last_user = st.session_state.messages[-2]["content"]
            last_answer = st.session_state.messages[-1]["content"]

        if last_user:
            render_request_summary(last_user)

        st.markdown(
            """
            <div class="answer-shell">
                <div class="answer-header">
                    <span class="answer-icon">🦁</span>
                    <span>粤见非遗为你生成</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(sanitize_model_output(last_answer))
        st.markdown("</div>", unsafe_allow_html=True)

with result_right:
    with st.container(border=True):
        st.markdown("### ⚡ 继续调整")

        if st.session_state.last_answer:
            if st.button("压缩成半天", use_container_width=True, disabled=st.session_state.pending_generate):
                set_toast("正在压缩成半天路线…", "🧭")
                queue_generation(
                    make_followup_prompt("把方案压缩成半天路线，保留最值得去的节点。"),
                    temperature,
                    "正在压缩成半天路线…",
                )

            if st.button("更适合亲子", use_container_width=True, disabled=st.session_state.pending_generate):
                set_toast("正在改成亲子友好版…", "👨‍👩‍👧")
                queue_generation(
                    make_followup_prompt("把方案改得更适合亲子家庭，增加孩子能参与的互动任务，节奏轻松。"),
                    temperature,
                    "正在改成亲子友好版…",
                )

            if st.button("生成小红书文案", use_container_width=True, disabled=st.session_state.pending_generate):
                set_toast("正在生成小红书文案…", "📕")
                queue_generation(
                    make_followup_prompt("基于方案生成一篇小红书文案，包含标题、正文、配图建议和标签。"),
                    temperature,
                    "正在生成小红书文案…",
                )

            if st.button("生成短视频脚本", use_container_width=True, disabled=st.session_state.pending_generate):
                set_toast("正在生成短视频脚本…", "🎬")
                queue_generation(
                    make_followup_prompt("基于方案生成一条 60 秒短视频脚本，包含分镜、旁白、字幕和拍摄建议。"),
                    temperature,
                    "正在生成短视频脚本…",
                )

            if st.button("加研学记录表", use_container_width=True, disabled=st.session_state.pending_generate):
                set_toast("正在补充研学记录表…", "📚")
                queue_generation(
                    make_followup_prompt("为方案补充研学记录表、观察任务和采访问题。"),
                    temperature,
                    "正在补充研学记录表…",
                )
        else:
            st.caption("生成方案后，可以在这里快速改成不同版本。")

        st.divider()

        st.markdown("### 📦 保存方案")
        if st.session_state.last_answer:
            export_text = (
                f"# 粤见非遗生成结果\n\n"
                f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"{sanitize_model_output(st.session_state.last_answer)}"
            )

            st.download_button(
                "下载方案文本",
                data=export_text.encode("utf-8"),
                file_name="yuejian_feiyi_result.md",
                mime="text/markdown",
                use_container_width=True,
                help="保存后可以复制到作业、攻略、公众号或答辩材料中。",
            )
            st.caption("保存后可以复制到作业、攻略、公众号或答辩材料中。")
        else:
            st.caption("生成方案后，可以在这里保存文本。")

        st.divider()

        st.markdown("### 📌 出发前核验")
        st.caption("开放时间、门票、预约、演出和交通可能变化，出发前请以场馆或官方平台信息为准。")


with st.expander("我该怎么用？"):
    st.markdown(
        """
        **第一次使用可以这样做：**

        1. 先选择你想要的用途：路线、研学、亲子体验或内容创作。
        2. 城市和时间不确定时，可以保持“自动判断”。
        3. 在“一句话需求”里写清楚：去哪里、多久、和谁、想体验什么。
        4. 点击“生成方案”，等待页面生成完整结果。
        5. 方案生成后，可以用右侧按钮继续调整，比如改成半天路线、亲子版、小红书文案或短视频脚本。

        **示例：**

        ```text
        我周末带孩子去佛山，想体验醒狮和石湾陶塑，节奏轻松一点，最好有互动任务。
        ```

        **出发前提醒：**  
        开放时间、门票、预约、演出和交通可能变化，出发前请以场馆或官方平台信息为准。
        """
    )
