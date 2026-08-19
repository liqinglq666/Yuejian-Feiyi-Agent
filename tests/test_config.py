import pytest

from core.config import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL_NAME,
    build_model_config,
    model_service_ready,
)


def test_build_model_config_reads_server_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "server-secret")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("MODEL_NAME", "example-model")

    config = build_model_config()

    assert config.api_key == "server-secret"
    assert config.base_url == "https://api.example.com/v1"
    assert config.model_name == "example-model"
    assert model_service_ready() is True


def test_build_model_config_uses_safe_defaults_for_optional_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "server-secret")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)

    config = build_model_config()

    assert config.base_url == DEFAULT_BASE_URL
    assert config.model_name == DEFAULT_MODEL_NAME


def test_missing_server_api_key_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert model_service_ready() is False
    with pytest.raises(ValueError, match="AI 服务暂未配置"):
        build_model_config()
