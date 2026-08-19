import pytest
from app.identity.federation.security import (
    validate_endpoint_url,
    validate_redirect_uris,
)


def test_localhost_urls_are_allowed_only_in_development(monkeypatch) -> None:
    monkeypatch.setenv("ENV", "test")
    monkeypatch.delenv("FEDERATION_ALLOWED_HOSTS", raising=False)

    assert validate_endpoint_url("http://localhost:8080/issuer", "issuer_url") == (
        "http://localhost:8080/issuer"
    )
    assert validate_redirect_uris(["http://127.0.0.1:3000/callback"]) == [
        "http://127.0.0.1:3000/callback"
    ]


def test_production_requires_https_and_explicit_allowlist(monkeypatch) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("FEDERATION_ALLOWED_HOSTS", "idp.example.org")

    assert validate_endpoint_url("https://idp.example.org/issuer", "issuer_url") == (
        "https://idp.example.org/issuer"
    )
    with pytest.raises(ValueError, match="HTTPS"):
        validate_endpoint_url("http://idp.example.org/issuer", "issuer_url")
    with pytest.raises(ValueError, match="FEDERATION_ALLOWED_HOSTS"):
        validate_endpoint_url("https://other.example.org/issuer", "issuer_url")


def test_federation_urls_reject_ssrf_and_ambiguous_oauth_targets(monkeypatch) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("FEDERATION_ALLOWED_HOSTS", "idp.example.org")

    for value in (
        "https://user:pass@idp.example.org/issuer",
        "https://idp.example.org/callback#fragment",
        "https://idp.example.org/*",
        "https://127.0.0.1/issuer",
        "https://169.254.169.254/latest/meta-data",
        "https://metadata.google.internal/computeMetadata/v1",
    ):
        with pytest.raises(ValueError):
            validate_endpoint_url(value, "issuer_url")

    with pytest.raises(ValueError, match=r"redirect_uris\[0\]"):
        validate_redirect_uris(["https://idp.example.org/callback#fragment"])


def test_redirect_uri_list_is_bounded_and_exact(monkeypatch) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("FEDERATION_ALLOWED_HOSTS", "idp.example.org")

    callback = "https://idp.example.org/oauth/callback"
    assert validate_redirect_uris([callback, callback]) == [callback, callback]
    with pytest.raises(ValueError, match="20"):
        validate_redirect_uris([callback] * 21)
