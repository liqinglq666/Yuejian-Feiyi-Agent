"""V3: protect the specialized workflows without spending model tokens."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from api.main import GenerateInput, _prepare_generation
from core.models import RetrievalBundle, RetrievedChunk, TaskRequest, TaskType
from core.revisions import plan_custom_revision, plan_quick_revision
from services.planner import build_task_plan
from services.prompt_builder import build_initial_messages, build_revision_messages
from services.quality import inspect_answer
from services.scenarios import (
    build_scene_guidance,
    diagnostic_findings,
    request_advisories,
    resolve_policy,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("scene", "task_type", "policy_id"),
    [
        ("游客路线", TaskType.ROUTE, "visitor_route"),
        ("学生研学", TaskType.STUDY, "study"),
        ("亲子体验", TaskType.ROUTE, "family"),
        ("内容创作", TaskType.SOCIAL, "social"),
        ("内容创作", TaskType.VIDEO, "video"),
        ("非遗问答", TaskType.QA, "qa"),
    ],
)
def test_scenario_strategy_routing(scene, task_type, policy_id):
    request = TaskRequest(scene=scene, raw_request="粤剧的文化介绍", task_type=task_type)
    assert resolve_policy(request).key == policy_id
    assert policy_id in {"visitor_route", "study", "family", "social", "video", "qa"}


def test_family_and_visitor_route_use_different_guidance_but_same_headings():
    visitor = TaskRequest(
        scene="游客路线", raw_request="佛山醒狮文化路线",
        city="佛山", duration="半天",
    )
    family = TaskRequest(
        scene="亲子体验", raw_request="佛山带孩子看醒狮",
        city="佛山", duration="半天",
    )
    sources = RetrievalBundle(query="醒狮", chunks=())
    visitor_prompt = build_initial_messages(visitor, sources)[1]["content"]
    family_prompt = build_initial_messages(family, sources)[1]["content"]
    assert "【任务模式：岭南文化路线】" in visitor_prompt
    assert "【任务模式：岭南文化路线】" in family_prompt
    assert "半天原则上不超过 3 个主要体验节点" in visitor_prompt
    assert "半天建议 1–2 个主要体验节点" in family_prompt
    assert "监护人陪同" in family_prompt
    assert "独立使用刀具" in family_prompt
    assert "未说明儿童年龄" in family_prompt
    assert "未说明儿童年龄" not in visitor_prompt
    assert build_task_plan(visitor, sources) != build_task_plan(family, sources)


def test_study_strategy_requires_recordable_outcomes():
    req = TaskRequest(scene="学生研学", raw_request="观察广绣针法")
    prompt = build_initial_messages(req, RetrievalBundle(query="广绣", chunks=()))[1]["content"]
    assert "目标需可观察或可展示" in prompt
    assert "采访仅作为拟议活动" in prompt
    assert "未指定学段" in prompt


def test_social_and_video_separately_specialized():
    social = TaskRequest(scene="内容创作", raw_request="广绣故事", task_type=TaskType.SOCIAL)
    video = social.with_updates(task_type=TaskType.VIDEO)
    source = RetrievalBundle(query="广绣", chunks=())
    a = build_initial_messages(social, source)[1]["content"]
    b = build_initial_messages(video, source)[1]["content"]
    assert "文化事实和体验建议分开表达" in a
    assert "60 秒分镜表要有镜头时长" in b
    assert "杜撰传承人发言" in b
    assert "60 秒分镜表要有镜头时长" not in a


def test_qa_strategy_prioritizes_actual_question():
    request = TaskRequest(scene="非遗问答", raw_request="粤剧为什么有不同的行当？")
    prompt = build_initial_messages(request, RetrievalBundle(query="粤剧", chunks=()))[1]["content"]
    assert "先正面回答所问问题" in prompt
    assert "不能把相邻地区类似项目当同一项目" in prompt


def test_family_quick_revision_changes_scene_policy():
    request = TaskRequest(scene="游客路线", raw_request="广州一天粤剧路线", duration="一天")
    changed = plan_quick_revision(request, "更适合亲子")
    assert changed.revised_request.scene == "亲子体验"
    assert resolve_policy(changed.revised_request).key == "family"
    prompt = build_revision_messages(
        # RevisionRequest matches what the FastAPI gateway passes through.
        _revision(changed.revised_request, changed.instruction, changed.target_task_type),
        RetrievalBundle(query="广州粤剧", chunks=()),
    )[1]["content"]
    assert "【V3 场景专属要求】" in prompt
    assert "监护人陪同" in prompt


def _revision(request, instruction, task_type):
    from core.models import RevisionRequest
    return RevisionRequest(
        root_request=request, current_answer="## 方案总览\n旧路线",
        instruction=instruction, target_task_type=task_type,
    )


def test_family_half_day_revision_keeps_family_policy():
    request = TaskRequest(scene="亲子体验", raw_request="带孩子了解陶塑", duration="一天")
    updated = plan_quick_revision(request, "压缩成半天")
    assert updated.revised_request.duration == "半天"
    assert resolve_policy(updated.revised_request).key == "family"


def test_custom_revise_switches_between_social_and_study_safely():
    req = TaskRequest(scene="内容创作", raw_request="潮州木雕科普图文")
    changed = plan_custom_revision(req, "改成学生研学任务卡和记录表")
    assert changed.revised_request.scene == "学生研学"
    assert resolve_policy(changed.revised_request).key == "study"


@pytest.mark.parametrize(
    ("scene", "type_"),
    [
        ("亲子体验", TaskType.SOCIAL),
        ("学生研学", TaskType.ROUTE),
        ("非遗问答", TaskType.VIDEO),
        ("内容创作", TaskType.STUDY),
        ("游客路线", TaskType.QA),
    ],
)
def test_inconsistent_scene_and_type_blocked_before_paid_api(scene, type_):
    from services.scenarios import resolve_policy
    req = TaskRequest(scene=scene, raw_request="了解广东非遗", task_type=type_)
    with pytest.raises(ValueError, match="不匹配"):
        resolve_policy(req)


def test_gateway_returns_http_400_for_mismatched_mode(monkeypatch):
    from core.models import ModelConfig
    monkeypatch.setattr(
        "api.main.build_model_config",
        lambda _settings: ModelConfig(api_key="local-test", base_url="https://api.openai.com/v1", model_name="stub"),
    )
    body = GenerateInput.model_validate({
        "request": {
            "scene": "学生研学", "raw_request": "广绣研学",
            "task_type": "social",
        },
    })
    with pytest.raises(HTTPException) as error:
        _prepare_generation(body, revise=False)
    assert error.value.status_code == 400


def test_scene_diagnostics_are_advisory_and_backwards_compatible():
    request = TaskRequest(scene="亲子体验", raw_request="带孩子看醒狮")
    content = "## 方案总览\n热闹\n## 行程时间轴\n上午\n## 节点详情\n看表演\n## 体验与记录建议\n欣赏\n## 出发前提醒\n以官方公告为准"
    old = inspect_answer(content, TaskType.ROUTE, RetrievalBundle(query="醒狮", chunks=()))
    new = inspect_answer(content, TaskType.ROUTE, RetrievalBundle(query="醒狮", chunks=()), request=request)
    assert old["sections_complete"]
    assert old["scenario"] is None
    assert new["scenario"] == "family"
    assert "可参与的亲子活动" in new["scene_review_hints"]
    assert "监护与安全提示" in new["scene_review_hints"]
    with_care = content + "\n家长陪同并安排观察互动"
    assert diagnostic_findings(with_care, request) == ()


def test_off_topic_official_entry_not_promoted_in_plan():
    chunk = RetrievedChunk(
        chunk_id="official", source_path="data/heritage_records.json",
        title="粤剧", content="项目：粤剧（广府大戏）",
        source_url="https://www.ihchina.cn/project_details/13221/",
    )
    request = TaskRequest(scene="非遗问答", raw_request="广州天气如何？")
    plan = build_task_plan(request, RetrievalBundle(query=request.retrieval_query, chunks=(chunk,)))
    assert "缺少官方项目记录" in plan


def test_optional_missing_inputs_are_safe_advisories():
    family = TaskRequest(scene="亲子体验", raw_request="带孩子去体验非遗")
    assert any("儿童年龄" in note for note in request_advisories(family))
    assert any("城市" in note for note in request_advisories(family))
    assert "输入缺失提醒" in build_scene_guidance(family)


@pytest.mark.parametrize(
    "filename",
    [
        "services/scenarios.py",
        "services/planner.py",
        "services/prompt_builder.py",
        "services/quality.py",
        "api/main.py",
    ],
)
def test_vercel_backend_matches_canonical(filename):
    # A duplicated backend is required by Vercel Services, so changes must
    # always be mirrored. Do not delete either tree just to remove duplicates.
    backend_file = ROOT / "backend" / filename
    assert backend_file.read_bytes() == (ROOT / filename).read_bytes()
