from __future__ import annotations

import ipaddress
import logging
import os
import socket
from collections.abc import Generator, Iterable
from functools import lru_cache
from time import monotonic
from typing import Any
from urllib.parse import urlparse

from core.models import ModelConfig

logger = logging.getLogger(__name__)

_REASONING_MODEL_PREFIXES = ("gpt-5", "o1", "o3", "o4")
_DASHSCOPE_THINKING_MODEL_PREFIXES = (
    "qwen-turbo",
    "qwen-plus",
    "qwen-flash",
    "qwen3",
    "deepseek-v4",
)
_DEEPSEEK_THINKING_MODEL_PREFIXES = ("deepseek-v4",)
_DNS_CACHE_TTL_SECONDS = 60.0


class ModelGatewayError(RuntimeError):
    """A safe, user-facing model gateway error."""

    def __init__(self, message: str, *, allow_fallback: bool = False) -> None:
        super().__init__(message)
        self.allow_fallback = allow_fallback


def _env_flag(name: str, *, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


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


def _resolve_public_addresses(host: str, port: int) -> tuple[str, ...]:
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(
                host,
                port,
                type=socket.SOCK_STREAM,
            )
        }
    except socket.gaierror as exc:
        raise ModelGatewayError("模型服务域名解析失败。") from exc

    if not addresses or any(_blocked_address(address) for address in addresses):
        raise ModelGatewayError("模型服务地址不能指向本机、内网或保留地址。")
    return tuple(sorted(addresses))


@lru_cache(maxsize=64)
def _resolve_public_addresses_cached(
    host: str,
    port: int,
    time_bucket: int,
) -> tuple[str, ...]:
    del time_bucket
    return _resolve_public_addresses(host, port)


