from __future__ import annotations

import os
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request

from api.main import app
from core.quotas import _visitor_fingerprint, reserve_platform_request, shared_quota_ready


def _request(headers: list[tuple[bytes,bytes]] | None = None) -> Request:
    return Request({"type":"http","method":"POST","path":"/v1/generate","headers":headers or [],"client":("1.2.3.4",1000)})


def test_without_shared_redis_platform_is_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "only-for-test")
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)
    assert not shared_quota_ready()
    assert TestClient(app).get("/v1/status").json()["platform_ready"] is False
    with pytest.raises(HTTPException) as exc:
        reserve_platform_request(_request())
    assert exc.value.status_code == 503


def test_real_vercel_header_used_only_on_vercel(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request([(b"x-vercel-forwarded-for",b"8.8.8.8"),(b"x-forwarded-for",b"9.9.9.9")])
    monkeypatch.setenv("VERCEL", "1")
    x = _visitor_fingerprint(request)
    monkeypatch.setenv("VERCEL", "0")
    y = _visitor_fingerprint(request)
    assert x != y
    assert len(x) == 24


def test_atomic_script_reserves_then_rejects(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://demo.upstash.io")
    monkeypatch.setenv("UPSTASH_REDIS_REST_TOKEN", "test-token")
    import httpx
    seen: list[list] = []
    state = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        import json
        args = json.loads(request.content)
        seen.append(args)
        state["count"] += 1
        return httpx.Response(200, json={"result": 0 if state["count"] == 1 else 2})

    transport = httpx.MockTransport(handler)
    class FakeClient:
        def __init__(self, **kwargs): pass
        def __enter__(self): return httpx.Client(transport=transport)
        def __exit__(self, *args): pass

    monkeypatch.setattr("core.quotas.httpx.Client", FakeClient)
    reserve_platform_request(_request())
    with pytest.raises(HTTPException) as exc:
        reserve_platform_request(_request())
    assert exc.value.status_code == 429
    assert len(seen) == 2 and seen[0][0] == "EVAL"
    assert "INCR" in seen[0][1]
    assert len(seen[0]) == 15


def test_quota_fails_closed_on_storage_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://demo.upstash.io")
    monkeypatch.setenv("UPSTASH_REDIS_REST_TOKEN", "test-token")
    import httpx
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error":"unavailable"})
    real_client = httpx.Client
    monkeypatch.setattr("core.quotas.httpx.Client", lambda **kw: real_client(transport=httpx.MockTransport(handler)))
    with pytest.raises(HTTPException) as exc:
        reserve_platform_request(_request())
    assert exc.value.status_code == 503
