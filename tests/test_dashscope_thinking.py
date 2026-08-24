import pytest

from core.models import ModelConfig
from services.llm import (
    _completion_request_kwargs,
    model_runtime_summary,
    platform_thinking_enabled,
)


def _config(*, source: str = "platform", model: str = "qwen3.7-flash") -> ModelConfig:
    return ModelConfig(
        api_key="test-key",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model_name=model,
        credential_source=source,
    )


def test_platform_dashscope_thinking_is_disabled_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LLM_ENABLE_THINKING", raising=False)
    config = _config()

    kwargs = _completion_request_kwargs(
        config,
        [{"role": "user", "content": "hello"}],
        temperature=0.62,
        max_tokens=1600,
        stream=True,
    )

    assert platform_thinking_enabled(config) is False
    assert kwargs["extra_body"] == {"enable_thinking": False}
    assert model_runtime_summary(config) == "qwen3.7-flash · 非思考模式"


def test_platform_dashscope_thinking_can_be_enabled_explicitly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_ENABLE_THINKING", "true")
    config = _config(model="qwen3.7-flash")

    kwargs = _completion_request_kwargs(
        config,
        [{"role": "user", "content": "hello"}],
        temperature=0.62,
        max_tokens=1600,
        stream=False,
    )

    assert platform_thinking_enabled(config) is True
    assert kwargs["extra_body"] == {"enable_thinking": True}
    assert model_runtime_summary(config) == "qwen3.7-flash · 思考模式"


def test_byok_dashscope_settings_are_not_overridden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LLM_ENABLE_THINKING", raising=False)
    config = _config(source="user")

    kwargs = _completion_request_kwargs(
        config,
        [{"role": "user", "content": "hello"}],
        temperature=0.62,
        max_tokens=1600,
        stream=True,
    )

    assert "extra_body" not in kwargs
    assert model_runtime_summary(config) == "qwen3.7-flash"


def test_non_dashscope_platform_model_is_not_modified() -> None:
    config = ModelConfig(
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        model_name="gpt-5",
        credential_source="platform",
    )

    kwargs = _completion_request_kwargs(
        config,
        [{"role": "user", "content": "hello"}],
        temperature=0.62,
        max_tokens=1600,
        stream=False,
    )

    assert "extra_body" not in kwargs
    assert model_runtime_summary(config) == "gpt-5"
