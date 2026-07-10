from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.models import TaskRequest, TaskType


@dataclass(frozen=True)
class RevisionPlan:
    instruction: str
    target_task_type: TaskType
    revised_request: TaskRequest


@dataclass(frozen=True)
class RevisionPreset:
    instruction: str
    target_task_type: TaskType
    request_updates: dict[str, Any]


REVISION_PRESETS: dict[str, RevisionPreset] = {
    "压缩成半天": RevisionPreset(
        instruction="把方案压缩成半天，保留最值得体验的节点，并减少往返。",
        target_task_type=TaskType.ROUTE,
        request_updates={"duration": "半天"},
    ),
    "更适合亲子": RevisionPreset(
        instruction="改成适合亲子家庭的版本，增加孩子能参与的互动任务，节奏轻松。",
        target_task_type=TaskType.ROUTE,
        request_updates={"scene": "亲子体验", "identity": "亲子家庭"},
    ),
    "生成小红书文案": RevisionPreset(
        instruction="改写成一篇可直接发布的小红书图文，包含标题、正文、配图建议和标签。",
        target_task_type=TaskType.SOCIAL,
        request_updates={"scene": "内容创作", "output_style": "小红书风格"},
    ),
    "生成短视频脚本": RevisionPreset(
        instruction="改写成一条 60 秒短视频脚本，包含分镜、旁白、字幕和拍摄建议。",
        target_task_type=TaskType.VIDEO,
        request_updates={"scene": "内容创作"},
    ),
    "加研学记录表": RevisionPreset(
        instruction="改写成研学方案，并补充可填写的观察记录表、采访问题和报告提纲。",
        target_task_type=TaskType.STUDY,
        request_updates={"scene": "学生研学", "identity": "学生研学", "output_style": "研学报告"},
    ),
}


def plan_quick_revision(request: TaskRequest, action: str) -> RevisionPlan:
    try:
        preset = REVISION_PRESETS[action]
    except KeyError as exc:
        raise ValueError(f"不支持的快捷调整：{action}") from exc

    revised_request = request.with_updates(
        task_type=preset.target_task_type,
        **preset.request_updates,
    )
    return RevisionPlan(
        instruction=preset.instruction,
        target_task_type=preset.target_task_type,
        revised_request=revised_request,
    )


def plan_custom_revision(request: TaskRequest, instruction: str) -> RevisionPlan:
    text = instruction.strip()
    if not text:
        raise ValueError("修改要求不能为空。")

    updates: dict[str, Any] = {}
    target = request.task_type or TaskType.QA

    duration = _infer_duration(text)
    if duration:
        updates["duration"] = duration
        target = TaskType.ROUTE

    if "亲子" in text:
        updates.update(scene="亲子体验", identity="亲子家庭")
        target = TaskType.ROUTE
    elif "研学" in text or "任务卡" in text or "记录表" in text:
        updates.update(scene="学生研学", identity="学生研学", output_style="研学报告")
        target = TaskType.STUDY
    elif "短视频" in text or "视频脚本" in text or "分镜" in text:
        updates.update(scene="内容创作")
        target = TaskType.VIDEO
    elif "小红书" in text or "图文" in text or "发布文案" in text:
        updates.update(scene="内容创作", output_style="小红书风格")
        target = TaskType.SOCIAL

    revised_request = request.with_updates(task_type=target, **updates)
    return RevisionPlan(
        instruction=text,
        target_task_type=target,
        revised_request=revised_request,
    )


def _infer_duration(text: str) -> str | None:
    duration_patterns = (
        ("半天", ("半天", "半日")),
        ("一天", ("一天", "一日", "1天")),
        ("两天", ("两天", "二天", "2天")),
        ("周末", ("周末",)),
        ("不限", ("时间不限", "不限时间")),
    )
    for duration, patterns in duration_patterns:
        if any(pattern in text for pattern in patterns):
            return duration
    return None
