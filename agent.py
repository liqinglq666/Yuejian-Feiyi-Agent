"""Backward-compatible public agent API.

The Streamlit application uses the structured service layer directly. These
functions remain for scripts or third-party imports that used the original API.
"""
from __future__ import annotations

from collections.abc import Generator

from core.models import ModelConfig, TaskRequest, TaskType
from services.llm import complete_chat, stream_chat
from services.prompt_builder import build_initial_messages
from services.retrieval import retrieve


KEYWORD_GROUPS: tuple[tuple[TaskType, tuple[str, ...]], ...] = (
    (TaskType.VIDEO, ("短视频", "分镜", "旁白", "镜头", "口播")),
    (TaskType.SOCIAL, ("小红书", "朋友圈", "图文", "文案", "标签")),
    (TaskType.STUDY, ("研学", "任务卡", "采访问题", "报告提纲")),
    (TaskType.ROUTE, ("路线", "行程", "一日游", "半天", "亲子")),
)

SCENE_BY_TASK = {
    TaskType.QA: "非遗问答",
    TaskType.ROUTE: "游客路线",
    TaskType.STUDY: "学生研学",
    TaskType.SOCIAL: "内容创作",
    TaskType.VIDEO: "内容创作",
}


def detect_task_type(user_input: str) -> str:
    """Compatibility fallback only; the web app uses explicit task routing."""
    for task_type, keywords in KEYWORD_GROUPS:
        if any(keyword in user_input for keyword in keywords):
            return task_type.value
    return TaskType.QA.value


def _build_request(user_input: str, task_type: str | TaskType | None) -> TaskRequest:
    resolved = TaskType(task_type or detect_task_type(user_input))
    return TaskRequest(
        scene=SCENE_BY_TASK[resolved],
        raw_request=user_input,
        task_type=resolved,
    )


def _config(api_key: str | None, base_url: str | None, model_name: str | None) -> ModelConfig:
    return ModelConfig(
        api_key=(api_key or "").strip(),
        base_url=(base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1").strip(),
        model_name=(model_name or "qwen-turbo").strip(),
    )


def ask_agent(
    user_input: str,
    temperature: float = 0.62,
    max_tokens: int = 1600,
    api_key: str | None = None,
    base_url: str | None = None,
    model_name: str | None = None,
    task_type: str | TaskType | None = None,
) -> str:
    request = _build_request(user_input, task_type)
    retrieval = retrieve(request.retrieval_query)
    return complete_chat(
        _config(api_key, base_url, model_name),
        build_initial_messages(request, retrieval),
        temperature=temperature,
        max_tokens=max_tokens,
    )


def ask_agent_stream(
    user_input: str,
    temperature: float = 0.62,
    max_tokens: int = 1600,
    api_key: str | None = None,
    base_url: str | None = None,
    model_name: str | None = None,
    task_type: str | TaskType | None = None,
) -> Generator[str, None, None]:
    request = _build_request(user_input, task_type)
    retrieval = retrieve(request.retrieval_query)
    yield from stream_chat(
        _config(api_key, base_url, model_name),
        build_initial_messages(request, retrieval),
        temperature=temperature,
        max_tokens=max_tokens,
    )
