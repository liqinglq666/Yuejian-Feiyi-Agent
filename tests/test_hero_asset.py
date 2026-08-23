from __future__ import annotations

import struct
from pathlib import Path

from ui.components import ASSET_DIR, asset_data_uri


def test_hero_asset_can_be_embedded_as_png_data_uri() -> None:
    """网页 Hero 应当可以正常读取唯一的 PNG 图片。"""
    uri = asset_data_uri("readme_hero_lingnan.png")

    assert uri.startswith("data:image/png;base64,")
    assert len(uri) > 10_000


def test_hero_is_a_real_png_image() -> None:
    """Hero 图片必须是真实且尺寸合理的 PNG 文件。"""
    image_path = ASSET_DIR / "readme_hero_lingnan.png"

    assert image_path.is_file()

    data = image_path.read_bytes()

    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(data) > 10_000

    width, height = struct.unpack(">II", data[16:24])

    assert width >= 1_000
    assert height >= 500


def test_readme_uses_the_png_hero_asset() -> None:
    """README 和在线网页应使用同一张 PNG 图片。"""
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "./assets/readme_hero_lingnan.png" in readme
    assert "https://yuejian-feiyi-agent.streamlit.app/" in readme


def test_old_hero_assets_are_not_referenced() -> None:
    """代码与 README 不应继续引用已经删除的旧图片。"""
    readme = Path("README.md").read_text(encoding="utf-8")
    components = Path("ui/components.py").read_text(encoding="utf-8")

    combined = readme + components

    assert "hero_lingnan_agent.webp" not in combined
    assert "readme_hero_lingnan.webp" not in combined
    assert "hero_feiyi.png" not in combined
