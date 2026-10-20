from pathlib import Path


def test_homepage_hero_is_valid_webp() -> None:
    image = Path("web/public/heritage/lingnan-festival-hero-desktop.webp")
    assert image.is_file()
    data = image.read_bytes()
    assert len(data) > 10_000
    assert data[:4] == b"RIFF"
    assert data[8:12] == b"WEBP"


def test_readme_and_homepage_reference_current_hero() -> None:
    page = Path("web/app/page.tsx").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    assert 'src="/heritage/lingnan-festival-hero-desktop.webp"' in page
    assert "./web/public/heritage/lingnan-festival-hero-desktop.webp" in readme
