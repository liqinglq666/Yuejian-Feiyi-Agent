from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class TaskType(str, Enum):
    QA = "qa"
    ROUTE = "route"
    STUDY = "study"
    SOCIAL = "social"
    VIDEO = "video"


SCENE_TASK_MAP: dict[str, TaskType] = {
    "游客路线": TaskType.ROUTE,
    "学生研学": TaskType.STUDY,
    "亲子体验": TaskType.ROUTE,
    "内容创作": TaskType.SOCIAL,
    "非遗问答": TaskType.QA,
}


ACTION_TASK_MAP: dict[str, TaskType] = {
    "压缩成半天": TaskType.ROUTE,
    "更适合亲子": TaskType.ROUTE,
    "生成小红书文案": TaskType.SOCIAL,
    "生成短视频脚本": TaskType.VIDEO,
    "加研学记录表": TaskType.STUDY,
}


@dataclass(frozen=True)
class TaskRequest:
    scene: str
    raw_request: str
    city: str = "自动判断"
    duration: str = "自动判断"
    identity: str = "自动匹配"
    interests: tuple[str, ...] = field(default_factory=tuple)
    output_style: str = "清晰实用"
    task_type: TaskType | None = None

    def __post_init__(self) -> None:
        if not self.raw_request.strip():
            raise ValueError("用户需求不能为空。")
        if self.task_type is None:
            object.__setattr__(self, "task_type", task_type_for_scene(self.scene))

    @property
    def retrieval_query(self) -> str:
        """Only knowledge-bearing fields are used for retrieval.

        Formatting rules and generated prompt scaffolding are intentionally excluded,
        so the retriever cannot be polluted by words such as “表格” or “网页输出”.
        """
        parts = [self.raw_request.strip()]
        if self.city not in {"", "自动判断"}:
            parts.append(self.city)
        if self.interests:
            parts.extend(self.interests)
        return " ".join(dict.fromkeys(part for part in parts if part))

    @property
    def condition_lines(self) -> list[str]:
        values = [
            ("用途", self.scene),
            ("城市", self.city),
            ("时间", self.duration),
            ("身份", self.identity),
            ("输出风格", self.output_style),
            ("特别想包含", "、".join(self.interests) if self.interests else "未指定"),
        ]
        return [f"- {name}：{value}" for name, value in values]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["task_type"] = self.task_type.value if self.task_type else None
        payload["interests"] = list(self.interests)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TaskRequest":
        data = dict(payload)
        raw_type = data.get("task_type")
        data["task_type"] = TaskType(raw_type) if raw_type else None
        data["interests"] = tuple(data.get("interests") or ())
        return cls(**data)


@dataclass(frozen=True)
class ModelConfig:
    api_key: str
    base_url: str
    model_name: str
    timeout_seconds: float = 120.0
    max_retries: int = 1

    def redacted(self) -> dict[str, Any]:
        return {
            "api_key": "***" if self.api_key else "",
            "base_url": self.base_url,
            "model_name": self.model_name,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
        }


@dataclass(frozen=True)
class RevisionRequest:
    root_request: TaskRequest
    current_answer: str
    instruction: str
    target_task_type: TaskType

    def __post_init__(self) -> None:
        if not self.current_answer.strip():
            raise ValueError("当前方案为空，无法继续调整。")
        if not self.instruction.strip():
            raise ValueError("修改要求不能为空。")


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    content: str
    source_path: str
    title: str
    city: str = ""
    category: str = ""
    source_name: str = ""
    source_url: str = ""
    score: float = 0.0

    @property
    def citation_label(self) -> str:
        return self.source_name or self.title or self.source_path


@dataclass(frozen=True)
class RetrievalBundle:
    query: str
    chunks: tuple[RetrievedChunk, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_empty(self) -> bool:
        return not self.chunks

    def formatted_context(self) -> str:
        if not self.chunks:
            return "未检索到高度相关资料。请谨慎回答，不要补造具体事实。"

        blocks: list[str] = []
        for index, chunk in enumerate(self.chunks, start=1):
            metadata = [f"来源：{chunk.citation_label}"]
            if chunk.city:
                metadata.append(f"城市：{chunk.city}")
            if chunk.category:
                metadata.append(f"类别：{chunk.category}")
            if chunk.source_url:
                metadata.append(f"链接：{chunk.source_url}")
            blocks.append(
                f"[S{index}] {'；'.join(metadata)}\n{chunk.content.strip()}"
            )
        return "\n\n---\n\n".join(blocks)

    def source_markdown(self) -> str:
        if not self.chunks:
            return ""
        lines = ["### 本次检索来源"]
        for index, chunk in enumerate(self.chunks, start=1):
            suffix = f"（{chunk.source_url}）" if chunk.source_url else ""
            lines.append(f"- [S{index}] {chunk.citation_label}{suffix}")
        return "\n".join(lines)


def task_type_for_scene(scene: str) -> TaskType:
    try:
        return SCENE_TASK_MAP[scene]
    except KeyError as exc:
        raise ValueError(f"不支持的场景：{scene}") from exc


def task_type_for_action(action: str, fallback: TaskType) -> TaskType:
    return ACTION_TASK_MAP.get(action, fallback)
