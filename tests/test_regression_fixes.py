from pathlib import Path

from core.models import ModelConfig, TaskRequest, TaskType
from core.revisions import plan_custom_revision
from services.llm import _completion_request_kwargs
from services.retrieval import parse_front_matter, read_text_file
from ui.results import _select_section_content, _split_tab_sections


def _model_config(model_name: str) -> ModelConfig:
    return ModelConfig(
        api_key="test-key",
        base_url="https://api.example.com/v1",
        model_name=model_name,
        credential_source="user",
    )


def test_gpt5_request_uses_reasoning_compatible_parameters() -> None:
    kwargs = _completion_request_kwargs(
        _model_config("gpt-5"),
        [{"role": "user", "content": "hello"}],
        temperature=0.62,
        max_tokens=1600,
        stream=False,
    )

    assert kwargs["max_completion_tokens"] == 1600
    assert "max_tokens" not in kwargs
    assert "temperature" not in kwargs


def test_regular_openai_compatible_model_keeps_standard_parameters() -> None:
    kwargs = _completion_request_kwargs(
        _model_config("qwen-plus"),
        [{"role": "user", "content": "hello"}],
        temperature=0.62,
        max_tokens=1600,
        stream=True,
    )

    assert kwargs["max_tokens"] == 1600
    assert kwargs["temperature"] == 0.62
    assert "max_completion_tokens" not in kwargs


def test_negated_task_keyword_does_not_switch_output_mode() -> None:
    request = TaskRequest(
        scene="游客路线",
        raw_request="广州非遗路线",
        task_type=TaskType.ROUTE,
    )

    plan = plan_custom_revision(request, "不要短视频，只把文字写得简洁一点")

    assert plan.target_task_type == TaskType.ROUTE
    assert plan.revised_request.scene == "游客路线"


def test_tab_sections_keep_h3_content_with_parent_section() -> None:
    markdown = """## 现场任务卡
先观察现场。

### 第一组
记录醒狮动作。

## 报告提纲
整理观察结论。
"""

    sections = _split_tab_sections(markdown)
    task_content = _select_section_content(sections, ("任务",), markdown)

    assert sections[0][0] == "现场任务卡"
    assert "### 第一组" in sections[0][1]
    assert "记录醒狮动作" in task_content


def test_utf8_bom_front_matter_is_parsed(tmp_path: Path) -> None:
    path = tmp_path / "bom.md"
    path.write_bytes(
        "---\ntitle: 粤剧\ncity: 广州\ncategory: 传统戏剧\n---\n# 粤剧\n内容".encode(
            "utf-8-sig"
        )
    )

    text = read_text_file(path)
    metadata, body = parse_front_matter(text)

    assert text.startswith("---")
    assert metadata["city"] == "广州"
    assert metadata["category"] == "传统戏剧"
    assert "# 粤剧" in body
