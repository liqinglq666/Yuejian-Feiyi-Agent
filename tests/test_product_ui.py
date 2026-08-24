from pathlib import Path

import pytest

from core.config import debug_ui_enabled
from ui.sidebar import MODE_LABELS, MODE_VALUES


def test_debug_ui_is_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEBUG_UI", raising=False)
    assert debug_ui_enabled() is False

    monkeypatch.setenv("DEBUG_UI", "true")
    assert debug_ui_enabled() is True


def test_sidebar_uses_product_facing_service_modes() -> None:
    assert MODE_LABELS == {
        "自动使用": "auto",
        "使用我的 API": "user",
    }
    assert MODE_VALUES["platform"] == "自动使用"
    assert "平台 API" not in MODE_LABELS


def test_normal_generation_copy_is_business_facing() -> None:
    source = Path("app.py").read_text(encoding="utf-8")

    assert 'request_line.markdown("✓ 已理解你的需求")' in source
    assert 'retrieval_line.markdown("✓ 已整理相关非遗资料")' in source
    assert 'model_line.markdown("◌ 正在生成专属方案…")' in source
    assert 'model_line.markdown("✓ 专属方案已生成")' in source


def test_build_information_is_guarded_by_debug_mode() -> None:
    source = Path("app.py").read_text(encoding="utf-8")
    guarded = (
        'if debug_ui_enabled():\n'
        '        st.sidebar.caption(f"Build {APP_BUILD_ID} · UI {WORKSPACE_UI_BUILD_ID}")'
    )
    assert guarded in source
