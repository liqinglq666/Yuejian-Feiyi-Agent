import pytest

from core.config import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL_NAME,
    build_model_config,
    build_platform_model_config,
    build_user_model_config,
    model_service_ready,
    platform_service_ready,
    user_api_configured,
)


def test_build_platform_config_reads_server_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PLATFORM_API_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "server-secret")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("MODEL_NAME", "example-model")

    config = build_platform_model_config()

    assert config.api_key == "server-secret"
    assert config.base_url == "https://api.example.com/v1"
    assert config.model_name == "example-model"
    assert config.credential_source == "platform"
    assert platform_service_ready() is True


def test_platform_config_uses_safe_defaults_for_optional_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PLATFORM_API_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "server-secret")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)

    config = build_platform_model_config()

    assert config.base_url == DEFAULT_BASE_URL
    assert config.model_name == DEFAULT_MODEL_NAME


def test_disabled_platform_is_not_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLATFORM_API_ENABLED", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "server-secret")

    assert platform_service_ready() is False
    with pytest.raises(ValueError, match="已暂停"):
        build_platform_model_config()


def test_explicit_user_mode_builds_byok_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLATFORM_API_ENABLED", "false")
    state = {
        "model_mode": "user",
        "user_api_key": "user-secret",
        "user_base_url": "https://api.example.com/v1",
        "user_model_name": "example-user-model",
    }

    assert user_api_configured(state) is True
    assert model_service_ready(state) is True

    config = build_model_config(state)
    assert config.api_key == "user-secret"
    assert config.base_url == "https://api.example.com/v1"
    assert config.model_name == "example-user-model"
    assert config.credential_source == "user"


def test_user_config_requires_all_fields() -> None:
    state = {
        "user_api_key": "user-secret",
        "user_base_url": "",
        "user_model_name": "example-user-model",
    }

    assert user_api_configured(state) is False
    with pytest.raises(ValueError, match="Base URL"):
        build_user_model_config(state)


def test_auto_mode_never_silently_spends_user_quota(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PLATFORM_API_ENABLED", "false")
    state = {
        "model_mode": "auto",
        "user_api_key": "user-secret",
        "user_base_url": "https://api.example.com/v1",
        "user_model_name": "example-user-model",
    }

    assert model_service_ready(state) is False
    with pytest.raises(ValueError, match="未经确认消耗"):
        build_model_config(state)


def test_auto_mode_uses_platform_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLATFORM_API_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "server-secret")
    state = {
        "model_mode": "auto",
        "user_api_key": "user-secret",
        "user_base_url": "https://api.example.com/v1",
        "user_model_name": "example-user-model",
    }

    config = build_model_config(state)
    assert config.api_key == "server-secret"
    assert config.credential_source == "platform"
