"""Base primitives for GULA Communication Providers (PROGRAM-COMM-002).

Every provider plugin shares the same cross-cutting machinery:

  - :class:`Redactor` — secret redaction for logs, errors and metrics
  - :class:`TokenBucket` — thread-safe rate limiting
  - :class:`ProviderMetrics` — dependency-free per-provider counters
  - :class:`ProviderSettings` — DI configuration snapshot
  - :class:`BaseChannelProvider` — common ``ChannelProvider`` behaviour:
    circuit breaker, rate limiting, retries, health, cancellation, metrics

The Communication Core (``shared.communication``) is never touched: this
package implements provider-side concerns only.
"""

from __future__ import annotations

import logging
import re
import threading
import time
from dataclasses import dataclass
from typing import Any

from shared.circuit_breaker import CircuitBreaker
from shared.communication.model import (
    ContentFormat,
    OutboundMessage,
    ProviderDeliveryResult,
    Recipient,
)
from shared.communication.providers import ChannelProvider, ProviderHealth, ProviderOptions

logger = logging.getLogger("gula.communication.providers.base")

# Matches common credential shapes so a stray secret can never leak.
_COMMON_SECRET_PATTERNS = (
    re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{30,}\b"),  # telegram bot token
    re.compile(r"\bre_[A-Za-z0-9]{20,}\b"),  # resend api key
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),  # slack tokens
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),  # generic bearer secrets
)


class Redactor:
    """Scrubs registered secrets and common credential shapes from strings.

    Providers register every secret they hold (tokens, webhook URLs with
    embedded credentials) so logs, exceptions and result payloads can never
    contain them.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._secrets: list[str] = []

    def register(self, secret: str) -> None:
        value = (secret or "").strip()
        if len(value) < 4:
            return
        with self._lock:
            if value not in self._secrets:
                self._secrets.append(value)

    def register_many(self, secrets: list[str]) -> None:
        for secret in secrets:
            self.register(secret)

    def redact(self, text: str) -> str:
        """Replace every known secret occurrence with ``[REDACTED]``."""
        out = str(text)
        with self._lock:
            secrets = list(self._secrets)
        for secret in secrets:
            out = out.replace(secret, "[REDACTED]")
        for pattern in _COMMON_SECRET_PATTERNS:
            out = pattern.sub("[REDACTED]", out)
        return out

    def redact_dict(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Redact the string values of a dict (used for request logging)."""
        return {
            key: self.redact(value) if isinstance(value, str) else value
            for key, value in payload.items()
        }


class TokenBucket:
    """Thread-safe smooth token bucket for per-provider rate limiting.

    ``rate_per_minute`` tokens are available initially; the bucket refills
    continuously toward the cap (no burst beyond the cap).
    """

    def __init__(self, rate_per_minute: int) -> None:
        self._max = max(1, int(rate_per_minute))
        self._tokens = float(self._max)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def consume(self, n: int = 1) -> bool:
        """Return True when ``n`` tokens are available (and consume them)."""
        with self._lock:
            now = time.monotonic()
            refill = ((now - self._last_refill) / 60.0) * self._max
            self._tokens = min(float(self._max), self._tokens + refill)
            self._last_refill = now
            if self._tokens < n:
                return False
            self._tokens -= n
            return True


