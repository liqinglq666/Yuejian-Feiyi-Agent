from __future__ import annotations

from pathlib import Path

from ui.components import asset_data_uri
from ui.editorial_styles import EDITORIAL_CSS
from ui.workspace import _workspace_aside_markup


def test_editorial_design_has_accessible_responsive_fallbacks() -> None:
    assert "prefers-reduced-motion" in EDITORIAL_CSS
    assert "@media(max-width:640px)" in EDITORIAL_CSS
    assert ":focus-visible" in EDITORIAL_CSS
    assert "--forest:" in EDITORIAL_CSS
    assert "--cinnabar:" in EDITORIAL_CSS


def test_hero_uses_existing_local_heritage_art() -> None:
    assert asset_data_uri("readme_hero_lingnan.png").startswith("data:image/png;base64,")
    markup = Path("ui/components.py").read_text(encoding="utf-8")
    assert 'class="editorial-hero"' in markup
    assert 'alt="岭南非遗主题插画' in markup
    assert "<script" not in markup


def test_customized_aside_escapes_user_facing_values() -> None:
    markup = _workspace_aside_markup(
        "内容创作",
        "<script>alert(1)</script>",
        "一天",
        "内容创作者",
        "短视频",
        "已连接",
    )
    assert "&lt;script&gt;" in markup
    assert "<script>" not in markup
    assert "🎬 短视频" in markup
