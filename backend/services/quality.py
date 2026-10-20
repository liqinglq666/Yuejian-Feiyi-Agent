"""Deterministic post-generation review; not an automated fact verifier.

Evidence labels require a direct topic match to an official registry entry.
They do not imply that every claim in a generated answer is supported.
"""
from __future__ import annotations

import re

from core.models import RetrievalBundle, RetrievedChunk, TaskRequest, TaskType
from services.scenarios import diagnostic_findings, resolve_policy

REQUIRED: dict[TaskType, tuple[str, ...]] = {
    TaskType.QA: ("一句话认识", "文化背景", "核心看点", "如何体验", "核验提醒"),
    TaskType.ROUTE: ("方案总览", "行程时间轴", "节点详情", "体验与记录建议", "出发前提醒"),
    TaskType.STUDY: ("研学主题与目标", "行前准备", "现场任务卡", "采访问题", "观察记录表", "报告提纲"),
    TaskType.SOCIAL: ("内容定位", "标题候选", "完整正文", "配图建议", "标签与延展选题"),
    TaskType.VIDEO: ("视频定位", "3 秒钩子", "60 秒分镜表", "旁白与字幕", "拍摄建议", "标题与标签"),
}


def directly_supported_topic(chunk: RetrievedChunk, query: str) -> bool:
    """Whether a registry record actually names the topic of the request."""
    if chunk.source_path != "data/heritage_records.json":
        return False
    if not chunk.source_url.startswith("https://www.ihchina.cn/"):
        return False

    # '项目：粤绣（广绣）' and similar structured records preserve alias metadata
    # in the first line, whereas free-form corpus prose is never official evidence.
    first_line = chunk.content.split("\n", 1)[0]
    alias_list = []
    match = re.match(r"^项目：.+?（(.*?)）$", first_line)
    if match:
        alias_list = [name.strip() for name in match.group(1).split("、")]

    # National-register titles often include a qualifier, e.g. "粤绣（广绣）"
    # or "英歌（潮阳英歌）". Recognize both the base project and its variant.
    base_name = re.split(r"[（(]", chunk.title, maxsplit=1)[0].strip()
    names = [chunk.title, base_name, *alias_list]
    names.extend(re.findall(r"[（(]([^()（）]+)[）)]", chunk.title))
    names = [name for name in names if len(name) >= 2]

    # Generic city-only queries do not turn whatever official snippet happened
    # to rank in the top results into "verified factual evidence".
    return any(name in query for name in names)


def inspect_answer(
    answer: str,
    task_type: TaskType,
    retrieval: RetrievalBundle,
    request: TaskRequest | None = None,
) -> dict:
    headings = {h.strip() for h in re.findall(r"^##\s+(.+?)\s*$", answer, flags=re.MULTILINE)}
    missing = [title for title in REQUIRED[task_type] if title not in headings]
    sources = {
        chunk.source_url
        for chunk in retrieval.chunks
        if directly_supported_topic(chunk, retrieval.query)
    }
    # Heuristic hints are advisory, never evidence of verified safety/accuracy.
    policy = resolve_policy(request) if request is not None else None
    hints = diagnostic_findings(answer, request) if request is not None else ()
    return {
        "sections_complete": not missing,
        "missing_sections": missing,
        "official_source_count": len(sources),
        "needs_fact_verification": not bool(sources),
        "scenario": policy.key if policy is not None else None,
        "scene_review_hints": list(hints),
    }
