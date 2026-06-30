"""
agent.py
粤见非遗智能体核心逻辑。

本版优化：
1. 默认 max_tokens 从 1800 降到 1200，减少等待时间。
2. RAG 检索从 top_k=6 降到 top_k=4，并限制 max_total_chars=2800。
3. 新增 ask_agent_stream，用于 Streamlit 流式输出。
"""

from __future__ import annotations

import os
from typing import Generator

from dotenv import load_dotenv
from openai import OpenAI

try:
    import streamlit as st
except Exception:
    st = None

from rag import retrieve_context
from prompts import (
    SYSTEM_PROMPT,
    TASK_PROMPTS,
    FALLBACK_PROMPT,
)


# =========================================================
# 环境变量读取
# =========================================================
load_dotenv()


def get_config_value(key: str, default: str = "") -> str:
    """
    优先从本地环境变量读取；
    部署到 Streamlit Cloud 后，从 st.secrets 读取。
    """
    value = os.getenv(key)
    if value:
        return str(value).strip()

    if st is not None:
        try:
            value = st.secrets.get(key, default)
            if value:
                return str(value).strip()
        except Exception:
            pass

    return default


def get_client(
    api_key: str | None = None,
    base_url: str | None = None,
) -> OpenAI:
    """
    创建 OpenAI 兼容客户端。

    本版本为“用户侧模型接入版”：
    - 使用用户在页面中填写的 API Key
    - 不读取公开部署环境中的默认模型 Key
    - 生成请求通过用户侧模型服务完成
    """
    final_api_key = (api_key or "").strip()
    final_base_url = (base_url or "").strip() or "https://dashscope.aliyuncs.com/compatible-mode/v1"

    if not final_api_key:
        raise RuntimeError("请先在左侧「模型接入」中填写 API Key 后再生成。")

    return OpenAI(
        api_key=final_api_key,
        base_url=final_base_url,
    )


def get_model_name(model_name: str | None = None) -> str:
    """
    获取模型名称。

    本版本不读取 .env / Secrets 中的 MODEL_NAME。
    如果页面未传入模型名称，则默认使用 qwen-turbo。
    """
    return (model_name or "").strip() or "qwen-turbo"


# =========================================================
# 任务类型识别
# =========================================================
def detect_task_type(user_input: str) -> str:
    """
    根据用户输入识别任务类型。
    返回：
    - qa：非遗问答
    - route：路线规划
    - study：研学任务
    - social：图文文案
    - video：短视频脚本
    """
    text = user_input.lower()

    video_keywords = [
        "短视频", "分镜", "脚本", "旁白", "镜头", "抖音", "快手", "视频", "口播",
    ]

    social_keywords = [
        "小红书", "朋友圈", "推文", "文案", "标题", "标签", "种草", "发布", "图文", "宣传",
    ]

    study_keywords = [
        "研学", "任务卡", "学习目标", "观察任务", "采访问题", "报告", "提纲",
        "课堂", "学生", "作业", "调研",
    ]

    route_keywords = [
        "路线", "规划", "怎么走", "一日游", "半日", "两天", "周末",
        "citywalk", "打卡", "行程", "景点", "游玩", "旅行", "旅游", "亲子",
    ]

    qa_keywords = [
        "是什么", "为什么", "介绍", "解释", "讲解", "区别", "代表", "文化", "历史", "背景", "价值",
    ]

    if any(keyword in text for keyword in video_keywords):
        return "video"

    if any(keyword in text for keyword in social_keywords):
        return "social"

    if any(keyword in text for keyword in study_keywords):
        return "study"

    if any(keyword in text for keyword in route_keywords):
        return "route"

    if any(keyword in text for keyword in qa_keywords):
        return "qa"

    return "qa"


