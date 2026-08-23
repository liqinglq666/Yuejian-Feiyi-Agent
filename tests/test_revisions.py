from core.models import RetrievalBundle, RevisionRequest, TaskRequest, TaskType
from core.revisions import plan_custom_revision, plan_quick_revision
from core.state import (
    apply_pending_form_sync,
    complete_initial_generation,
    complete_revision,
    initialize_state,
    load_recent_plan,
    queue_revision,
)
from services.prompt_builder import build_revision_messages


def test_quick_half_day_revision_overrides_duration_and_persists() -> None:
    state: dict = {}
    initialize_state(state)
    original = TaskRequest(
        scene="游客路线",
        raw_request="安排广州一天非遗路线",
        city="广州",
        duration="一天",
    )
    complete_initial_generation(state, original, "一天版方案", "来源 A")

    plan = plan_quick_revision(original, "压缩成半天")
    assert plan.revised_request.duration == "半天"
    assert plan.target_task_type == TaskType.ROUTE

    queue_revision(
        state,
        plan.instruction,
        plan.target_task_type,
        revised_request=plan.revised_request,
    )
    assert state["pending_job"]["revised_request"]["duration"] == "半天"

    complete_revision(
        state,
        plan.instruction,
        plan.target_task_type,
        "半天版方案",
        "来源 B",
        revised_request=plan.revised_request,
    )
    assert state["root_request"]["duration"] == "半天"
    assert state["pending_form_sync"]["selected_duration"] == "半天"

    apply_pending_form_sync(state)
    assert state["selected_duration"] == "半天"
    assert state["pending_form_sync"] is None


def test_quick_content_conversion_updates_scene_and_task_type() -> None:
    request = TaskRequest(scene="游客路线", raw_request="广州非遗路线", duration="一天")
    plan = plan_quick_revision(request, "生成短视频脚本")

    assert plan.revised_request.scene == "内容创作"
    assert plan.revised_request.identity == "内容创作者"
    assert plan.revised_request.task_type == TaskType.VIDEO


def test_half_day_from_content_mode_returns_to_consistent_route_mode() -> None:
    request = TaskRequest(
        scene="内容创作",
        raw_request="写一篇广州非遗小红书",
        duration="不限",
        identity="内容创作者",
        output_style="小红书风格",
    )
    plan = plan_quick_revision(request, "压缩成半天")

    assert plan.revised_request.task_type == TaskType.ROUTE
    assert plan.revised_request.scene == "游客路线"
    assert plan.revised_request.duration == "半天"
    assert plan.revised_request.identity == "自动匹配"
    assert plan.revised_request.output_style == "清晰实用"


def test_custom_revision_infers_duration_and_parent_identity() -> None:
    request = TaskRequest(scene="游客路线", raw_request="佛山非遗路线", duration="一天")
    plan = plan_custom_revision(request, "压缩成半天，并改成亲子版")

    assert plan.revised_request.duration == "半天"
    assert plan.revised_request.scene == "亲子体验"
    assert plan.revised_request.identity == "亲子家庭"
    assert plan.target_task_type == TaskType.ROUTE


def test_custom_parent_video_keeps_audience_and_changes_output_type() -> None:
    request = TaskRequest(scene="游客路线", raw_request="佛山非遗路线", duration="一天")
    plan = plan_custom_revision(request, "改成适合亲子家庭的短视频脚本")

    assert plan.target_task_type == TaskType.VIDEO
    assert plan.revised_request.scene == "内容创作"
    assert plan.revised_request.identity == "亲子家庭"
    assert plan.revised_request.task_type == TaskType.VIDEO


def test_custom_duration_uses_latest_non_negated_request() -> None:
    request = TaskRequest(scene="游客路线", raw_request="广州非遗路线", duration="半天")
    plan = plan_custom_revision(request, "先不要半天，还是改回一天")

    assert plan.revised_request.duration == "一天"
    assert plan.target_task_type == TaskType.ROUTE


def test_recent_plan_restores_sources_and_updates_by_plan_id() -> None:
    state: dict = {}
    initialize_state(state)

    first = TaskRequest(scene="游客路线", raw_request="广州路线", city="广州")
    complete_initial_generation(state, first, "广州答案", "广州来源")
    first_item = dict(state["recent_plans"][0])
    first_id = first_item["plan_id"]

    second = TaskRequest(scene="游客路线", raw_request="佛山路线", city="佛山")
    complete_initial_generation(state, second, "佛山答案", "佛山来源")
    second_id = state["recent_plans"][0]["plan_id"]

    load_recent_plan(state, first_item)
    assert state["active_plan_id"] == first_id
    assert state["current_sources"] == "广州来源"

    revised = first.with_updates(duration="半天")
    complete_revision(
        state,
        "压缩成半天",
        TaskType.ROUTE,
        "广州半天答案",
        "广州新来源",
        revised_request=revised,
    )

    assert state["recent_plans"][0]["plan_id"] == first_id
    assert state["recent_plans"][0]["sources"] == "广州新来源"
    assert any(item["plan_id"] == second_id for item in state["recent_plans"])
    assert len({item["plan_id"] for item in state["recent_plans"]}) == 2


def test_revision_prompt_prioritizes_effective_conditions_over_old_text() -> None:
    effective = TaskRequest(
        scene="游客路线",
        raw_request="安排广州一天非遗路线",
        city="广州",
        duration="半天",
        task_type=TaskType.ROUTE,
    )
    revision = RevisionRequest(
        root_request=effective,
        current_answer="这是原来的一天版路线。",
        instruction="压缩成半天",
        target_task_type=TaskType.ROUTE,
    )
    messages = build_revision_messages(revision, RetrievalBundle(query="", chunks=()))
    prompt = messages[1]["content"]

    assert "【本轮生效条件｜最高优先级】" in prompt
    assert "- 时间：半天" in prompt
    assert "必须以本轮生效的“时间”字段为准" in prompt
    assert prompt.index("- 时间：半天") < prompt.index("安排广州一天非遗路线")
