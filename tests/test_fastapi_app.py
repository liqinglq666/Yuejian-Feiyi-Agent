from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from api.main import _generation_events, app
from core.models import TaskRequest

client = TestClient(app)


def test_status_contains_five_existing_scenes() -> None:
    response = client.get("/v1/status")
    assert response.status_code == 200
    assert len(response.json()["scenes"]) == 5
    assert response.headers["cache-control"] == "no-store"


def test_invalid_scene_rejected() -> None:
    response = client.post("/v1/generate", json={
        "request": {"scene": "fake", "raw_request": "路线"},
    })
    assert response.status_code == 422


def test_empty_request_rejected() -> None:
    response = client.post("/v1/generate", json={
        "request": {"scene": "游客路线", "raw_request": ""},
    })
    assert response.status_code == 422


def test_export_works_without_ai_credentials() -> None:
    response = client.post("/v1/export", json={
        "request": {"scene": "游客路线", "raw_request": "广州一天非遗"},
        "answer": "## 路线\n去看粤剧。",
        "format": "md",
    })
    assert response.status_code == 200
    assert "广州一天非遗" in response.text
    assert "attachment" in response.headers["content-disposition"]


def test_stages_stream_and_sanitize(monkeypatch: pytest.MonkeyPatch) -> None:
    from core.models import RetrievalBundle

    monkeypatch.setattr("api.main.retrieve", lambda *a, **kw: RetrievalBundle(query="test", chunks=()))
    monkeypatch.setattr(
        "api.main.collect_stream_with_safe_fallback",
        lambda *a, **kw: iter([("## 方案总览", False), ("## 方案总览\n推荐体验粤剧。", True)]),
    )
    events = list(_generation_events(None, TaskRequest(scene="游客路线", raw_request="广州路线"), None, 0.62))
    assert any("event: snapshot" in event for event in events)
    done = next(item for item in events if "event: complete" in item)
    payload = json.loads(done.split("data: ", 1)[1].strip())
    assert "推荐体验粤剧" in payload["answer"]


def test_user_api_secret_not_returned_in_status() -> None:
    response = client.get("/v1/status")
    assert "api_key" not in response.text

def test_stream_reports_latency_and_keeps_initial_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    from core.models import RetrievalBundle
    monkeypatch.setattr("api.main.retrieve",lambda *a,**kw:RetrievalBundle(query="test",chunks=()))
    monkeypatch.setattr("api.main.collect_stream_with_safe_fallback",lambda *a,**kw:iter([
        ("## 方案总览",False),("## 方案总览\\n资料",False),("## 方案总览\\n资料\\n其他",True)
    ]))
    events=list(_generation_events(None,TaskRequest(scene="游客路线",raw_request="广州"),None,.62))
    assert any("event: snapshot" in e for e in events)
    final=json.loads(next(e for e in events if "event: complete" in e).split("data: ",1)[1])
    assert final["metrics"]["total_ms"]>=0
    assert "quality" in final and "needs_fact_verification" in final["quality"]


def test_export_has_separate_rate_control(monkeypatch: pytest.MonkeyPatch) -> None:
    from api import main as api_module
    monkeypatch.setattr(api_module,"EXPORT_RATE_LIMIT",1)
    api_module._EXPORT_WINDOW.clear()
    payload={"request":{"scene":"游客路线","raw_request":"广州一天"},"answer":"## 方案总览\\n文化行程","format":"txt"}
    assert client.post("/v1/export",json=payload).status_code==200
    assert client.post("/v1/export",json=payload).status_code==429
    api_module._EXPORT_WINDOW.clear()


def test_request_rate_limit_distinguishes_vercel_visitors(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi import HTTPException, Request
    from api import main as api_module

    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setattr(api_module, "RATE_LIMIT", 1)
    api_module._window.clear()

    def visitor(address: str) -> Request:
        return Request({
            "type": "http",
            "client": ("127.0.0.1", 1234),
            "method": "GET",
            "path": "/v1/generate",
            "headers": [(b"x-vercel-forwarded-for", address.encode("ascii"))],
        })

    api_module._rate_limit(visitor("8.8.8.8"))
    with pytest.raises(HTTPException) as err:
        api_module._rate_limit(visitor("8.8.8.8"))
    assert err.value.status_code == 429
    api_module._rate_limit(visitor("1.1.1.1"))
    api_module._window.clear()
