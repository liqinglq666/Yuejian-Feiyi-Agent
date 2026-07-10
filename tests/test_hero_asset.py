from ui.components import asset_data_uri


def test_hero_asset_can_be_embedded_as_webp_data_uri() -> None:
    uri = asset_data_uri("hero_lingnan_agent.webp")

    assert uri.startswith("data:image/webp;base64,")
    assert len(uri) > 1_000
