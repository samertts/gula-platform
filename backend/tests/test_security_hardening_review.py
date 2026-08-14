from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from app.routes import metrics
from app.security import rate_limit


def test_prometheus_metrics_fails_closed_without_production_bearer(monkeypatch) -> None:
    monkeypatch.setattr(metrics, "IS_PRODUCTION", True)
    monkeypatch.delenv("METRICS_BEARER_TOKEN", raising=False)

    request = SimpleNamespace(headers={})
    response = metrics.prometheus_metrics(request, db=Mock())

    assert response.status_code == 503
    assert response.body == b"Metrics authentication is not configured"


def test_auth_identifier_rate_limit_key_is_hmac_and_does_not_contain_identifier(monkeypatch) -> None:
    seen_keys: list[str] = []

    def allow(key: str, max_requests: int, window_seconds: int, request=None):
        seen_keys.append(key)
        return True, max_requests, 0

    monkeypatch.setattr(rate_limit, "_check", allow)
    monkeypatch.setenv("NID_HMAC_KEY", "n" * 64)
    request = SimpleNamespace(
        client=SimpleNamespace(host="198.51.100.10"),
        headers={},
    )

    rate_limit.rate_limit_auth(request, identifier="Person@example.com")

    assert len(seen_keys) == 2
    assert seen_keys[0].startswith("auth:")
    assert seen_keys[1].startswith("auth-id:")
    assert all("person@example.com" not in key for key in seen_keys)
    assert all("@" not in key for key in seen_keys)
    assert len(seen_keys[1].split(":", 1)[1]) == 64


def test_public_health_diagnostics_do_not_format_raw_exception_text() -> None:
    from pathlib import Path

    source = (Path(__file__).parents[1] / "app" / "main.py").read_text()

    assert "db_error = str(e)" not in source
    assert "redis_error = str(e)" not in source
    assert "db_err = str(e)" not in source
    assert "red_err = str(e)" not in source
    assert "queue_err = str(e)" not in source
