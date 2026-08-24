import pytest

from core.config import DEFAULT_MODEL_NAME, build_user_model_config
from core.models import ModelConfig
import services.llm as llm


def test_default_platform_model_is_qwen37_flash() -> None:
    assert DEFAULT_MODEL_NAME == "qwen3.7-flash"


def test_deepseek_preset_disables_thinking() -> None:
    config = build_user_model_config(
        {
            "user_provider": "DeepSeek",
            "user_api_key": "secret",
            "user_base_url": "https://api.deepseek.com",
            "user_model_name": "deepseek-v4-flash",
        }
    )

    kwargs = llm._completion_request_kwargs(
        config,
        [{"role": "user", "content": "hello"}],
        temperature=0.62,
        max_tokens=1600,
        stream=True,
    )

    assert config.thinking_enabled is False
    assert kwargs["extra_body"] == {"thinking": {"type": "disabled"}}
    assert llm.model_runtime_summary(config) == "deepseek-v4-flash · 非思考模式"


def test_custom_deepseek_compatible_config_is_not_overridden() -> None:
    config = build_user_model_config(
        {
            "user_provider": "自定义 OpenAI-compatible",
            "user_api_key": "secret",
            "user_base_url": "https://api.deepseek.com",
            "user_model_name": "deepseek-v4-flash",
        }
    )

    kwargs = llm._completion_request_kwargs(
        config,
        [{"role": "user", "content": "hello"}],
        temperature=0.62,
        max_tokens=1600,
        stream=True,
    )

    assert config.thinking_enabled is None
    assert "extra_body" not in kwargs
    assert llm.model_runtime_summary(config) == "deepseek-v4-flash"


def test_http_400_stream_failure_does_not_call_non_stream_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = ModelConfig(
        api_key="secret",
        base_url="https://api.example.com/v1",
        model_name="example-model",
        credential_source="user",
    )
    calls = {"complete": 0}

    class BadRequest(Exception):
        status_code = 400

    def broken_stream(*args, **kwargs):
        del args, kwargs
        raise llm._public_error(BadRequest("bad request"), config=config, streaming=True)
        yield "unreachable"

    def complete(*args, **kwargs):
        del args, kwargs
        calls["complete"] += 1
        return "should not run"

    monkeypatch.setattr(llm, "stream_chat", broken_stream)
    monkeypatch.setattr(llm, "complete_chat", complete)

    with pytest.raises(llm.ModelGatewayError, match="请求参数"):
        list(
            llm.collect_stream_with_safe_fallback(
                config,
                [{"role": "user", "content": "hello"}],
                temperature=0.62,
            )
        )

    assert calls["complete"] == 0


def test_empty_stream_can_fallback_once(monkeypatch: pytest.MonkeyPatch) -> None:
    config = ModelConfig(
        api_key="secret",
        base_url="https://api.example.com/v1",
        model_name="example-model",
        credential_source="user",
    )
    calls = {"complete": 0}

    def empty_stream(*args, **kwargs):
        del args, kwargs
        if False:
            yield ""

    def complete(*args, **kwargs):
        del args, kwargs
        calls["complete"] += 1
        return "fallback answer"

    monkeypatch.setattr(llm, "stream_chat", empty_stream)
    monkeypatch.setattr(llm, "complete_chat", complete)

    result = list(
        llm.collect_stream_with_safe_fallback(
            config,
            [{"role": "user", "content": "hello"}],
            temperature=0.62,
        )
    )

    assert result == [("fallback answer", True)]
    assert calls["complete"] == 1
