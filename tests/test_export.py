from core.models import TaskRequest
from services.export import build_plain_text


def test_plain_text_export_removes_markdown_heading_markers() -> None:
    request = TaskRequest(scene="非遗问答", raw_request="介绍粤剧")
    answer = "## 一句话认识\n粤剧。\n\n### 核心看点\n- 唱腔"
    text = build_plain_text(request, answer, "### 本次检索资料\n- 项目知识库 · 粤剧")

    assert "# 粤见非遗生成结果" not in text
    assert "## 一句话认识" not in text
    assert "### 核心看点" not in text
    assert "一句话认识" in text
    assert "核心看点" in text