# =========================================================
# Prompt 构造
# =========================================================
def build_user_prompt(
    user_input: str,
    task_type: str,
    context: str,
) -> str:
    """
    构造最终发送给模型的用户 Prompt。
    """
    task_prompt = TASK_PROMPTS.get(task_type, FALLBACK_PROMPT)

    return f"""
你需要根据用户需求，结合【广东非遗知识库】生成高质量答案。

【用户需求】
{user_input}

【识别到的任务类型】
{task_type}

【任务输出要求】
{task_prompt}

【广东非遗知识库检索结果】
{context if context.strip() else "未检索到高度相关资料。请基于通用广东非遗知识谨慎回答，并提醒用户以官方信息为准。"}

【生成要求】
1. 回答必须围绕广东、岭南文化、广东非遗或城市文化体验展开。
2. 不要泛泛而谈，要尽量给出可执行、可落地的方案。
3. 涉及开放时间、票价、活动、交通、预约等实时信息时，必须提醒用户以官方平台为准。
4. 如果资料不足，不要编造具体事实，可以给出“建议核验”的提示。
5. 语言要清晰、实用、有广东文化味道，但不要过度堆砌辞藻。
""".strip()


def build_messages(user_input: str) -> list[dict[str, str]]:
    """
    统一构造 messages，普通输出和流式输出共用。
    """
    task_type = detect_task_type(user_input)

    # 提速核心修改：top_k 从 6 改为 4，max_total_chars 从 4200 改为 2800
    context = retrieve_context(
        user_input,
        top_k=4,
        max_total_chars=2800,
    )

    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": build_user_prompt(
                user_input=user_input,
                task_type=task_type,
                context=context,
            ),
        },
    ]


# =========================================================
# 普通非流式输出
# =========================================================
def ask_agent(
    user_input: str,
    temperature: float = 0.62,
    max_tokens: int = 1200,
    api_key: str | None = None,
    base_url: str | None = None,
    model_name: str | None = None,
) -> str:
    """
    普通生成入口。
    max_tokens 已从 1800 降为 1200，用于提速。
    """
    if not user_input or not user_input.strip():
        return "请先输入你的需求，例如：我第一次来广州，有一天时间，想体验岭南非遗文化。"

    client = get_client(api_key=api_key, base_url=base_url)
    final_model_name = get_model_name(model_name)
    messages = build_messages(user_input)

    try:
        response = client.chat.completions.create(
            model=final_model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        answer = response.choices[0].message.content

        if not answer:
            return "模型返回内容为空，请稍后重试，或换一种更具体的提问方式。"

        return answer.strip()

    except Exception as exc:
        raise RuntimeError(
            f"模型调用失败：{exc}\n\n"
            "请检查 API Key、OPENAI_BASE_URL、MODEL_NAME 是否配置正确。"
        )


# =========================================================
# 流式输出
# =========================================================
def ask_agent_stream(
    user_input: str,
    temperature: float = 0.62,
    max_tokens: int = 1200,
    api_key: str | None = None,
    base_url: str | None = None,
    model_name: str | None = None,
) -> Generator[str, None, None]:
    """
    流式生成入口。
    app.py 中会逐块读取这个生成器，实现像 ChatGPT 一样边生成边显示。
    """
    if not user_input or not user_input.strip():
        yield "请先输入你的需求，例如：我第一次来广州，有一天时间，想体验岭南非遗文化。"
        return

    client = get_client(api_key=api_key, base_url=base_url)
    final_model_name = get_model_name(model_name)
    messages = build_messages(user_input)

    try:
        stream = client.chat.completions.create(
            model=final_model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if delta and delta.content:
                yield delta.content

    except Exception as exc:
        raise RuntimeError(
            f"模型流式调用失败：{exc}\n\n"
            "请检查 API Key、OPENAI_BASE_URL、MODEL_NAME 是否配置正确。"
        )


# =========================================================
# 本地测试
# =========================================================
if __name__ == "__main__":
    demo = "我第一次来广州，有一天时间，想体验岭南非遗文化，最好适合拍照和写研学记录。"
    for part in ask_agent_stream(demo):
        print(part, end="", flush=True)