class ProviderMetrics:
    """Thread-safe, dependency-free per-provider counters + latency summary.

    Exposes a Prometheus text exposition fragment through
    :meth:`prometheus` so operators can scrape per-provider health without
    any external metrics library.
    """

    _lock = threading.Lock()

    def __init__(self, provider: str) -> None:
        self._provider = provider
        self._attempts_total: dict[tuple[str, str], int] = {}
        self._failures_total: dict[str, int] = {}
        self._latency_sum = 0.0
        self._latency_count = 0
        self._circuit_open_total = 0
        self._rate_limited_total = 0
        self._cancelled_total = 0
        self._delivered_total = 0

    def record_attempt(self, ok: bool) -> None:
        with self._lock:
            state = "ok" if ok else "fail"
            self._attempts_total[(self._provider, state)] = (
                self._attempts_total.get((self._provider, state), 0) + 1
            )
            if ok:
                self._delivered_total += 1

    def record_failure(self, stage: str) -> None:
        with self._lock:
            self._failures_total[stage] = self._failures_total.get(stage, 0) + 1

    def record_latency(self, seconds: float) -> None:
        with self._lock:
            self._latency_sum += seconds
            self._latency_count += 1

    def record_circuit_open(self) -> None:
        with self._lock:
            self._circuit_open_total += 1

    def record_rate_limited(self) -> None:
        with self._lock:
            self._rate_limited_total += 1

    def record_cancelled(self) -> None:
        with self._lock:
            self._cancelled_total += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "provider": self._provider,
                "attempts_total": dict(self._attempts_total),
                "failures_total": dict(self._failures_total),
                "latency_sum": self._latency_sum,
                "latency_count": self._latency_count,
                "circuit_open_total": self._circuit_open_total,
                "rate_limited_total": self._rate_limited_total,
                "cancelled_total": self._cancelled_total,
                "delivered_total": self._delivered_total,
            }

    def prometheus(self) -> str:
        """Prometheus text exposition fragment for this provider."""
        snap = self.snapshot()
        name = snap["provider"].replace("-", "_")
        lines = [f"# gula_communication_provider: {name}", ""]
        for (provider, state), count in sorted(snap["attempts_total"].items()):
            lines.append(
                f'gula_communication_provider_attempts_total{{provider="{provider}",'
                f'state="{state}"}} {count}',
            )
        count = snap["latency_count"]
        lines.append(
            f"gula_communication_provider_latency_seconds_sum{{provider=\"{name}\"}} "
            f"{round(snap['latency_sum'], 9)}",
        )
        lines.append(
            f"gula_communication_provider_latency_seconds_count{{provider=\"{name}\"}} {count}",
        )
        for stage, cnt in sorted(snap["failures_total"].items()):
            lines.append(
                f'gula_communication_provider_failures_total{{provider="{name}",'
                f'stage="{stage}"}} {cnt}',
            )
        lines.append(
            f"gula_communication_provider_circuit_open_total{{provider=\"{name}\"}} "
            f"{snap['circuit_open_total']}",
        )
        lines.append(
            f"gula_communication_provider_rate_limited_total{{provider=\"{name}\"}} "
            f"{snap['rate_limited_total']}",
        )
        lines.append(
            f"gula_communication_provider_cancelled_total{{provider=\"{name}\"}} "
            f"{snap['cancelled_total']}",
        )
        lines.append(
            f"gula_communication_provider_delivered_total{{provider=\"{name}\"}} "
            f"{snap['delivered_total']}",
        )
        return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class ProviderSettings:
    """DI snapshot of a provider's operational configuration.

    All values may come from env / docker / k8s / cloud secrets; nothing is
    hardcoded in provider code.
    """

    name: str
    channel: str
    timeout_seconds: float = 10.0
    max_retries: int = 2
    backoff_base_seconds: float = 0.5
    backoff_max_seconds: float = 30.0
    rate_per_minute: int = 60
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout: float = 30.0
    enabled: bool = True
    health_probe_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "channel": self.channel,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "rate_per_minute": self.rate_per_minute,
            "circuit_failure_threshold": self.circuit_failure_threshold,
            "circuit_recovery_timeout": self.circuit_recovery_timeout,
            "enabled": self.enabled,
            "health_probe_enabled": self.health_probe_enabled,
        }


def _transient(result: ProviderDeliveryResult) -> bool:
    """A delivery result is retryable when the provider marked it so."""
    return bool(result.retryable)


