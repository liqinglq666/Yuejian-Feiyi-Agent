from __future__ import annotations

from collections.abc import MutableMapping
from copy import deepcopy
from datetime import datetime
from typing import Any

from core.models import TaskRequest, TaskType

DEFAULT_STATE: dict[str, Any] = {
    "selected_scene": "游客路线",
    "last_scene": "游客路线",
    "user_input": "我第一次来广州，有一天时间，想体验岭南非遗文化，最好适合拍照和写研学记录。",
    "selected_city": "自动判断",
    "selected_duration": "自动判断",
    "selected_identity": "自动匹配",
    "selected_interests": [],
    "custom_revision": "",
    "output_style": "清晰实用",
    "temperature": 0.62,
    "provider": "阿里云百炼 Qwen",
    "last_provider": "阿里云百炼 Qwen",
    "user_api_key": "",
    "user_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "user_model_name": "qwen-turbo",
    "pending_job": None,
    "pending_form_sync": None,
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


def apply_pending_form_sync(state: MutableMapping[str, Any]) -> None:
    """Apply widget values before Streamlit creates the widgets for this run."""
    payload = state.get("pending_form_sync")
    if not payload:
        return
    for key, value in dict(payload).items():
        state[key] = deepcopy(value)
    state["pending_form_sync"] = None


def queue_initial_generation(state: MutableMapping[str, Any], request: TaskRequest) -> None:
    state["pending_job"] = {
        "kind": "initial",
        "request": request.to_dict(),
    }


def queue_revision(
    state: MutableMapping[str, Any],
    instruction: str,
    target_task_type: TaskType,
    revised_request: TaskRequest | None = None,
) -> None:
    root_payload = state.get("root_request")
    answer = str(state.get("current_answer", ""))
    if not root_payload or not answer.strip():
        raise ValueError("请先生成一个方案。")

    current_request = TaskRequest.from_dict(dict(root_payload))
    effective_request = revised_request or current_request.with_updates(
        task_type=target_task_type
    )
    state["pending_job"] = {
        "kind": "revision",
        "root_request": current_request.to_dict(),
        "revised_request": effective_request.to_dict(),
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
    revised_request: TaskRequest | None = None,
) -> None:
    pending_job = state.get("pending_job") or {}
    if revised_request is None:
        request_payload = pending_job.get("revised_request") or state.get("root_request")
        if not request_payload:
            raise ValueError("缺少修订后的结构化需求。")
        revised_request = TaskRequest.from_dict(dict(request_payload))

    history = list(state.get("revision_history", []))
    history.append(
        {
            "instruction": instruction,
            "task_type": target_task_type.value,
            "duration": revised_request.duration,
            "scene": revised_request.scene,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    state["revision_history"] = history[-10:]
    state["root_request"] = revised_request.to_dict()
    state["current_answer"] = answer
    state["current_sources"] = sources_markdown
    state["pending_job"] = None
    state["custom_revision"] = ""
    state["pending_form_sync"] = _form_values_for_request(revised_request)
    _replace_latest_recent_plan(state, revised_request, answer)


def clear_current_plan(state: MutableMapping[str, Any]) -> None:
    state["pending_job"] = None
    state["pending_form_sync"] = None
    state["root_request"] = None
    state["current_answer"] = ""
    state["current_sources"] = ""
    state["revision_history"] = []
    state["custom_revision"] = ""


def start_new_plan(state: MutableMapping[str, Any]) -> None:
    clear_current_plan(state)
    state["selected_scene"] = DEFAULT_STATE["selected_scene"]
    state["user_input"] = ""
    state["selected_city"] = DEFAULT_STATE["selected_city"]
    state["selected_duration"] = DEFAULT_STATE["selected_duration"]
    state["selected_identity"] = DEFAULT_STATE["selected_identity"]
    state["selected_interests"] = []


def set_toast(state: MutableMapping[str, Any], message: str, icon: str = "🦁") -> None:
    state["toast_message"] = message
    state["toast_icon"] = icon


def _form_values_for_request(request: TaskRequest) -> dict[str, Any]:
    return {
        "selected_scene": request.scene,
        "last_scene": request.scene,
        "selected_city": request.city,
        "selected_duration": request.duration,
        "selected_identity": request.identity,
        "selected_interests": list(request.interests),
        "output_style": request.output_style,
    }


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


def _replace_latest_recent_plan(
    state: MutableMapping[str, Any],
    request: TaskRequest,
    answer: str,
) -> None:
    recent = list(state.get("recent_plans", []))
    updated = {
        "title": _guess_title(request),
        "request": request.to_dict(),
        "answer": answer,
        "time": datetime.now().strftime("%H:%M"),
    }
    if recent:
        recent[0] = updated
    else:
        recent.append(updated)
    state["recent_plans"] = recent[:3]


def _guess_title(request: TaskRequest) -> str:
    city = "" if request.city == "自动判断" else request.city
    if city:
        return f"{city}{request.scene.replace('游客', '').replace('学生', '')}"
    text = request.raw_request.strip().replace("\n", " ")
    return text[:16] + ("…" if len(text) > 16 else "")
