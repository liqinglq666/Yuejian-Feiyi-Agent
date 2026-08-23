from pathlib import Path

from services.retrieval import clear_cache, get_index, retrieve


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
    assert "[S1]" not in result.formatted_context()
    assert "[S1]" not in result.source_markdown()
    assert "测试文化资料" in result.source_markdown()


def test_multi_city_markdown_infers_city_from_heading_hierarchy(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write(
        data_dir / "routes.md",
        """# 广东路线库

## 广州非遗路线
### 粤剧体验
在园林与展陈中认识粤剧服饰和唱腔。

## 佛山非遗路线
### 醒狮体验
观察南狮动作、鼓点与采青，并了解武术基础。
""",
    )

    clear_cache()
    index = get_index(data_dir)
    foshan_chunks = [
        chunk
        for chunk in index.chunks
        if "醒狮" in chunk.title or "醒狮" in chunk.content
    ]
    assert foshan_chunks
    assert all(chunk.city == "佛山" for chunk in foshan_chunks)

    result = retrieve("佛山醒狮体验", data_dir=data_dir, top_k=1)
    assert not result.is_empty
    assert result.chunks[0].city == "佛山"
    assert "醒狮" in (result.chunks[0].title + result.chunks[0].content)


def test_retrieval_returns_warning_for_unmatched_query(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write(data_dir / "sample.md", "# 醒狮\n醒狮是岭南民俗活动。")

    clear_cache()
    result = retrieve("量子计算芯片", data_dir=data_dir)
    assert result.is_empty
    assert result.warnings
