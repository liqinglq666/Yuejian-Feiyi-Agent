from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from dotenv import load_dotenv

from core.models import ModelConfig

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL_NAME = "qwen-turbo"

PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "阿里云百炼": {
        "base_url": DEFAULT_BASE_URL,
        "model_name": "qwen-plus",
    },
    "DeepSeek": {
        "base_url": "https://api.deepseek.com",
        "model_name": "deepseek-v4-flash",
    },
    "OpenAI": {
        "base_url": "https://api.openai.com/v1",
        "model_name": "gpt-5",
    },
    "自定义 OpenAI-compatible": {
        "base_url": "",
        "model_name": "",
    },
}

MODEL_MODES = ("auto", "platform", "user")

load_dotenv()


def _env_flag(name: str, *, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def platform_api_enabled() -> bool:
    """Return whether the deployment owner currently offers the shared API."""
    return _env_flag("PLATFORM_API_ENABLED", default=True)


def platform_service_ready() -> bool:
    """Return whether the shared platform API can be selected."""
    return platform_api_enabled() and bool(os.getenv("OPENAI_API_KEY", "").strip())


def user_api_configured(state: Mapping[str, Any] | None) -> bool:
    if state is None:
        return False
    return all(
        str(state.get(key, "")).strip()
        for key in ("user_api_key", "user_base_url", "user_model_name")
    )


def model_service_ready(state: Mapping[str, Any] | None = None) -> bool:
    """Return whether at least one explicitly usable model route exists."""
    mode = str((state or {}).get("model_mode", "auto"))
    if mode == "user":
        return user_api_configured(state)
    if mode == "platform":
        return platform_service_ready()
    return platform_service_ready()


def active_model_source(state: Mapping[str, Any] | None = None) -> str:
    mode = str((state or {}).get("model_mode", "auto"))
    if mode == "user":
        return "user"
    if mode == "platform":
        return "platform"
    if platform_service_ready():
        return "platform"
    return "none"


def build_platform_model_config() -> ModelConfig:
    if not platform_api_enabled():
        raise ValueError("平台 AI 服务当前已暂停，请切换到“我的 API”继续使用。")

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = (os.getenv("OPENAI_BASE_URL", "") or DEFAULT_BASE_URL).strip()
    model_name = (os.getenv("MODEL_NAME", "") or DEFAULT_MODEL_NAME).strip()

    if not api_key:
        raise ValueError("平台 AI 服务当前未配置，请切换到“我的 API”继续使用。")
    if not base_url:
        raise ValueError("平台 AI 服务地址未配置，请联系管理员。")
    if not model_name:
        raise ValueError("平台 AI 模型未配置，请联系管理员。")

    return ModelConfig(
        api_key=api_key,
        base_url=base_url,
        model_name=model_name,
        credential_source="platform",
    )


def build_user_model_config(state: Mapping[str, Any] | None) -> ModelConfig:
    if state is None:
        raise ValueError("请先配置个人 API。")

    api_key = str(state.get("user_api_key", "")).strip()
    base_url = str(state.get("user_base_url", "")).strip()
    model_name = str(state.get("user_model_name", "")).strip()

    if not api_key:
        raise ValueError("请先填写个人 API Key。")
    if not base_url:
        raise ValueError("请先填写个人 API Base URL。")
    if not model_name:
        raise ValueError("请先填写个人模型名称。")

    return ModelConfig(
        api_key=api_key,
        base_url=base_url,
        model_name=model_name,
        credential_source="user",
    )


def build_model_config(state: Mapping[str, Any] | None = None) -> ModelConfig:
    """Resolve the active model route without silently spending a user's quota.

    Auto mode uses the platform API only. If the platform route is unavailable,
    users who configured BYOK must explicitly select "我的 API" before their
    credentials can be used.
    """
    mode = str((state or {}).get("model_mode", "auto"))
    if mode not in MODEL_MODES:
        mode = "auto"

    if mode == "platform":
        return build_platform_model_config()
    if mode == "user":
        return build_user_model_config(state)

    if platform_service_ready():
        return build_platform_model_config()
    if user_api_configured(state):
        raise ValueError(
            "平台 AI 服务当前不可用。为避免未经确认消耗你的个人额度，"
            "请在“AI 模型服务”中切换到“我的 API”后继续。"
        )
    raise ValueError("平台 AI 服务当前不可用。你可以在“AI 模型服务”中配置自己的 API。")
