from core.state import start_new_plan
from ui.results import split_markdown_sections
from ui.workspace import EXAMPLES, apply_example, select_scene


def test_split_markdown_sections_preserves_task_blocks() -> None:
    markdown = """开场说明

## 方案总览
适合一天体验。

## 行程时间轴
09:00 出发。

### 上午节点
参观粤剧相关展陈。
"""

    sections = split_markdown_sections(markdown)

    assert sections[0] == ("方案概览", "开场说明")
    assert sections[1] == ("方案总览", "适合一天体验。")
    assert sections[2] == ("行程时间轴", "09:00 出发。")
    assert sections[3] == ("上午节点", "参观粤剧相关展陈。")


def test_select_scene_updates_state_without_widget_mutation() -> None:
    state = {"selected_scene": "游客路线"}
    select_scene(state, "内容创作")
    assert state["selected_scene"] == "内容创作"


def test_example_updates_all_structured_conditions() -> None:
    state: dict = {
        "selected_scene": "亲子体验",
        "selected_city": "佛山",
        "selected_duration": "周末",
        "selected_identity": "亲子家庭",
        "selected_interests": ["醒狮"],
        "output_style": "游客友好",
    }
    preset = EXAMPLES["广州一日路线"]

    apply_example(
        state,
        preset.scene,
        preset.text,
        preset.city,
        preset.duration,
        preset.identity,
        preset.interests,
        preset.output_style,
    )

    assert state["selected_scene"] == "游客路线"
    assert state["selected_city"] == "广州"
    assert state["selected_duration"] == "一天"
    assert state["selected_identity"] == "外地游客"
    assert state["selected_interests"] == ["非遗", "拍照", "研学"]
    assert state["output_style"] == "游客友好"


def test_start_new_plan_resets_workspace_and_keeps_recent_plans() -> None:
    state = {
        "selected_scene": "内容创作",
        "user_input": "旧需求",
        "selected_city": "广州",
        "selected_duration": "一天",
        "selected_identity": "内容创作者",
        "selected_interests": ["粤剧"],
        "custom_revision": "缩短",
        "pending_job": {"kind": "initial"},
        "root_request": {"scene": "内容创作"},
        "current_answer": "旧答案",
        "current_sources": "旧来源",
        "revision_history": [{"instruction": "缩短"}],
        "recent_plans": [{"title": "保留的方案"}],
        "active_plan_id": "old-plan",
    }

    start_new_plan(state)

    assert state["selected_scene"] == "游客路线"
    assert state["user_input"] == ""
    assert state["selected_city"] == "自动判断"
    assert state["selected_duration"] == "自动判断"
    assert state["selected_identity"] == "自动匹配"
    assert state["selected_interests"] == []
    assert state["current_answer"] == ""
    assert state["active_plan_id"] is None
    assert state["recent_plans"] == [{"title": "保留的方案"}]
