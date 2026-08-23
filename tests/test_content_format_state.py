from core.models import TaskRequest, TaskType
from core.state import complete_initial_generation, initialize_state, load_recent_plan


def test_recent_video_plan_restores_video_content_format() -> None:
    state: dict = {}
    initialize_state(state)
    request = TaskRequest(
        scene="内容创作",
        raw_request="生成英歌舞短视频",
        task_type=TaskType.VIDEO,
    )
    complete_initial_generation(state, request, "视频答案", "项目知识库 · 英歌舞")
    item = dict(state["recent_plans"][0])

    state["content_format"] = "图文"
    load_recent_plan(state, item)

    assert state["pending_form_sync"]["content_format"] == "短视频"
