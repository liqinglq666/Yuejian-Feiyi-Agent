from __future__ import annotations

import os

from dotenv import load_dotenv

from core.models import ModelConfig

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL_NAME = "qwen-turbo"

load_dotenv()


def model_service_ready() -> bool:
    """Return whether the server-side model credential is configured."""
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def build_model_config() -> ModelConfig:
    """Build model configuration from server-side environment variables only."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = (os.getenv("OPENAI_BASE_URL", "") or DEFAULT_BASE_URL).strip()
    model_name = (os.getenv("MODEL_NAME", "") or DEFAULT_MODEL_NAME).strip()

    if not api_key:
        raise ValueError("AI 服务暂未配置，请联系管理员。")
    if not base_url:
        raise ValueError("AI 服务地址暂未配置，请联系管理员。")
    if not model_name:
        raise ValueError("AI 模型暂未配置，请联系管理员。")

    return ModelConfig(
        api_key=api_key,
        base_url=base_url,
        model_name=model_name,
    )
