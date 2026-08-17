from __future__ import annotations

from dataclasses import dataclass

from core.models import ModelConfig


@dataclass(frozen=True)
class ProviderPreset:
    name: str
    base_url: str
    default_model: str
    model_examples: tuple[str, ...]


PROVIDER_PRESETS: dict[str, ProviderPreset] = {
    "阿里云百炼 Qwen": ProviderPreset(
        name="阿里云百炼 Qwen",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        default_model="qwen-turbo",
        model_examples=("qwen-turbo", "qwen-plus", "qwen-max"),
    ),
    "DeepSeek": ProviderPreset(
        name="DeepSeek",
        base_url="https://api.deepseek.com",
        default_model="deepseek-chat",
        model_examples=("deepseek-chat",),
    ),
    "自定义 OpenAI 兼容接口": ProviderPreset(
        name="自定义 OpenAI 兼容接口",
        base_url="",
        default_model="",
        model_examples=(),
    ),
}


def build_model_config(session_state: object) -> ModelConfig:
    api_key = str(getattr(session_state, "user_api_key", "")).strip()
    base_url = str(getattr(session_state, "user_base_url", "")).strip()
    model_name = str(getattr(session_state, "user_model_name", "")).strip()

    if not api_key:
        raise ValueError("请先在左侧填写 API Key。")
    if not base_url:
        raise ValueError("请填写 Base URL。")
    if not model_name:
        raise ValueError("请填写模型名称。")

    return ModelConfig(
        api_key=api_key,
        base_url=base_url,
        model_name=model_name,
    )
