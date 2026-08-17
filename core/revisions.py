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
        request_updates={
            "scene": "亲子体验",
            "identity": "亲子家庭",
            "output_style": "游客友好",
        },
    ),
    "生成小红书文案": RevisionPreset(
        instruction="改写成一篇可直接发布的小红书图文，包含标题、正文、配图建议和标签。",
        target_task_type=TaskType.SOCIAL,
        request_updates={
            "scene": "内容创作",
            "identity": "内容创作者",
            "output_style": "小红书风格",
        },
    ),
    "生成短视频脚本": RevisionPreset(
        instruction="改写成一条 60 秒短视频脚本，包含分镜、旁白、字幕和拍摄建议。",
        target_task_type=TaskType.VIDEO,
        request_updates={
            "scene": "内容创作",
            "identity": "内容创作者",
            "output_style": "清晰实用",
        },
    ),
    "加研学记录表": RevisionPreset(
        instruction="改写成研学方案，并补充可填写的观察记录表、采访问题和报告提纲。",
        target_task_type=TaskType.STUDY,
        request_updates={
            "scene": "学生研学",
            "identity": "学生研学",
            "output_style": "研学报告",
        },
    ),
}


_TASK_KEYWORDS: dict[TaskType, tuple[str, ...]] = {
    TaskType.VIDEO: ("短视频", "视频脚本", "分镜", "口播"),
    TaskType.SOCIAL: ("小红书", "图文", "发布文案", "公众号", "推文"),
    TaskType.STUDY: ("研学", "任务卡", "记录表", "报告提纲"),
    TaskType.ROUTE: ("路线", "行程", "游玩安排", "一日游", "半日游"),
    TaskType.QA: ("问答", "科普", "介绍一下", "讲解"),
}

_IDENTITY_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("亲子家庭", ("亲子", "带孩子", "小朋友", "儿童")),
    ("学生研学", ("学生", "高中生", "大学生", "研学")),
    ("内容创作者", ("博主", "创作者", "自媒体", "账号运营")),
    ("外地游客", ("游客", "第一次来", "外地")),
    ("本地居民", ("本地居民", "本地人")),
)


def plan_quick_revision(request: TaskRequest, action: str) -> RevisionPlan:
    try:
        preset = REVISION_PRESETS[action]
    except KeyError as exc:
        raise ValueError(f"不支持的快捷调整：{action}") from exc

    updates = dict(preset.request_updates)
    if action == "压缩成半天":
        is_parent = request.scene == "亲子体验" or request.identity == "亲子家庭"
        updates.update(
            scene="亲子体验" if is_parent else "游客路线",
            identity="亲子家庭" if is_parent else _route_identity(request.identity),
            output_style=_route_style(request.output_style),
        )

    revised_request = request.with_updates(
        task_type=preset.target_task_type,
        **updates,
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

    duration = _infer_duration(text)
    explicit_target = _infer_task_type(text)
    identity = _infer_identity(text)

    target = explicit_target or request.task_type or TaskType.QA
    if explicit_target is None and duration:
        target = TaskType.ROUTE
    if explicit_target is None and identity == "亲子家庭":
        target = TaskType.ROUTE

    updates: dict[str, Any] = {}
    if duration:
        updates["duration"] = duration
    if identity:
        updates["identity"] = identity

    scene, default_identity, output_style = _conditions_for_target(
        request,
        target,
        explicit_identity=identity,
        text=text,
    )
    updates["scene"] = scene
    if not identity and default_identity:
        updates["identity"] = default_identity
    if output_style:
        updates["output_style"] = output_style

    revised_request = request.with_updates(task_type=target, **updates)
    return RevisionPlan(
        instruction=text,
        target_task_type=target,
        revised_request=revised_request,
    )


def _infer_task_type(text: str) -> TaskType | None:
    matches: list[tuple[int, TaskType]] = []
    for task_type, keywords in _TASK_KEYWORDS.items():
        for keyword in keywords:
            start = text.rfind(keyword)
            if start >= 0:
                matches.append((start, task_type))
    if not matches:
        return None
    return max(matches, key=lambda item: item[0])[1]


def _infer_identity(text: str) -> str | None:
    matches: list[tuple[int, str]] = []
    for identity, keywords in _IDENTITY_KEYWORDS:
        for keyword in keywords:
            start = text.rfind(keyword)
            if start >= 0:
                matches.append((start, identity))
    if not matches:
        return None
    return max(matches, key=lambda item: item[0])[1]


def _conditions_for_target(
    request: TaskRequest,
    target: TaskType,
    *,
    explicit_identity: str | None,
    text: str,
) -> tuple[str, str | None, str | None]:
    if target == TaskType.VIDEO:
        return "内容创作", explicit_identity or "内容创作者", "清晰实用"
    if target == TaskType.SOCIAL:
        style = "小红书风格" if "小红书" in text else "清晰实用"
        return "内容创作", explicit_identity or "内容创作者", style
    if target == TaskType.STUDY:
        return "学生研学", explicit_identity or "学生研学", "研学报告"
    if target == TaskType.ROUTE:
        is_parent = explicit_identity == "亲子家庭" or (
            explicit_identity is None
            and (request.scene == "亲子体验" or request.identity == "亲子家庭")
        )
        scene = "亲子体验" if is_parent else "游客路线"
        identity = "亲子家庭" if is_parent else _route_identity(request.identity)
        return scene, identity, _route_style(request.output_style)
    return "非遗问答", explicit_identity or request.identity, "专业讲解"


def _route_identity(identity: str) -> str:
    if identity in {"外地游客", "本地居民", "亲子家庭"}:
        return identity
    return "自动匹配"


def _route_style(output_style: str) -> str:
    if output_style in {"清晰实用", "游客友好", "专业讲解"}:
        return output_style
    return "清晰实用"


def _infer_duration(text: str) -> str | None:
    duration_patterns = (
        ("半天", ("半天", "半日")),
        ("一天", ("一天", "一日", "1天")),
        ("两天", ("两天", "二天", "2天")),
        ("周末", ("周末",)),
        ("不限", ("时间不限", "不限时间")),
    )
    matches: list[tuple[int, str]] = []
    for duration, patterns in duration_patterns:
        for pattern in patterns:
            start = text.rfind(pattern)
            if start < 0:
                continue
            prefix = text[max(0, start - 7) : start]
            if any(marker in prefix for marker in ("不要", "不想", "取消", "别用", "去掉")):
                continue
            matches.append((start, duration))
    if not matches:
        return None
    return max(matches, key=lambda item: item[0])[1]
