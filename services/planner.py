"""Lightweight deterministic task planning without an extra paid LLM call.

The plan is injected as task guidance. It never invents real places, events,
opening hours, travel times, or claims of verified fact.
"""
from __future__ import annotations

from core.models import RetrievalBundle, TaskRequest, TaskType

STEPS: dict[TaskType, tuple[str, ...]] = {
    TaskType.ROUTE: (
        "识别城市、时长、同行人以及偏好的非遗主题",
        "只从检索材料中选取与地点及主题直接相关的项目",
        "按合理节奏组织文化体验节点，不猜测真实交通时间",
        "检查是否错误承诺开放时间、票价、预约与演出",
    ),
    TaskType.STUDY: (
        "确定学生群体与可观察的研学目标",
        "用已核验文化事实设计观察或采访问题",
        "组织行前、现场记录和报告结构",
        "核实活动可执行性并标出现场信息待确认处",
    ),
    TaskType.QA: (
        "确定用户问的是项目概念、历史还是体验方式",
        "区分有官方来源的文化事实和待核验的信息",
        "用通俗语言解释重点并提供合理后续体验建议",
        "检查名录编号、人物及实时信息是否被无依据地确定",
    ),
    TaskType.SOCIAL: (
        "确认创作主题、受众与发布用途",
        "选择可溯源的文化事实，区分创意修辞与事实陈述",
        "完成标题、正文和配图建议",
        "删除无来源的活动安排、人物、地点及宣传性承诺",
    ),
    TaskType.VIDEO: (
        "确定视频主题、时长及受众",
        "用可核验事实编排旁白与画面",
        "输出可执行的分镜和拍摄说明",
        "标记未经确认的采访对象、场地和演出安排",
    ),
}


def build_task_plan(request: TaskRequest, retrieval: RetrievalBundle) -> str:
    task_type = request.task_type or TaskType.QA
    has_official = any(c.source_path == "data/heritage_records.json" for c in retrieval.chunks)
    lines = [f"任务类型：{task_type.value}", "内部执行步骤（不要在最终报告显示）："]
    lines.extend(f"{i}. {step}" for i, step in enumerate(STEPS[task_type], start=1))
    lines.append(
        "检索中存在官方项目记录，但具体事实仍须逐项对应原文。"
        if has_official
        else "缺少官方项目记录，须降低事实确定性，不得编造具体信息。"
    )
    lines.append("在输出前逐项自查完整标题、城市与时长、事实支持情况和体验风险。")
    return "\n".join(lines)
