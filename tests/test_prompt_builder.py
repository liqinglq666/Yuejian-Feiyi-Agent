from core.models import RetrievalBundle, RevisionRequest, TaskRequest, TaskType
from services.prompt_builder import build_initial_messages, build_revision_messages


def test_initial_prompt_has_one_task_instruction_layer() -> None:
    request = TaskRequest(scene="内容创作", raw_request="写一篇广绣小红书")
    messages = build_initial_messages(request, RetrievalBundle(query="广绣", chunks=()))
    prompt = messages[1]["content"]
    assert prompt.count("【任务模式：图文传播】") == 1
    assert "【任务模式：短视频脚本】" not in prompt


def test_initial_video_prompt_uses_video_instruction() -> None:
    request = TaskRequest(
        scene="内容创作",
        raw_request="生成英歌舞短视频",
        task_type=TaskType.VIDEO,
    )
    messages = build_initial_messages(request, RetrievalBundle(query="英歌舞", chunks=()))
    prompt = messages[1]["content"]
    assert "【任务模式：短视频脚本】" in prompt
    assert "【任务模式：图文传播】" not in prompt


def test_initial_prompt_prioritizes_structured_conditions() -> None:
    request = TaskRequest(
        scene="游客路线",
        raw_request="原本安排广州一天路线",
        city="佛山",
        duration="半天",
    )
    messages = build_initial_messages(request, RetrievalBundle(query="佛山", chunks=()))
    prompt = messages[1]["content"]
    assert "【结构化条件｜最高优先级】" in prompt
    assert "- 城市：佛山" in prompt
    assert "- 时间：半天" in prompt
    assert "必须以结构化条件为准" in prompt
    assert prompt.index("- 城市：佛山") < prompt.index("原本安排广州一天路线")


def test_revision_prompt_does_not_recurse_previous_prompt() -> None:
    root = TaskRequest(scene="游客路线", raw_request="广州一天体验粤剧")
    revision = RevisionRequest(
        root_request=root,
        current_answer="## 当前路线\n上午参观，下午体验。",
        instruction="改成亲子版",
        target_task_type=TaskType.ROUTE,
    )
    messages = build_revision_messages(revision, RetrievalBundle(query="广州粤剧", chunks=()))
    prompt = messages[1]["content"]
    assert prompt.count("【最初需求】") == 1
    assert prompt.count("【当前方案】") == 1
    assert prompt.count("【本次修改要求】") == 1
    assert "上一版 Prompt" not in prompt
