from services.output import sanitize_model_output


def test_sanitize_model_output_removes_html_and_empty_numbers() -> None:
    raw = "# 标题\n\n4.\n\n- \n内容<br>下一项"
    cleaned = sanitize_model_output(raw)
    assert cleaned.startswith("## 标题")
    assert "4." not in cleaned
    assert "<br>" not in cleaned
    assert "内容；下一项" in cleaned
