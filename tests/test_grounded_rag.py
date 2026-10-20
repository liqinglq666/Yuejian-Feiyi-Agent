from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.models import RetrievalBundle, RetrievedChunk, TaskType
from services.quality import inspect_answer
from services.retrieval import KnowledgeBaseError, clear_cache, get_index, retrieve


def test_registry_fields_and_sources():
    records=json.loads((Path(__file__).resolve().parents[1]/"data"/"heritage_records.json").read_text(encoding="utf-8"))
    assert len(records)>=8
    for r in records:
        assert all(r.get(k) for k in ["id","name","cities","category","facts","source_name","source_url","verified_on","experience"])
        assert r["source_url"].startswith("https://www.ihchina.cn/")
        assert r["verified_on"]=="2026-10-20"
    assert len({r["id"] for r in records})==len(records)
def test_verified_source_is_returned():
    clear_cache()
    found=retrieve("广州粤剧文化背景与观演体验",top_k=4)
    assert any("ihchina.cn" in c.source_url for c in found.chunks)
    assert "https://www.ihchina.cn/" in found.source_markdown()
def test_registry_modification_invalidates_cached_index(tmp_path):
    (tmp_path/"note.md").write_text("# 测试\n内容",encoding="utf-8")
    record={"id":"mock","name":"测试项目","cities":["佛山"],"category":"传统技艺","facts":["测试"],"source_name":"官方名录","source_url":"https://www.ihchina.cn/project_details/14263.html","verified_on":"2026-10-20"}
    path=tmp_path/"heritage_records.json"
    path.write_text(json.dumps([record],ensure_ascii=False),encoding="utf-8")
    clear_cache()
    assert any(c.title=="测试项目" for c in get_index(tmp_path).chunks)
    record["name"]="新测试项目"
    path.write_text(json.dumps([record],ensure_ascii=False,indent=2),encoding="utf-8")
    assert any(c.title=="新测试项目" for c in get_index(tmp_path).chunks)
def test_fake_official_source_rejected(tmp_path):
    (tmp_path/"note.md").write_text("# Test\nfoo",encoding="utf-8")
    record={"id":"f","name":"错误","cities":["广州"],"category":"美术","facts":["未知"],"source_name":"假源","source_url":"https://example.com/data","verified_on":"2026-10-20"}
    (tmp_path/"heritage_records.json").write_text(json.dumps([record],ensure_ascii=False),encoding="utf-8")
    clear_cache()
    with pytest.raises(KnowledgeBaseError):
        get_index(tmp_path)
def test_quality_checks_evidence_and_structure():
    chunk=RetrievedChunk(chunk_id="a",title="粤剧",content="项目：粤剧（广府大戏）",source_path="data/heritage_records.json",source_url="https://www.ihchina.cn/project_details/13221/")
    report=inspect_answer("## 一句话认识\n## 文化背景\n## 核心看点\n## 如何体验\n## 核验提醒",TaskType.QA,RetrievalBundle(query="粤剧",chunks=(chunk,)))
    assert report["sections_complete"] and report["official_source_count"]==1
    empty=inspect_answer("## 测试",TaskType.QA,RetrievalBundle(query="x",chunks=()))
    assert empty["needs_fact_verification"] and not empty["sections_complete"]


def test_unrelated_official_source_is_not_marked_evidence():
    from services.quality import directly_supported_topic
    result=RetrievalBundle(
        query="佛山现代科技展览地点",
        chunks=(
            RetrievedChunk(
                chunk_id="official",
                title="粤剧",
                content="项目：粤剧（广府大戏）",
                source_path="data/heritage_records.json",
                source_url="https://www.ihchina.cn/project_details/13221/",
            ),
        ),
    )
    assert not directly_supported_topic(result.chunks[0],result.query)
    assert inspect_answer("## 核验提醒",TaskType.QA,result)["needs_fact_verification"]


def test_sources_markdown_contains_clickable_project_link():
    chunk=RetrievedChunk(
        chunk_id="verified",
        title="陆丰皮影戏",
        content="项目：陆丰皮影戏",
        source_path="data/heritage_records.json",
        source_name="国家级名录",
        source_url="https://www.ihchina.cn/project_details/13399/",
    )
    markdown=RetrievalBundle(query="陆丰皮影戏",chunks=(chunk,)).source_markdown()
    assert "[陆丰皮影戏｜国家级名录](https://www.ihchina.cn/project_details/13399/)" in markdown


def test_planner_injects_no_false_realtime_venues():
    from core.models import TaskRequest
    from services.planner import build_task_plan
    from services.prompt_builder import build_initial_messages
    request=TaskRequest(scene="游客路线",raw_request="安排佛山一日醒狮路线",city="佛山")
    retrieved=RetrievalBundle(query=request.retrieval_query,chunks=())
    plan=build_task_plan(request,retrieved)
    assert "不猜测真实交通时间" in plan
    assert "缺少官方项目记录" in plan
    msgs=build_initial_messages(request,retrieved)
    assert "【内部任务规划】" in msgs[-1]["content"]
