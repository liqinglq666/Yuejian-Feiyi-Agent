"""Deterministic output checks without a second paid model call.

This is a structural sanity check, not a guarantee that claims are true.
Evidence availability is explicitly reported separately from correctness.
"""
from __future__ import annotations

import re

from core.models import RetrievalBundle, TaskType

REQUIRED: dict[TaskType, tuple[str,...]] = {
    TaskType.QA: ("一句话认识","文化背景","核心看点","如何体验","核验提醒"),
    TaskType.ROUTE: ("方案总览","行程时间轴","节点详情","体验与记录建议","出发前提醒"),
    TaskType.STUDY: ("研学主题与目标","行前准备","现场任务卡","采访问题","观察记录表","报告提纲"),
    TaskType.SOCIAL: ("内容定位","标题候选","完整正文","配图建议","标签与延展选题"),
    TaskType.VIDEO: ("视频定位","3 秒钩子","60 秒分镜表","旁白与字幕","拍摄建议","标题与标签"),
}

def inspect_answer(answer: str, task_type: TaskType, retrieval: RetrievalBundle) -> dict:
    headings = {h.strip() for h in re.findall(r"^##\s+(.+)\s*$", answer, flags=re.MULTILINE)}
    missing = [h for h in REQUIRED[task_type] if h not in headings]
    verified_sources = sum(1 for c in retrieval.chunks if c.source_url.startswith("https://www.ihchina.cn/"))
    return {
        "sections_complete": not missing,
        "missing_sections": missing,
        "official_source_count": verified_sources,
        "needs_fact_verification": verified_sources == 0,
    }
