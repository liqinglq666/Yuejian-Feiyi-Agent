"""Deterministic per-scene planning, with no additional model call."""
from __future__ import annotations

from core.models import RetrievalBundle, TaskRequest
from services.quality import directly_supported_topic
from services.scenarios import resolve_policy


def build_task_plan(request: TaskRequest, retrieval: RetrievalBundle) -> str:
    policy = resolve_policy(request)
    has_official = any(
        directly_supported_topic(chunk, retrieval.query) for chunk in retrieval.chunks
    )
    lines = [
        f"任务模式：{request.task_type.value}",
        f"专业策略：{policy.description}",
        "内部执行步骤（不要在最终报告显示）：",
    ]
    lines.extend(f"{position}. {step}" for position, step in enumerate(policy.steps, start=1))
    lines.append(
        "检索到与本次主题直接匹配的官方项目资料；事实仍需逐项核对。"
        if has_official
        else "缺少官方项目记录或官方资料未直接匹配本次主题，须降低事实确定性。"
    )
    lines.append("在输出前检查场景要求、指定标题、事实支持情况与风险提醒。")
    return "\n".join(lines)
