from api.main import _generation_events
from core.models import RetrievalBundle, TaskRequest


def test_web_generation_uses_compact_retrieval_context(monkeypatch) -> None:
    captured = {}

    def retrieve_stub(query, **kwargs):
        captured.update(kwargs)
        return RetrievalBundle(query=query, chunks=())

    monkeypatch.setattr("api.main.retrieve", retrieve_stub)
    monkeypatch.setattr(
        "api.main.collect_stream_with_safe_fallback",
        lambda *_args, **_kwargs: iter([("## 方案总览\n建议按需体验。", True)]),
    )
    events = list(_generation_events(None, TaskRequest(scene="游客路线", raw_request="广州路线"), None, 0.5))
    assert any("event: complete" in event for event in events)
    assert captured["top_k"] == 3
    assert captured["max_total_chars"] == 2200
