from core.models import TaskRequest, TaskType
from core.state import (
    complete_initial_generation,
    complete_revision,
    initialize_state,
    queue_revision,
)


def test_revision_keeps_root_request_and_only_records_instruction() -> None:
    state: dict = {}
    initialize_state(state)
    request = TaskRequest(scene="游客路线", raw_request="广州一天体验粤剧")
    complete_initial_generation(state, request, "第一版答案", "")

    queue_revision(state, "改成亲子版", TaskType.ROUTE)
    job = state["pending_job"]
    assert job["root_request"]["raw_request"] == "广州一天体验粤剧"
    assert job["current_answer"] == "第一版答案"
    assert "【最初需求】" not in job["root_request"]["raw_request"]

    complete_revision(state, "改成亲子版", TaskType.ROUTE, "第二版答案", "")
    assert state["root_request"]["raw_request"] == "广州一天体验粤剧"
    assert state["current_answer"] == "第二版答案"
    assert len(state["revision_history"]) == 1
