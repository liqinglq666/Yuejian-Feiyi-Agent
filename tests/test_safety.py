from __future__ import annotations

import socket

import pytest

import agent
import rag


def test_private_model_gateway_is_rejected(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))],
    )

    with pytest.raises(RuntimeError, match="内网"):
        agent.get_client(api_key="demo", base_url="https://gateway.example/v1")


def test_missing_knowledge_base_is_explicit(monkeypatch, tmp_path):
    monkeypatch.setattr(rag, "DATA_DIR", tmp_path / "missing")
    rag.clear_cache()

    with pytest.raises(rag.KnowledgeBaseError, match="目录不存在"):
        rag.retrieve_context("广州粤剧路线")

    rag.clear_cache()


def test_upstream_error_is_not_echoed(monkeypatch):
    monkeypatch.setattr(
        agent,
        "get_client",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("token=super-secret internal-host")),
    )

    with pytest.raises(RuntimeError) as exc_info:
        agent.ask_agent("介绍粤剧", api_key="demo")

    message = str(exc_info.value)
    assert "super-secret" not in message
    assert "internal-host" not in message
    assert "请检查 API Key" in message
