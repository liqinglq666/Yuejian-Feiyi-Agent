from services.output import sanitize_model_output


def test_sanitize_model_output_removes_html_and_empty_numbers() -> None:
    raw = "# 标题\n\n4.\n\n- \n内容<br>下一项"
    cleaned = sanitize_model_output(raw)
    assert cleaned.startswith("## 标题")
    assert "4." not in cleaned
    assert "<br>" not in cleaned
    assert "内容；下一项" in cleaned


def test_sanitize_model_output_removes_source_markers() -> None:
    raw = "粤剧是岭南文化的重要组成部分。[S1]\n醒狮适合亲子观察。[S2] [s3]"
    cleaned = sanitize_model_output(raw)
    assert "[S1]" not in cleaned
    assert "[S2]" not in cleaned
    assert "[s3]" not in cleaned
    assert "粤剧是岭南文化的重要组成部分。" in cleaned
    assert "醒狮适合亲子观察。" in cleaned
