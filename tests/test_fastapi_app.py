from __future__ import annotations

import json

from fastapi.testclient import TestClient
import pytest

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