def validate_base_url(
    base_url: str,
    *,
    resolve_dns: bool = True,
    enforce_server_allowlist: bool = True,
    cache_dns: bool = False,
) -> str:
    value = base_url.strip().rstrip("/")
    parsed = urlparse(value)
    allow_http = os.getenv("ALLOW_INSECURE_LLM_HTTP", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    if parsed.scheme not in {"http", "https"}:
        raise ModelGatewayError("模型服务地址只允许 http 或 https。")
    if parsed.scheme != "https" and not allow_http:
        raise ModelGatewayError("模型服务地址必须使用 HTTPS。")
    if not parsed.hostname or parsed.username or parsed.password:
        raise ModelGatewayError("模型服务地址格式不合法。")
    if parsed.query or parsed.fragment:
        raise ModelGatewayError("模型服务地址不能包含 query 或 fragment。")

    host = parsed.hostname.lower()
    if enforce_server_allowlist:
        allowed_hosts = {
            item.strip().lower()
            for item in os.getenv("LLM_ALLOWED_HOSTS", "").split(",")
            if item.strip()
        }
        if allowed_hosts and host not in allowed_hosts:
            raise ModelGatewayError("当前模型服务地址不在服务端允许列表中。")

    if not resolve_dns:
        return value

    port = parsed.port or 443
    if cache_dns:
        time_bucket = int(monotonic() // _DNS_CACHE_TTL_SECONDS)
        _resolve_public_addresses_cached(host, port, time_bucket)
    else:
        _resolve_public_addresses(host, port)
    return value


def build_client(config: ModelConfig) -> Any:
    is_user = config.credential_source == "user"
    if not config.api_key.strip():
        detail = "个人 API Key 为空，请重新配置。" if is_user else "平台 AI 服务暂未配置。"
        raise ModelGatewayError(detail)
    if not config.model_name.strip():
        detail = "个人模型名称为空，请重新配置。" if is_user else "平台 AI 模型暂未配置。"
        raise ModelGatewayError(detail)

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ModelGatewayError("AI 服务依赖缺失，请联系管理员。") from exc

    return OpenAI(
        api_key=config.api_key.strip(),
        base_url=validate_base_url(
            config.base_url,
            enforce_server_allowlist=not is_user,
            cache_dns=not is_user,
        ),
        timeout=config.timeout_seconds,
        max_retries=config.max_retries,
    )


def _uses_reasoning_model_parameters(model_name: str) -> bool:
    normalized = model_name.strip().lower()
    return normalized.startswith(_REASONING_MODEL_PREFIXES)


def _is_dashscope_host(base_url: str) -> bool:
    host = (urlparse(base_url.strip()).hostname or "").lower()
    return host == "dashscope.aliyuncs.com" or host.endswith(".maas.aliyuncs.com")


def _is_deepseek_host(base_url: str) -> bool:
    host = (urlparse(base_url.strip()).hostname or "").lower()
    return host == "api.deepseek.com"


def _supports_platform_thinking_control(config: ModelConfig) -> bool:
    if config.credential_source != "platform" or not _is_dashscope_host(config.base_url):
        return False
    normalized = config.model_name.strip().lower()
    return normalized.startswith(_DASHSCOPE_THINKING_MODEL_PREFIXES)


def _supports_explicit_thinking_preference(config: ModelConfig) -> bool:
    if config.thinking_enabled is None or not _is_deepseek_host(config.base_url):
        return False
    normalized = config.model_name.strip().lower()
    return normalized.startswith(_DEEPSEEK_THINKING_MODEL_PREFIXES)


def platform_thinking_enabled(config: ModelConfig) -> bool:
    """Return the effective thinking mode for supported shared DashScope models."""
    return _supports_platform_thinking_control(config) and _env_flag(
        "LLM_ENABLE_THINKING",
        default=False,
    )


def model_runtime_summary(config: ModelConfig) -> str:
    """Short runtime label safe to show in the generation progress UI."""
    if _supports_platform_thinking_control(config):
        mode = "思考模式" if platform_thinking_enabled(config) else "非思考模式"
        return f"{config.model_name} · {mode}"
    if _supports_explicit_thinking_preference(config):
        mode = "思考模式" if config.thinking_enabled else "非思考模式"
        return f"{config.model_name} · {mode}"
    return config.model_name


def _completion_request_kwargs(
    config: ModelConfig,
    messages: list[dict[str, str]],
    *,
    temperature: float,
    max_tokens: int,
    stream: bool,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": config.model_name,
        "messages": messages,
        "stream": stream,
    }
    if _uses_reasoning_model_parameters(config.model_name):
        kwargs["max_completion_tokens"] = max_tokens
    else:
        kwargs["temperature"] = temperature
        kwargs["max_tokens"] = max_tokens

    extra_body: dict[str, Any] = {}
    if _supports_platform_thinking_control(config):
        extra_body["enable_thinking"] = platform_thinking_enabled(config)
    if _supports_explicit_thinking_preference(config):
        extra_body["thinking"] = {
            "type": "enabled" if config.thinking_enabled else "disabled"
        }
    if extra_body:
        kwargs["extra_body"] = extra_body
    return kwargs


def stream_chat(
    config: ModelConfig,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.62,
    max_tokens: int = 1600,
) -> Generator[str, None, None]:
    try:
        stream = build_client(config).chat.completions.create(
            **_completion_request_kwargs(
                config,
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content
    except Exception as exc:
        raise _public_error(exc, config=config, streaming=True) from exc


def complete_chat(
    config: ModelConfig,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.62,
    max_tokens: int = 1600,
) -> str:
    try:
        response = build_client(config).chat.completions.create(
            **_completion_request_kwargs(
                config,
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )
        )
        answer = response.choices[0].message.content
        if not answer:
            raise ModelGatewayError("模型返回内容为空。")
        return answer.strip()
    except Exception as exc:
        if isinstance(exc, ModelGatewayError):
            raise
        raise _public_error(exc, config=config, streaming=False) from exc


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
    """Yield `(text, is_final)` and avoid duplicate calls for hard failures.

    A normal completion fallback is attempted only when streaming fails before any
    text and the gateway classified the failure as safe to retry non-streaming.
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
            raise ModelGatewayError("模型流式返回为空。", allow_fallback=True)
        yield full, True
        return
    except ModelGatewayError as exc:
        if full.strip() or not exc.allow_fallback:
            raise
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


def _public_error(
    exc: Exception,
    *,
    config: ModelConfig,
    streaming: bool,
) -> ModelGatewayError:
    if isinstance(exc, ModelGatewayError):
        return exc

    logger.exception("Model gateway request failed", exc_info=exc)
    status_code = getattr(exc, "status_code", None)
    message = str(exc).lower()
    is_user = config.credential_source == "user"
    is_timeout = "timeout" in message or "timed out" in message

    if status_code == 400:
        detail = (
            "个人模型不接受当前请求参数，请检查模型名称或更换兼容模型。"
            if is_user
            else "平台模型不接受当前请求参数，请联系管理员检查模型配置。"
        )
    elif status_code == 401:
        detail = (
            "个人 API Key 无效，或与当前 Base URL 不匹配。"
            if is_user
            else "平台模型凭据无效，请联系管理员。"
        )
    elif status_code == 403:
        detail = (
            "个人 API 当前没有调用该模型的权限。"
            if is_user
            else "平台当前没有调用该模型的权限。"
        )
    elif status_code == 404:
        detail = (
            "个人模型名称或 Base URL 配置错误。"
            if is_user
            else "平台模型名称或接口地址配置错误。"
        )
    elif status_code == 429:
        detail = (
            "个人 API 当前请求过多或额度不足，请检查服务商额度。"
            if is_user
            else "平台 AI 服务当前请求过多或额度不足，请稍后重试。"
        )
    elif is_timeout:
        detail = "AI 服务响应超时，请稍后重试。"
    elif "connection" in message or "network" in message:
        detail = "暂时无法连接 AI 服务，请稍后重试。"
    else:
        detail = "AI 服务调用失败，请稍后重试。"

    # HTTP errors and timeouts are expected to fail the same way when retried
    # non-streaming. Only transport/stream failures without an HTTP status may
    # fall back once before any text has been returned.
    allow_fallback = streaming and status_code is None and not is_timeout
    prefix = "流式生成失败" if streaming else "模型调用失败"
    return ModelGatewayError(
        f"{prefix}：{detail}",
        allow_fallback=allow_fallback,
    )
