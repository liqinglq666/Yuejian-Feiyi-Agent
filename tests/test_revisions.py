from core.models import RetrievalBundle, RevisionRequest, TaskRequest, TaskType
from core.revisions import plan_custom_revision, plan_quick_revision
from core.state import (
    apply_pending_form_sync,
    complete_initial_generation,
    complete_revision,
    initialize_state,
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
    complete_initial_generation(state, original, "一天版方案", "")

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
        "",
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
    assert plan.revised_request.task_type == TaskType.VIDEO


def test_custom_revision_infers_duration_and_parent_identity() -> None:
    request = TaskRequest(scene="游客路线", raw_request="佛山非遗路线", duration="一天")
    plan = plan_custom_revision(request, "压缩成半天，并改成亲子版")

    assert plan.revised_request.duration == "半天"
    assert plan.revised_request.scene == "亲子体验"
    assert plan.revised_request.identity == "亲子家庭"
    assert plan.target_task_type == TaskType.ROUTE


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
