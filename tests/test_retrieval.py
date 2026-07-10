from pathlib import Path

from services.retrieval import clear_cache, retrieve


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_hybrid_retrieval_prefers_city_and_domain_match(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write(
        data_dir / "guangzhou_yueju.md",
        """---
title: 粤剧体验
city: 广州
category: 传统戏剧
source_name: 测试文化资料
source_url: https://example.com/yueju
---
# 粤剧
粤剧是岭南地区具有代表性的传统戏剧，广州有相关场馆与文化展示。
""",
    )
    _write(
        data_dir / "foshan_pottery.md",
        """---
title: 石湾陶塑
city: 佛山
category: 传统美术
---
# 石湾陶塑
石湾陶塑与佛山陶瓷文化相关，适合亲子手作体验。
""",
    )

    clear_cache()
    result = retrieve("广州一天粤剧体验", data_dir=data_dir, top_k=1)
    assert not result.is_empty
    assert result.chunks[0].city == "广州"
    assert "粤剧" in result.chunks[0].content
    assert "[S1]" in result.formatted_context()


def test_retrieval_returns_warning_for_unmatched_query(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write(data_dir / "sample.md", "# 醒狮\n醒狮是岭南民俗活动。")

    clear_cache()
    result = retrieve("量子计算芯片", data_dir=data_dir)
    assert result.is_empty
    assert result.warnings
