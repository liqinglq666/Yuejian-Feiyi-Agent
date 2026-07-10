from __future__ import annotations

import ipaddress
import logging
import os
import socket
from collections.abc import Generator, Iterable
from typing import Any
from urllib.parse import urlparse

from core.models import ModelConfig

logger = logging.getLogger(__name__)


class ModelGatewayError(RuntimeError):
    """A safe, user-facing model gateway error."""


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


def validate_base_url(base_url: str, *, resolve_dns: bool = True) -> str:
    value = base_url.strip().rstrip("/")
    parsed = urlparse(value)
    allow_http = os.getenv("ALLOW_INSECURE_LLM_HTTP", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    if parsed.scheme not in {"http", "https"}:
        raise ModelGatewayError("Base URL 只允许 http 或 https。")
    if parsed.scheme != "https" and not allow_http:
        raise ModelGatewayError("Base URL 必须使用 HTTPS。")
    if not parsed.hostname or parsed.username or parsed.password:
        raise ModelGatewayError("Base URL 格式不合法。")
    if parsed.query or parsed.fragment:
        raise ModelGatewayError("Base URL 不能包含 query 或 fragment。")

    host = parsed.hostname.lower()
    allowed_hosts = {
        item.strip().lower()
        for item in os.getenv("LLM_ALLOWED_HOSTS", "").split(",")
        if item.strip()
    }
    if allowed_hosts and host not in allowed_hosts:
        raise ModelGatewayError("该模型网关不在服务端允许列表中。")

    if not resolve_dns:
        return value

    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(
                host,
                parsed.port or 443,
                type=socket.SOCK_STREAM,
            )
        }
    except socket.gaierror as exc:
        raise ModelGatewayError("模型网关域名解析失败。") from exc

    if not addresses or any(_blocked_address(address) for address in addresses):
        raise ModelGatewayError("Base URL 不能指向本机、内网或保留地址。")
    return value


def build_client(config: ModelConfig) -> Any:
    if not config.api_key.strip():
        raise ModelGatewayError("请先填写 API Key。")
    if not config.model_name.strip():
        raise ModelGatewayError("请先填写模型名称。")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ModelGatewayError("缺少 openai 依赖，请先安装 requirements.txt。") from exc

    return OpenAI(
        api_key=config.api_key.strip(),
        base_url=validate_base_url(config.base_url),
        timeout=config.timeout_seconds,
        max_retries=config.max_retries,
    )


def stream_chat(
    config: ModelConfig,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.62,
    max_tokens: int = 1600,
) -> Generator[str, None, None]:
    try:
        stream = build_client(config).chat.completions.create(
            model=config.model_name,
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
        raise _public_error(exc, streaming=True) from exc


def complete_chat(
    config: ModelConfig,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.62,
    max_tokens: int = 1600,
) -> str:
    try:
        response = build_client(config).chat.completions.create(
            model=config.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        answer = response.choices[0].message.content
        if not answer:
            raise ModelGatewayError("模型返回内容为空。")
        return answer.strip()
    except Exception as exc:
        if isinstance(exc, ModelGatewayError):
            raise
        raise _public_error(exc, streaming=False) from exc


def test_connection(config: ModelConfig) -> str:
    answer = complete_chat(
        config,
        [
            {"role": "system", "content": "你是接口连通性测试助手。"},
            {"role": "user", "content": "只回复 OK"},
        ],
        temperature=0.0,
        max_tokens=8,
    )
    return answer


def collect_stream_with_safe_fallback(
    config: ModelConfig,
    messages: list[dict[str, str]],
    *,
    temperature: float,
    max_tokens: int = 1600,
) -> Iterable[tuple[str, bool]]:
    """Yield `(text, is_final)` and avoid a second bill after partial output.

    A normal completion fallback is attempted only when streaming fails before the
    gateway returned any text.
    """
    full = ""
    try:
        for part in stream_chat(
            config,
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            full += part
            yield full, False
        if not full.strip():
            raise ModelGatewayError("模型流式返回为空。")
        yield full, True
        return
    except Exception:
        if full.strip():
            raise

    answer = complete_chat(
        config,
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    yield answer, True


def _public_error(exc: Exception, *, streaming: bool) -> ModelGatewayError:
    if isinstance(exc, ModelGatewayError):
        return exc

    logger.exception("Model gateway request failed", exc_info=exc)
    status_code = getattr(exc, "status_code", None)
    message = str(exc).lower()

    if status_code == 401:
        detail = "API Key 无效或已过期。"
    elif status_code == 403:
        detail = "当前账号没有调用该模型的权限。"
    elif status_code == 404:
        detail = "模型名称或 Base URL 不正确。"
    elif status_code == 429:
        detail = "请求过于频繁，或账户额度不足。"
    elif "timeout" in message or "timed out" in message:
        detail = "模型响应超时，请稍后重试。"
    elif "connection" in message or "network" in message:
        detail = "无法连接模型服务，请检查网络和 Base URL。"
    else:
        detail = "模型服务调用失败，请检查配置后重试。"

    prefix = "流式生成失败" if streaming else "模型调用失败"
    return ModelGatewayError(f"{prefix}：{detail}")
