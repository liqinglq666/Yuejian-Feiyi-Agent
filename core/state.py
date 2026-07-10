from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, MutableMapping

from core.models import TaskRequest, TaskType


DEFAULT_STATE: dict[str, Any] = {
    "selected_scene": "游客路线",
    "last_scene": "游客路线",
    "user_input": "我第一次来广州，有一天时间，想体验岭南非遗文化，最好适合拍照和写研学记录。",
    "output_style": "清晰实用",
    "temperature": 0.62,
    "provider": "阿里云百炼 Qwen",
    "last_provider": "阿里云百炼 Qwen",
    "user_api_key": "",
    "user_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "user_model_name": "qwen-turbo",
    "pending_job": None,
    "root_request": None,
    "current_answer": "",
    "current_sources": "",
    "revision_history": [],
    "recent_plans": [],
    "toast_message": "",
    "toast_icon": "🦁",
}


def initialize_state(state: MutableMapping[str, Any]) -> None:
    for key, value in DEFAULT_STATE.items():
        if key not in state:
            state[key] = deepcopy(value)


def queue_initial_generation(state: MutableMapping[str, Any], request: TaskRequest) -> None:
    state["pending_job"] = {
        "kind": "initial",
        "request": request.to_dict(),
    }


def queue_revision(
    state: MutableMapping[str, Any],
    instruction: str,
    target_task_type: TaskType,
) -> None:
    root_payload = state.get("root_request")
    answer = str(state.get("current_answer", ""))
    if not root_payload or not answer.strip():
        raise ValueError("请先生成一个方案。")

    state["pending_job"] = {
        "kind": "revision",
        "root_request": dict(root_payload),
        "current_answer": answer,
        "instruction": instruction.strip(),
        "target_task_type": target_task_type.value,
    }


def complete_initial_generation(
    state: MutableMapping[str, Any],
    request: TaskRequest,
    answer: str,
    sources_markdown: str,
) -> None:
    state["root_request"] = request.to_dict()
    state["current_answer"] = answer
    state["current_sources"] = sources_markdown
    state["revision_history"] = []
    state["pending_job"] = None
    _add_recent_plan(state, request, answer)


def complete_revision(
    state: MutableMapping[str, Any],
    instruction: str,
    target_task_type: TaskType,
    answer: str,
    sources_markdown: str,
) -> None:
    history = list(state.get("revision_history", []))
    history.append(
        {
            "instruction": instruction,
            "task_type": target_task_type.value,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    state["revision_history"] = history[-10:]
    state["current_answer"] = answer
    state["current_sources"] = sources_markdown
    state["pending_job"] = None


def clear_current_plan(state: MutableMapping[str, Any]) -> None:
    state["pending_job"] = None
    state["root_request"] = None
    state["current_answer"] = ""
    state["current_sources"] = ""
    state["revision_history"] = []


def set_toast(state: MutableMapping[str, Any], message: str, icon: str = "🦁") -> None:
    state["toast_message"] = message
    state["toast_icon"] = icon


def _add_recent_plan(
    state: MutableMapping[str, Any],
    request: TaskRequest,
    answer: str,
) -> None:
    title = _guess_title(request)
    item = {
        "title": title,
        "request": request.to_dict(),
        "answer": answer,
        "time": datetime.now().strftime("%H:%M"),
    }
    recent = [entry for entry in state.get("recent_plans", []) if entry.get("answer") != answer]
    recent.insert(0, item)
    state["recent_plans"] = recent[:3]


def _guess_title(request: TaskRequest) -> str:
    city = "" if request.city == "自动判断" else request.city
    if city:
        return f"{city}{request.scene.replace('游客', '').replace('学生', '')}"
    text = request.raw_request.strip().replace("\n", " ")
    return text[:16] + ("…" if len(text) > 16 else "")
