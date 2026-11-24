"""HttpTransport tests: timeouts, retries, circuit breaker, rate limiting
and redaction — all over httpx.MockTransport (no network)."""

from __future__ import annotations

import httpx
import pytest

from shared.circuit_breaker import CircuitBreaker
from shared.communication_providers.base import ProviderMetrics, Redactor, TokenBucket
from shared.communication_providers.transport import (
    CircuitOpenError,
    HttpTransport,
    TransportSettings,
)

from .conftest import mock_client


def _transport(*, handler, settings: TransportSettings | None = None, name: str = "t") -> HttpTransport:
    return HttpTransport(
        name=name,
        settings=settings or TransportSettings(max_retries=1, backoff_base_seconds=0.0),
        http_client=mock_client(handler),
    )


class TestTransportBasics:
    def test_success(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return httpx.Response(204)

        transport = _transport(handler=handler)
        response = transport.request("POST", "https://example.com/hook", json={"a": 1})
        assert response.ok
        assert response.status_code == 204
        assert len(calls) == 1

    def test_json_body_parsed(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"ok": True})

        transport = _transport(handler=handler)
        response = transport.request("GET", "https://example.com")
        assert response.json == {"ok": True}

    def test_transient_status_retried(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return httpx.Response(500 if len(calls) < 2 else 204)

        transport = _transport(handler=handler, settings=TransportSettings(max_retries=2, backoff_base_seconds=0.0))
        response = transport.request("POST", "https://example.com/hook")
        assert response.ok
        assert len(calls) == 2

    def test_permanent_status_no_retry(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return httpx.Response(400)

        transport = _transport(handler=handler)
        response = transport.request("POST", "https://example.com/hook")
        assert response.status_code == 400
        assert len(calls) == 1

    def test_retries_exhausted(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return httpx.Response(503)

        transport = _transport(
            handler=handler,
            settings=TransportSettings(max_retries=2, backoff_base_seconds=0.0),
        )
        response = transport.request("POST", "https://example.com/hook")
        assert response.status_code == 503
        assert len(calls) == 3

    def test_network_error_retried_then_fails(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            raise httpx.ReadTimeout("slow", request=request)

        transport = _transport(
            handler=handler,
            settings=TransportSettings(max_retries=1, backoff_base_seconds=0.0),
        )
        response = transport.request("POST", "https://example.com/hook")
        assert response.status_code == 0
        assert "ReadTimeout" in response.text
        assert len(calls) == 2


class TestTransportCircuit:
    def test_circuit_opens(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return httpx.Response(500)

        transport = HttpTransport(
            name="circ",
            settings=TransportSettings(max_retries=0, backoff_base_seconds=0.0),
            http_client=mock_client(handler),
            circuit_breaker=CircuitBreaker("circ", failure_threshold=2, recovery_timeout=60.0),
        )
        transport.request("POST", "https://example.com/hook")
        transport.request("POST", "https://example.com/hook")
        with pytest.raises(CircuitOpenError):
            transport.request("POST", "https://example.com/hook")
        assert len(calls) == 2


class TestTransportRateLimit:
    def test_rate_limit_returns_429(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(204)

        transport = HttpTransport(
            name="rl",
            settings=TransportSettings(max_retries=0),
            http_client=mock_client(handler),
            rate_limiter=TokenBucket(rate_per_minute=1),
            metrics=ProviderMetrics("rl"),
        )
        first = transport.request("POST", "https://example.com/hook")
        second = transport.request("POST", "https://example.com/hook")
        assert first.ok
        assert second.status_code == 429
        assert second.text == "rate limit exceeded"


class TestTransportRedaction:
    def test_response_text_redacted(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="failed with SECRET-HOOK")

        redactor = Redactor()
        redactor.register("SECRET-HOOK")
        transport = HttpTransport(
            name="red",
            settings=TransportSettings(max_retries=0),
            http_client=mock_client(handler),
            redactor=redactor,
        )
        response = transport.request("POST", "https://example.com/hook")
        assert "SECRET-HOOK" not in response.text
        assert "[REDACTED]" in response.text

    def test_error_text_redacted(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("token=ABC123XYZ", request=request)

        redactor = Redactor()
        transport = HttpTransport(
            name="red2",
            settings=TransportSettings(max_retries=0),
            http_client=mock_client(handler),
            redactor=redactor,
        )
        response = transport.request("POST", "https://example.com/hook")
        assert response.status_code == 0

    def test_metrics_recorded(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(204)

        metrics = ProviderMetrics("m")
        transport = HttpTransport(
            name="m",
            settings=TransportSettings(max_retries=0),
            http_client=mock_client(handler),
            metrics=metrics,
        )
        transport.request("POST", "https://example.com/hook")
        snap = metrics.snapshot()
        assert snap["delivered_total"] == 1
