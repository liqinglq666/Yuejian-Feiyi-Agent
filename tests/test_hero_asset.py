from pathlib import Path

from ui.components import ASSET_DIR, asset_data_uri


def test_hero_asset_can_be_embedded_as_webp_data_uri() -> None:
    uri = asset_data_uri("hero_lingnan_agent.webp")

    assert uri.startswith("data:image/webp;base64,")
    assert len(uri) > 1_000


def test_readme_hero_is_a_real_webp_image() -> None:
    data = (ASSET_DIR / "readme_hero_lingnan.webp").read_bytes()

    assert data[:4] == b"RIFF"
    assert data[8:12] == b"WEBP"
    assert len(data) > 10_000


def test_readme_uses_the_valid_hero_asset() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "assets/readme_hero_lingnan.webp" in readme
