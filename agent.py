from __future__ import annotations

import ipaddress
import logging
import os
import socket
from typing import Generator
from urllib.parse import urlparse

from dotenv import load_dotenv
from openai import OpenAI

try:
    import streamlit as st
except ImportError:
    st = None

from prompts import FALLBACK_PROMPT, SYSTEM_PROMPT, TASK_PROMPTS
from rag import KnowledgeBaseError, retrieve_context

logger = logging.getLogger(__name__)
load_dotenv()


def get_config_value(key: str, default: str = "") -> str:
    value = os.getenv(key)
    if value:
        return str(value).strip()

    if st is not None:
        try:
            value = st.secrets.get(key, default)
        except Exception:
            value = default
        if value:
            return str(value).strip()
    return default


def _blocked_address(value: str) -> bool:
    address = ipaddress.ip_address(value)
    return any(
        (
            address.is_private,
            address.is_loopback,
            address.is_link_local,
            address.is_multicast,
            address.is_reserved,
            address.is_unspecified,
        )
    )


def _validate_base_url(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    parsed = urlparse(value)
    allow_http = os.getenv("ALLOW_INSECURE_LLM_HTTP", "").lower() in {"1", "true", "yes", "on"}

    if parsed.scheme not in {"http", "https"}:
        raise RuntimeError("Base URL 只允许 http/https。")
    if parsed.scheme != "https" and not allow_http:
        raise RuntimeError("Base URL 必须使用 HTTPS。")
    if not parsed.hostname or parsed.username or parsed.password:
        raise RuntimeError("Base URL 格式不合法。")
    if parsed.query or parsed.fragment:
        raise RuntimeError("Base URL 不能带 query 或 fragment。")

    host = parsed.hostname.lower()
    allowed_hosts = {
        item.strip().lower()
        for item in os.getenv("LLM_ALLOWED_HOSTS", "").split(",")
        if item.strip()
    }
    if allowed_hosts and host not in allowed_hosts:
        raise RuntimeError("该模型网关不在服务端允许列表中。")

    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)
        }
    except socket.gaierror as exc:
        raise RuntimeError("模型网关域名解析失败。") from exc

    if not addresses or any(_blocked_address(address) for address in addresses):
        raise RuntimeError("Base URL 不能指向本机、内网或保留地址。")
    return value


def get_client(api_key: str | None = None, base_url: str | None = None) -> OpenAI:
    final_api_key = (api_key or "").strip()
    final_base_url = (base_url or "").strip() or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    if not final_api_key:
        raise RuntimeError("请先在左侧「模型接入」中填写 API Key 后再生成。")

    return OpenAI(
        api_key=final_api_key,
        base_url=_validate_base_url(final_base_url),
        max_retries=1,
        timeout=120.0,
    )


def get_model_name(model_name: str | None = None) -> str:
    return (model_name or "").strip() or "qwen-turbo"


def detect_task_type(user_input: str) -> str:
    text = user_input.lower()
    groups = [
        ("video", ["短视频", "分镜", "脚本", "旁白", "镜头", "抖音", "快手", "视频", "口播"]),
        ("social", ["小红书", "朋友圈", "推文", "文案", "标题", "标签", "种草", "发布", "图文", "宣传"]),
        ("study", ["研学", "任务卡", "学习目标", "观察任务", "采访问题", "报告", "提纲", "课堂", "学生", "作业", "调研"]),
        ("route", ["路线", "规划", "怎么走", "一日游", "半日", "两天", "周末", "citywalk", "打卡", "行程", "景点", "游玩", "旅行", "旅游", "亲子"]),
    ]
    for task_type, keywords in groups:
        if any(keyword in text for keyword in keywords):
            return task_type
    return "qa"


def build_user_prompt(user_input: str, task_type: str, context: str) -> str:
    task_prompt = TASK_PROMPTS.get(task_type, FALLBACK_PROMPT)
    context_text = context.strip() or "未检索到高度相关资料。请谨慎回答，并提醒用户核验实时信息。"
    return f"""
你需要根据用户需求，结合【广东非遗知识库】生成高质量答案。

【用户需求】
{user_input}

【识别到的任务类型】
{task_type}

【任务输出要求】
{task_prompt}

【广东非遗知识库检索结果】
{context_text}

【生成要求】
1. 回答必须围绕广东、岭南文化、广东非遗或城市文化体验展开。
2. 尽量给出可执行方案，不要泛泛而谈。
3. 开放时间、票价、活动、交通和预约等实时信息必须提醒用户以官方平台为准。
4. 资料不足时不要编造具体事实。
5. 语言清晰实用，不要堆砌辞藻。
""".strip()


def build_messages(user_input: str) -> list[dict[str, str]]:
    task_type = detect_task_type(user_input)
    context = retrieve_context(user_input, top_k=4, max_total_chars=2800)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_user_prompt(user_input, task_type, context),
        },
    ]


def _raise_public_error(exc: Exception, *, streaming: bool = False) -> None:
    if isinstance(exc, KnowledgeBaseError):
        logger.error("RAG unavailable: %s", exc)
        raise RuntimeError(f"知识库暂时不可用：{exc}") from exc

    logger.exception("Model request failed", exc_info=exc)
    prefix = "模型流式调用失败" if streaming else "模型调用失败"
    raise RuntimeError(f"{prefix}，请检查 API Key、Base URL、模型名称和网络连接。") from exc


def ask_agent(
    user_input: str,
    temperature: float = 0.62,
    max_tokens: int = 1200,
    api_key: str | None = None,
    base_url: str | None = None,
    model_name: str | None = None,
) -> str:
    if not user_input or not user_input.strip():
        return "请先输入你的需求，例如：我第一次来广州，有一天时间，想体验岭南非遗文化。"

    try:
        client = get_client(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=get_model_name(model_name),
            messages=build_messages(user_input),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        answer = response.choices[0].message.content
        if not answer:
            raise RuntimeError("模型返回内容为空。")
        return answer.strip()
    except Exception as exc:
        _raise_public_error(exc)


def ask_agent_stream(
    user_input: str,
    temperature: float = 0.62,
    max_tokens: int = 1200,
    api_key: str | None = None,
    base_url: str | None = None,
    model_name: str | None = None,
) -> Generator[str, None, None]:
    if not user_input or not user_input.strip():
        yield "请先输入你的需求，例如：我第一次来广州，有一天时间，想体验岭南非遗文化。"
        return

    try:
        client = get_client(api_key=api_key, base_url=base_url)
        stream = client.chat.completions.create(
            model=get_model_name(model_name),
            messages=build_messages(user_input),
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
        _raise_public_error(exc, streaming=True)


if __name__ == "__main__":
    demo = "我第一次来广州，有一天时间，想体验岭南非遗文化。"
    for part in ask_agent_stream(demo):
        print(part, end="", flush=True)
