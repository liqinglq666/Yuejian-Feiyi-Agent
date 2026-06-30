"""
agent.py
粤见非遗智能体核心逻辑。

职责边界：
1. app.py 负责页面、交互、场景化输入。
2. prompts.py 负责任务级 Prompt 模板。
3. rag.py 负责本地知识库检索。
4. agent.py 只负责配置读取、Prompt 组装和模型调用。
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
    WEB_OUTPUT_RULES,
)


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


def get_client() -> OpenAI:
    """
    创建 OpenAI 兼容客户端。
    """
    api_key = get_config_value("OPENAI_API_KEY")
    base_url = get_config_value(
        "OPENAI_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    if not api_key:
        raise RuntimeError(
            "未检测到模型 API Key。请在本地 .env 或 Streamlit Secrets 中配置 OPENAI_API_KEY。"
        )

    return OpenAI(
        api_key=api_key,
        base_url=base_url,
    )


def get_model_name() -> str:
    """
    获取模型名称。
    默认使用 qwen-turbo，优先保证网页体验速度。
    需要更高质量时，可在 .env 中改成 qwen-plus。
    """
    return get_config_value("MODEL_NAME", "qwen-turbo")


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
        "课堂", "学生", "作业", "调研", "记录表",
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

【通用生成要求】
1. 回答必须围绕广东、岭南文化、广东非遗或城市文化体验展开。
2. 不要泛泛而谈，要尽量给出可执行、可落地的方案。
3. 涉及开放时间、票价、活动、交通、预约等实时信息时，必须提醒用户以官方平台为准。
4. 如果资料不足，不要编造具体事实，可以给出“建议核验”的提示。
5. 语言要清晰、实用、有广东文化味道，但不要过度堆砌辞藻。

{WEB_OUTPUT_RULES}
""".strip()


def build_messages(user_input: str) -> list[dict[str, str]]:
    """
    统一构造 messages，普通输出和流式输出共用。
    """
    task_type = detect_task_type(user_input)

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


def ask_agent(
    user_input: str,
    temperature: float = 0.62,
    max_tokens: int = 1200,
) -> str:
    """
    普通生成入口。
    """
    if not user_input or not user_input.strip():
        return "请先输入你的需求，例如：我第一次来广州，有一天时间，想体验岭南非遗文化。"

    client = get_client()
    model_name = get_model_name()
    messages = build_messages(user_input)

    try:
        response = client.chat.completions.create(
            model=model_name,
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


def ask_agent_stream(
    user_input: str,
    temperature: float = 0.62,
    max_tokens: int = 1200,
) -> Generator[str, None, None]:
    """
    流式生成入口。
    """
    if not user_input or not user_input.strip():
        yield "请先输入你的需求，例如：我第一次来广州，有一天时间，想体验岭南非遗文化。"
        return

    client = get_client()
    model_name = get_model_name()
    messages = build_messages(user_input)

    try:
        stream = client.chat.completions.create(
            model=model_name,
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


if __name__ == "__main__":
    demo = "我第一次来广州，有一天时间，想体验岭南非遗文化，最好适合拍照和写研学记录。"
    for part in ask_agent_stream(demo):
        print(part, end="", flush=True)