class BaseChannelProvider(ChannelProvider):
    """Shared behaviour for every GULA communication provider.

    Subclasses implement :meth:`deliver` and optionally the capability
    methods; this base provides the cross-cutting guarantees:

    - circuit breaker around every delivery (``shared.circuit_breaker``)
    - rate limiting (``TokenBucket``)
    - retries with exponential backoff for retryable failures
    - health derived from circuit state + configuration
    - per-provider metrics + Prometheus exposition
    - cancellation tracking for background deliveries
    - secret redaction for every logged error
    """

    name: str
    channel: str

    def __init__(
        self,
        settings: ProviderSettings,
        *,
        redactor: Redactor | None = None,
        circuit_breaker: CircuitBreaker | None = None,
        rate_limiter: TokenBucket | None = None,
        metrics: ProviderMetrics | None = None,
        logger_obj: logging.Logger | None = None,
    ) -> None:
        self._settings = settings
        self.name = settings.name
        self.channel = settings.channel
        self.redactor = redactor or Redactor()
        self._circuit = circuit_breaker or CircuitBreaker(
            name=settings.name,
            failure_threshold=settings.circuit_failure_threshold,
            recovery_timeout=settings.circuit_recovery_timeout,
        )
        self._rate_limiter = rate_limiter or TokenBucket(settings.rate_per_minute)
        self.metrics = metrics or ProviderMetrics(settings.name)
        self._log = logger_obj or logger
        self._cancelled_refs: set[str] = set()
        self._cancel_lock = threading.Lock()

    # ── configuration / DI ─────────────────────────────────────────────────

    @property
    def settings(self) -> ProviderSettings:
        return self._settings

    def register_secret(self, secret: str) -> None:
        """Track a secret so it can never appear in logs or errors."""
        self.redactor.register(secret)

    # ── ChannelProvider interface ──────────────────────────────────────────

    def health(self) -> ProviderHealth:
        if not self._settings.enabled or not self.is_configured:
            return ProviderHealth.DOWN
        if self._circuit.state.value == "OPEN":
            return ProviderHealth.DOWN
        return ProviderHealth.OK

    @property
    def is_configured(self) -> bool:
        """True when the provider has the credentials it needs."""
        return True

    def health_report(self) -> dict[str, Any]:
        """Structured health snapshot for deep checks (metrics endpoints)."""
        return {
            "name": self.name,
            "channel": self.channel,
            "health": self.health().value,
            "configured": self.is_configured,
            "circuit": self._circuit.state.value,
            "metrics": self.metrics.snapshot(),
            "settings": self._settings.to_dict(),
        }

    def cancel(self, delivery_ref: str) -> bool:
        """Cancel a scheduled/background delivery by reference.

        Returns True when the delivery was known and cancelled; a provider
        may only cancel deliveries it has not yet completed.
        """
        with self._cancel_lock:
            if delivery_ref in self._cancelled_refs:
                return False
            self._cancelled_refs.add(delivery_ref)
        self.metrics.record_cancelled()
        self._log.info("communication_provider_cancelled name=%s ref=%s", self.name, delivery_ref)
        return True

    def is_cancelled(self, delivery_ref: str) -> bool:
        with self._cancel_lock:
            return delivery_ref in self._cancelled_refs

    # ── cross-cutting delivery wrapper ─────────────────────────────────────

    def _guard(self, retryable: bool = True) -> bool:
        """True when the delivery may proceed (rate limit + circuit)."""
        if not self._rate_limiter.consume(1):
            self.metrics.record_rate_limited()
            return False
        if not self._circuit.allow_request():
            self.metrics.record_circuit_open()
            return False
        return retryable  # placeholder for subclass hook parity

    def _deliver_protected(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None,
        attempt_fn,
    ) -> ProviderDeliveryResult:
        """Run ``attempt_fn`` with retries + circuit + rate limit + metrics.

        ``attempt_fn`` receives ``(recipient, message, options)`` and must
        return a :class:`ProviderDeliveryResult` (never raise).
        """
        if not self.is_configured:
            return ProviderDeliveryResult(
                success=False,
                channel=self.channel,
                provider=self.name,
                error=self._not_configured_error(),
                retryable=False,
            )
        if not self._rate_limiter.consume(1):
            self.metrics.record_rate_limited()
            return ProviderDeliveryResult(
                success=False,
                channel=self.channel,
                provider=self.name,
                error="rate limit exceeded",
                retryable=True,
            )
        if not self._circuit.allow_request():
            self.metrics.record_circuit_open()
            return ProviderDeliveryResult(
                success=False,
                channel=self.channel,
                provider=self.name,
                error=f"circuit open: {self.name}",
                retryable=False,
            )

        attempts = 0
        last: ProviderDeliveryResult | None = None
        while True:
            attempts += 1
            start = time.monotonic()
            try:
                last = attempt_fn(recipient, message, options)
            except Exception as exc:
                self._circuit.record_failure()
                self.metrics.record_failure("exception")
                error = self.redactor.redact(f"{type(exc).__name__}: {exc}")
                self._log.error(
                    "communication_provider_exception name=%s error_type=%s",
                    self.name,
                    type(exc).__name__,
                )
                last = ProviderDeliveryResult(
                    success=False,
                    channel=self.channel,
                    provider=self.name,
                    error=error,
                    retryable=False,
                )
            self.metrics.record_latency(time.monotonic() - start)
            self.metrics.record_attempt(last.success)
            if last.success:
                self._circuit.record_success()
                return last
            self._circuit.record_failure()
            if not _transient(last) or attempts >= (self._settings.max_retries or 1):
                return last
            delay = min(
                self._settings.backoff_base_seconds * (2 ** (attempts - 1)),
                self._settings.backoff_max_seconds,
            )
            self._log.warning(
                "communication_provider_retry name=%s attempt=%d delay_seconds=%.2f",
                self.name,
                attempts,
                delay,
            )
            time.sleep(delay)

    # ── helpers ────────────────────────────────────────────────────────────

    def _not_configured_error(self) -> str:
        return f"{self.name} not configured (check {self.channel} provider secrets)"

    def _result(
        self,
        *,
        success: bool,
        delivery_ref: str = "",
        error: str | None = None,
        retryable: bool = False,
        latency_ms: float = 0.0,
    ) -> ProviderDeliveryResult:
        return ProviderDeliveryResult(
            success=success,
            channel=self.channel,
            provider=self.name,
            delivery_ref=delivery_ref,
            error=self.redactor.redact(error) if error else None,
            retryable=retryable,
            latency_ms=latency_ms,
        )

    def _default_subject(self, message: OutboundMessage) -> str:
        return message.subject or "GULA notification"

    def _format_name(self, message: OutboundMessage) -> str:
        return message.format.value if isinstance(message.format, ContentFormat) else str(message.format)


__all__ = [
    "BaseChannelProvider",
    "ProviderMetrics",
    "ProviderSettings",
    "Redactor",
    "TokenBucket",
]
