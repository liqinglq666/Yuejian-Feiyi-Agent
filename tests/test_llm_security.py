import pytest

from services import llm
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


def test_platform_allowlist_is_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_ALLOWED_HOSTS", "dashscope.aliyuncs.com")

    with pytest.raises(ModelGatewayError, match="允许列表"):
        validate_base_url("https://api.deepseek.com", resolve_dns=False)


def test_byok_can_use_public_host_outside_platform_allowlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_ALLOWED_HOSTS", "dashscope.aliyuncs.com")

    assert (
        validate_base_url(
            "https://api.deepseek.com",
            resolve_dns=False,
            enforce_server_allowlist=False,
        )
        == "https://api.deepseek.com"
    )


def test_byok_still_rejects_non_https_url() -> None:
    with pytest.raises(ModelGatewayError, match="HTTPS"):
        validate_base_url(
            "http://example.com/v1",
            resolve_dns=False,
            enforce_server_allowlist=False,
        )


def test_platform_dns_validation_can_reuse_short_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, int]] = []

    def fake_resolve(host: str, port: int) -> tuple[str, ...]:
        calls.append((host, port))
        return ("93.184.216.34",)

    monkeypatch.setattr(llm, "_resolve_public_addresses", fake_resolve)
    llm._resolve_public_addresses_cached.cache_clear()

    for _ in range(2):
        validate_base_url(
            "https://api.example.com/v1",
            enforce_server_allowlist=False,
            cache_dns=True,
        )

    assert calls == [("api.example.com", 443)]


def test_uncached_dns_validation_still_resolves_every_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, int]] = []

    def fake_resolve(host: str, port: int) -> tuple[str, ...]:
        calls.append((host, port))
        return ("93.184.216.34",)

    monkeypatch.setattr(llm, "_resolve_public_addresses", fake_resolve)

    for _ in range(2):
        validate_base_url(
            "https://api.example.com/v1",
            enforce_server_allowlist=False,
            cache_dns=False,
        )

    assert calls == [
        ("api.example.com", 443),
        ("api.example.com", 443),
    ]
