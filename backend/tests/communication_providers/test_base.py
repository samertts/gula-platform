"""Base-layer tests: redaction, rate limiting, metrics, circuit breaking,
retries, health and cancellation (PROGRAM-COMM-002)."""

from __future__ import annotations

from shared.circuit_breaker import CircuitBreaker
from shared.communication.model import OutboundMessage, Recipient
from shared.communication.providers import ProviderHealth, ProviderOptions
from shared.communication_providers.base import (
    BaseChannelProvider,
    ProviderMetrics,
    ProviderSettings,
    Redactor,
    TokenBucket,
)

from .conftest import delivery_result, make_message, options


class _EchoProvider(BaseChannelProvider):
    """Test provider whose attempt_fn can be swapped per test."""

    def __init__(self, settings: ProviderSettings, **kwargs: object) -> None:
        super().__init__(settings, **kwargs)
        self.calls = 0

    @property
    def is_configured(self) -> bool:
        return True

    def deliver(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> object:
        self.calls += 1
        return self._deliver_protected(recipient, message, options, self._attempt)

    def _attempt(self, recipient: Recipient, message: OutboundMessage, opts: ProviderOptions | None) -> object:
        return delivery_result(True)


class TestRedactor:
    def test_redacts_registered_secret(self):
        redactor = Redactor()
        redactor.register("supersecret-token")
        assert redactor.redact("url with supersecret-token inside") == "url with [REDACTED] inside"

    def test_redacts_common_credential_shapes(self):
        redactor = Redactor()
        assert "123456:abcdefghijklmnopqrstuvwxyz123456" not in redactor.redact(
            "token 123456:abcdefghijklmnopqrstuvwxyz123456",
        )
        assert "re_abcdefghijklmnopqrstuvwxyz123" not in redactor.redact("key re_abcdefghijklmnopqrstuvwxyz123")

    def test_short_secrets_not_registered(self):
        redactor = Redactor()
        redactor.register("ab")
        assert "ab" in redactor.redact("keep ab")

    def test_redact_dict_values(self):
        redactor = Redactor()
        redactor.register("token123")
        out = redactor.redact_dict({"Authorization": "Bearer token123", "count": 3})
        assert out["Authorization"] == "Bearer [REDACTED]"
        assert out["count"] == 3


class TestTokenBucket:
    def test_consumes_tokens(self):
        bucket = TokenBucket(rate_per_minute=2)
        assert bucket.consume() is True
        assert bucket.consume() is True
        assert bucket.consume() is False

    def test_refills_over_time(self):
        import time

        bucket = TokenBucket(rate_per_minute=120)
        assert bucket.consume(120) is True
        time.sleep(0.6)
        assert bucket.consume(1) is True


class TestProviderMetrics:
    def test_snapshot_and_prometheus(self):
        metrics = ProviderMetrics("discord")
        metrics.record_attempt(True)
        metrics.record_attempt(False)
        metrics.record_latency(0.5)
        metrics.record_circuit_open()
        snap = metrics.snapshot()
        assert snap["delivered_total"] == 1
        assert snap["circuit_open_total"] == 1
        exposition = metrics.prometheus()
        assert 'provider="discord"' in exposition
        assert "gula_communication_provider_attempts_total" in exposition

    def test_thread_safe(self):
        import threading

        metrics = ProviderMetrics("x")
        threads = [threading.Thread(target=lambda: [metrics.record_attempt(True) for _ in range(50)]) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert metrics.snapshot()["delivered_total"] == 200


class TestBaseProviderRetry:
    def test_retries_retryable_failures_then_succeeds(self):
        settings = ProviderSettings(name="t", channel="t", max_retries=2, backoff_base_seconds=0.0)
        provider = _EchoProvider(settings)
        calls = []

        def attempt(r, m, o):
            calls.append(1)
            first = len(calls) < 2
            return delivery_result(not first, retryable=first)

        provider._attempt = attempt  # type: ignore[method-assign]
        result = provider.deliver(Recipient("a"), make_message())
        assert result.success is True
        assert len(calls) == 2

    def test_non_retryable_failure_stops(self):
        settings = ProviderSettings(name="t", channel="t", max_retries=3, backoff_base_seconds=0.0)
        provider = _EchoProvider(settings)
        calls = []

        def attempt(r, m, o):
            calls.append(1)
            return delivery_result(False, retryable=False, error="permanent")

        provider._attempt = attempt  # type: ignore[method-assign]
        result = provider.deliver(Recipient("a"), make_message())
        assert result.success is False
        assert result.error == "permanent"
        assert len(calls) == 1

    def test_exception_marked_failure_and_redacted(self):
        settings = ProviderSettings(name="t", channel="t", max_retries=1, backoff_base_seconds=0.0)
        provider = _EchoProvider(settings)
        provider.register_secret("TOP-SECRET")

        def attempt(r, m, o):
            raise RuntimeError("boom with TOP-SECRET")

        provider._attempt = attempt  # type: ignore[method-assign]
        result = provider.deliver(Recipient("a"), make_message())
        assert result.success is False
        assert "TOP-SECRET" not in (result.error or "")
        assert provider.metrics.snapshot()["failures_total"].get("exception") == 1


class TestBaseProviderCircuit:
    def test_circuit_opens_after_threshold(self):
        settings = ProviderSettings(
            name="t",
            channel="t",
            max_retries=0,
            circuit_failure_threshold=2,
            circuit_recovery_timeout=60.0,
        )
        provider = _EchoProvider(
            settings,
            circuit_breaker=CircuitBreaker("t", failure_threshold=2, recovery_timeout=60.0),
        )

        def attempt(r, m, o):
            return delivery_result(False, error="fail")

        provider._attempt = attempt  # type: ignore[method-assign]
        provider.deliver(Recipient("a"), make_message())
        provider.deliver(Recipient("a"), make_message())
        assert provider.health() == ProviderHealth.DOWN
        result = provider.deliver(Recipient("a"), make_message())
        assert result.success is False
        assert "circuit" in (result.error or "")

    def test_success_recloses(self):
        settings = ProviderSettings(
            name="t",
            channel="t",
            max_retries=0,
            circuit_failure_threshold=1,
            circuit_recovery_timeout=60.0,
        )
        provider = _EchoProvider(
            settings,
            circuit_breaker=CircuitBreaker("t", failure_threshold=1, recovery_timeout=60.0),
        )
        provider._attempt = lambda r, m, o: delivery_result(False, error="x")  # type: ignore[method-assign]
        provider.deliver(Recipient("a"), make_message())
        assert provider.health() == ProviderHealth.DOWN
        provider._attempt = lambda r, m, o: delivery_result(True)  # type: ignore[method-assign]
        provider._circuit.reset()
        assert provider.health() == ProviderHealth.OK


class TestBaseProviderRateLimit:
    def test_rate_limit_blocks(self):
        settings = ProviderSettings(name="t", channel="t", rate_per_minute=1, max_retries=0)
        provider = _EchoProvider(settings)
        first = provider.deliver(Recipient("a"), make_message())
        second = provider.deliver(Recipient("a"), make_message())
        assert first.success is True
        assert second.success is False
        assert "rate limit" in (second.error or "")
        assert provider.metrics.snapshot()["rate_limited_total"] == 1


class TestBaseProviderHealthAndCancel:
    def test_health_down_when_disabled(self):
        settings = ProviderSettings(name="t", channel="t", enabled=False)
        provider = _EchoProvider(settings)
        assert provider.health() == ProviderHealth.DOWN

    def test_cancel_lifecycle(self):
        settings = ProviderSettings(name="t", channel="t")
        provider = _EchoProvider(settings)
        assert provider.cancel("ref-1") is True
        assert provider.is_cancelled("ref-1") is True
        assert provider.cancel("ref-1") is False
        assert provider.metrics.snapshot()["cancelled_total"] == 1

    def test_health_report_shape(self):
        settings = ProviderSettings(name="t", channel="t")
        provider = _EchoProvider(settings)
        report = provider.health_report()
        assert report["name"] == "t"
        assert report["health"] == "ok"
        assert "metrics" in report
        assert "settings" in report

    def test_result_redacts_errors(self):
        settings = ProviderSettings(name="t", channel="t")
        provider = _EchoProvider(settings)
        provider.register_secret("HIDDEN-API-KEY")
        result = provider._result(success=False, error="failed with HIDDEN-API-KEY")
        assert "HIDDEN-API-KEY" not in (result.error or "")


class TestProviderSettings:
    def test_serialisable(self):
        settings = ProviderSettings(name="x", channel="y")
        data = settings.to_dict()
        assert data["name"] == "x"
        assert data["channel"] == "y"
        assert "timeout_seconds" in data
        assert "enabled" in data
