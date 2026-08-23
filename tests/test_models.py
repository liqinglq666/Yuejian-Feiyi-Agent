from core.models import TaskRequest, TaskType, task_type_for_action


def test_content_scene_uses_explicit_social_route_even_when_text_mentions_video() -> None:
    request = TaskRequest(
        scene="内容创作",
        raw_request="先写小红书正文，再给一个短视频延展建议",
    )
    assert request.task_type is TaskType.SOCIAL


def test_content_scene_can_explicitly_use_video_route() -> None:
    request = TaskRequest(
        scene="内容创作",
        raw_request="生成一条英歌舞短视频",
        task_type=TaskType.VIDEO,
    )
    assert request.task_type is TaskType.VIDEO


def test_retrieval_query_excludes_output_scaffolding() -> None:
    request = TaskRequest(
        scene="游客路线",
        raw_request="我想在广州体验粤剧和醒狮",
        city="广州",
        interests=("粤剧", "醒狮"),
        output_style="研学报告",
    )
    query = request.retrieval_query
    assert "网页输出" not in query
    assert "表格" not in query
    assert "广州" in query
    assert "粤剧" in query


def test_explicit_city_removes_conflicting_city_from_retrieval_query() -> None:
    request = TaskRequest(
        scene="游客路线",
        raw_request="原本想去广州看粤剧，现在请按新的条件安排",
        city="佛山",
        interests=("醒狮",),
    )
    query = request.retrieval_query
    assert "佛山" in query
    assert "广州" not in query
    assert "醒狮" in query


def test_action_can_change_target_task_type() -> None:
    assert task_type_for_action("生成短视频脚本", TaskType.ROUTE) is TaskType.VIDEO
    assert task_type_for_action("未知动作", TaskType.ROUTE) is TaskType.ROUTE


def test_request_length_limit_is_enforced() -> None:
    import pytest

    with pytest.raises(ValueError, match="不能超过"):
        TaskRequest(scene="非遗问答", raw_request="粤" * 1201)
