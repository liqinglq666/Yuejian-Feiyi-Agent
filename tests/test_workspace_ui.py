from ui.workspace import _workspace_aside_markup


def test_workspace_aside_markup_is_single_block_without_markdown_code_indentation() -> None:
    markup = _workspace_aside_markup(
        "游客路线",
        "广州",
        "一天",
        "外地游客",
        "图文",
        "当前使用平台 API",
    )

    assert "\n" not in markup
    assert '<div class="workspace-aside">' in markup
    assert '<div class="aside-list">' in markup
    assert "当前使用平台 API" in markup
    assert "<code" not in markup


def test_workspace_aside_only_shows_content_format_for_content_creation() -> None:
    route_markup = _workspace_aside_markup(
        "游客路线",
        "广州",
        "一天",
        "外地游客",
        "短视频",
        "当前使用平台 API",
    )
    content_markup = _workspace_aside_markup(
        "内容创作",
        "汕头",
        "不限",
        "内容创作者",
        "短视频",
        "当前使用平台 API",
    )

    assert "🎬 短视频" not in route_markup
    assert "🎬 短视频" in content_markup
