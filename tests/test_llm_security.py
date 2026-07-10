import pytest

from services.llm import ModelGatewayError, validate_base_url


def test_https_public_url_is_accepted_without_dns_lookup() -> None:
    assert (
        validate_base_url("https://api.example.com/v1/", resolve_dns=False)
        == "https://api.example.com/v1"
    )


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com/v1",
        "https://user:pass@example.com/v1",
        "https://example.com/v1?token=secret",
        "not-a-url",
    ],
)
def test_invalid_gateway_urls_are_rejected(url: str) -> None:
    with pytest.raises(ModelGatewayError):
        validate_base_url(url, resolve_dns=False)
