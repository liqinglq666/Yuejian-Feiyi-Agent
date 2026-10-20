"""Scenario-specific domain policies shared by generation and revision.

Keep the public API and the five existing scenes stable. VIDEO is the
content-creation variant, not a sixth homepage entry. All checks are
deterministic guidance/diagnostics, not paid model calls or fact verification.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.models import TaskRequest, TaskType


@dataclass(frozen=True)
class ScenarioPolicy:
    key: str
    description: str
    steps: tuple[str, ...]
    requirements: tuple[str, ...]
    diagnostic_groups: tuple[tuple[str, tuple[str, ...]], ...] = ()


_VISITOR = ScenarioPolicy(
    key="visitor_route",
    description="游客文化路线",
    steps=(
        "识别城市、可用时长和非遗兴趣，优先保证地点与主题一致",
        "从可追溯材料中挑选文化节点，不把非遗项目等同于正在开放的体验活动",
        "按合理节奏组织顺序，不猜测真实交通时间",
        "核查路线节点、票价、演出及开放情况是否需要另行确认",
    ),
    requirements=(
        "把用户选定的城市、时长与兴趣视为硬约束，旧文本冲突时以结构化条件为准。",
        "半天原则上不超过 3 个主要体验节点；一天原则上不超过 5 个，避免赶场。",
        "没有地址、交通或实时活动数据时，只做建议性顺序，不写确定的通勤分钟数。",
        "用『文化看点/拟体验/待确认信息』区分项目知识与实际可到访场馆。",
    ),
    diagnostic_groups=(("现场信息核验提示", ("核实", "确认", "为准", "待核验")),),
)

_FAMILY = ScenarioPolicy(
    key="family",
    description="亲子非遗体验",
    steps=(
        "确认孩子年龄是否已提供；未提供时采用低风险、可调整的活动建议",
        "优先安排少量适龄互动与观察任务，不把成人路线直接缩短",
        "安排休息、补水、陪护与替代活动，不假定能进入工坊或参与演出",
        "检查工具、火源、人群拥挤和其他可能的儿童安全风险",
    ),
    requirements=(
        "每个主要节点写明孩子能参与的具体互动任务，避免只列成人参观点。",
        "孩子年龄不明确时，不假定具体岁数；避免推荐独立使用刀具、窑炉、热水或其他危险器具。",
        "提示监护人陪同，按体力安排休息、饮水与退出选项。",
        "半天建议 1–2 个主要体验节点；若活动和工坊未核实开放，说明需预约或进一步确认。",
    ),
    diagnostic_groups=(
        ("可参与的亲子活动", ("互动", "观察", "动手", "提问", "一起")),
        ("监护与安全提示", ("安全", "陪同", "监护", "看护", "家长")),
    ),
)

_STUDY = ScenarioPolicy(
    key="study",
    description="学生研学",
    steps=(
        "确定适用学段和可观察、可记录的学习目标",
        "用来源可核对的文化事实形成现场任务和开放式观察问题",
        "准备记录表、采访礼仪和成果评价方式",
        "区分可离线完成的研学练习与需事先确认的实地访问",
    ),
    requirements=(
        "目标需可观察或可展示，例如辨识技法、比较材料、记录变化，不只写感受。",
        "现场任务卡应包含行动、观察证据和记录方式，并给出简单可填写的记录表。",
        "采访仅作为拟议活动；没有实际采访不得虚构传承人引语或访问成果。",
        "学生年龄不明确时分层给出基础版和进阶版；涉及工坊需有教师/监护人安全要求。",
    ),
    diagnostic_groups=(
        ("可操作的观察记录", ("观察", "记录", "填写", "勾选")),
        ("研学成果产出", ("报告", "成果", "汇报", "总结")),
    ),
)

_SOCIAL = ScenarioPolicy(
    key="social",
    description="非遗图文创作",
    steps=(
        "明确文化主题、目标受众与发布平台；未指定平台则输出通用图文",
        "把有官方依据的文化事实与创意叙述明确区分",
        "组织标题、可直接编辑的正文、配图构思与标签",
        "复核活动时间、地址、票价、项目编号等可能造成误导的说法",
    ),
    requirements=(
        "文化事实和体验建议分开表达，避免将虚构活动写成真实举办公告。",
        "标题和正文应贴合用户受众、语气与平台；不得编造官方背书或传播数据。",
        "配图建议只能描述可以自行创作或拍摄的内容，不能声称已有授权素材。",
        "涉及展览、活动、票价、人物及开放状态时标注核验需求。",
    ),
    diagnostic_groups=(("真实性提示", ("核实", "核验", "确认", "为准", "待核实")),),
)

_VIDEO = ScenarioPolicy(
    key="video",
    description="非遗短视频脚本",
    steps=(
        "确定视频受众、时长、主题与文化事实边界",
        "把视觉镜头、镜头时间、解说和字幕一一对应",
        "说明拍摄场景的可获得性，无法确认时提供室内替代方案",
        "检查镜头中有没有虚构访谈、已发生的演出或未经许可的素材",
    ),
    requirements=(
        "60 秒分镜表要有镜头时长、画面、旁白或字幕对应关系，节奏合理。",
        "无实际拍摄条件时以插画、物件特写等可实现画面代替虚构现场演出。",
        "不得杜撰传承人发言、现场视频、采访结果或素材使用授权。",
        "历史和名录事实仅依据可核验内容，活动信息保持不确定性提示。",
    ),
    diagnostic_groups=(
        ("分镜时间描述", ("秒", "时长", "00:", "0-")),
        ("素材与事实核验", ("核实", "授权", "确认", "待核验", "为准")),
    ),
)

_QA = ScenarioPolicy(
    key="qa",
    description="非遗问答",
    steps=(
        "抽取用户的具体问题，判断是在问项目概念、来源、技艺还是体验",
        "优先从与问题直接相关的官方项目记录中组织可确认事实",
        "用简短可理解的语言解释；资料不足时明确未知部分",
        "区分项目文化事实和需要另外确认的场馆、演出、预约信息",
    ),
    requirements=(
        "先正面回答所问问题，再提供背景和体验补充，避免偏离主题。",
        "若项目名录级别、编号、人物、起源年代无直接来源，不能猜测。",
        "资料不足时标注未知或待核验，不能把相邻地区类似项目当同一项目。",
        "必要时说明文化项目资料不是实时活动、开放状态或预约证明。",
    ),
    diagnostic_groups=(("不确定信息提示", ("核实", "核验", "为准", "待确认")),),
)


POLICIES: dict[tuple[str, TaskType], ScenarioPolicy] = {
    ("游客路线", TaskType.ROUTE): _VISITOR,
    ("亲子体验", TaskType.ROUTE): _FAMILY,
    ("学生研学", TaskType.STUDY): _STUDY,
    ("内容创作", TaskType.SOCIAL): _SOCIAL,
    ("内容创作", TaskType.VIDEO): _VIDEO,
    ("非遗问答", TaskType.QA): _QA,
}


def resolve_policy(request: TaskRequest) -> ScenarioPolicy:
    """Reject inconsistent scene/task combinations before an AI call is made."""
    try:
        return POLICIES[(request.scene, request.task_type)]
    except KeyError as exc:
        raise ValueError("场景与任务类型不匹配，请重新选择用途后重试。") from exc


def request_advisories(request: TaskRequest) -> tuple[str, ...]:
    """Missing optional information produces conservative guidance, not a block."""
    policy = resolve_policy(request)
    notes: list[str] = []
    if request.city in {"", "自动判断"} and policy.key in {"visitor_route", "family"}:
        notes.append("未指定城市：不要自行确定地点或通勤顺序；先提供泛化文化建议。")
    if policy.key == "family" and not any(
        marker in request.raw_request for marker in ("岁", "幼儿", "小学生", "初中", "高中", "年龄")
    ):
        notes.append("未说明儿童年龄：选择通用低风险活动，不假定年龄或独立操作技能。")
    if policy.key == "study" and not any(
        marker in request.raw_request for marker in ("年级", "小学", "初中", "高中", "大学", "学段")
    ):
        notes.append("未指定学段：分别给出基础和进阶研学任务，不能臆测学生年级。")
    if policy.key in {"social", "video"} and not any(
        marker in request.raw_request + request.output_style for marker in ("小红书", "公众号", "抖音", "视频号", "B站", "微博")
    ):
        notes.append("未说明发布平台：采用通用创作格式，不冒充平台官方模板。")
    return tuple(notes)


def build_scene_guidance(request: TaskRequest) -> str:
    policy = resolve_policy(request)
    lines = [f"业务场景：{policy.description}", "必须执行的场景要求："]
    lines.extend(f"- {rule}" for rule in policy.requirements)
    notes = request_advisories(request)
    if notes:
        lines.append("输入缺失提醒（应保守处理，不要自行假设）：")
        lines.extend(f"- {item}" for item in notes)
    return "\n".join(lines)


def diagnostic_findings(answer: str, request: TaskRequest) -> tuple[str, ...]:
    """Heuristic reminders for human review, not proof of actual safety."""
    policy = resolve_policy(request)
    body = "\n".join(
        line for line in answer.splitlines() if not line.strip().startswith("#")
    )
    missing = [
        label
        for label, alternatives in policy.diagnostic_groups
        if not any(term in body for term in alternatives)
    ]
    return tuple(missing)
