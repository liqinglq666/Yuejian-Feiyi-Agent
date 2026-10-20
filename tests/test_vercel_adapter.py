from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app


def test_vercel_services_prefix_routing() -> None:
    response = TestClient(app).get("/api/v1/status")
    assert response.status_code == 200
    assert response.json()["service"] == "ok"
    assert len(response.json()["scenes"]) == 5
