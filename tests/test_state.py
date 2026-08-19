from core.models import TaskRequest, TaskType
from core.state import (
    clear_user_api_config,
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


def test_user_api_key_never_enters_recent_plan() -> None:
    state: dict = {}
    initialize_state(state)
    state["model_mode"] = "user"
    state["user_api_key"] = "super-secret-user-key"

    request = TaskRequest(scene="游客路线", raw_request="广州一天体验粤剧")
    complete_initial_generation(state, request, "方案", "来源")

    assert state["user_api_key"] == "super-secret-user-key"
    assert "user_api_key" not in state["recent_plans"][0]
    assert "super-secret-user-key" not in repr(state["recent_plans"])


def test_clear_user_api_config_forgets_key_and_returns_to_auto() -> None:
    state: dict = {}
    initialize_state(state)
    state["model_mode"] = "user"
    state["user_api_key"] = "super-secret-user-key"
    state["user_api_test_status"] = "ok"
    state["user_api_test_message"] = "连接成功"

    clear_user_api_config(state)

    assert state["user_api_key"] == ""
    assert state["model_mode"] == "auto"
    assert state["user_api_test_status"] == ""
    assert state["user_api_test_message"] == ""
