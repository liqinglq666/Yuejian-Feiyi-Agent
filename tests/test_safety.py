from __future__ import annotations

import logging
import socket
from pathlib import Path

import pytest

from core.models import ModelConfig
from services import llm, retrieval


def _user_config() -> ModelConfig:
    return ModelConfig(
        api_key="demo",
        base_url="https://gateway.example/v1",
        model_name="demo-model",
        credential_source="user",
    )


def test_private_model_gateway_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))
        ],
    )

    with pytest.raises(llm.ModelGatewayError, match="内网"):
        llm.build_client(_user_config())


def test_missing_knowledge_base_is_explicit(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    retrieval.clear_cache()

    with pytest.raises(retrieval.KnowledgeBaseError, match="目录不存在"):
        retrieval.retrieve_context("广州粤剧路线", data_dir=missing)

    retrieval.clear_cache()


def test_upstream_error_is_not_exposed_or_logged(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    secret = "token=super-secret internal-host"
    config = _user_config()

    def broken_client(_config: ModelConfig):
        raise RuntimeError(secret)

    monkeypatch.setattr(llm, "build_client", broken_client)

    with caplog.at_level(logging.WARNING, logger=llm.__name__):
        with pytest.raises(llm.ModelGatewayError) as exc_info:
            llm.complete_chat(
                config,
                [{"role": "user", "content": "介绍粤剧"}],
            )

    message = str(exc_info.value)
    assert "super-secret" not in message
    assert "internal-host" not in message
    assert "AI 服务调用失败" in message
    assert "super-secret" not in caplog.text
    assert "internal-host" not in caplog.text
    assert "RuntimeError" in caplog.text
