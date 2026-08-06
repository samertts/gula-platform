"""HTTP transport for GULA Communication Providers (PROGRAM-COMM-002).

A uniform, provider-agnostic transport built on ``httpx`` with:

  - bounded timeouts (per-call override supported)
  - transient-failure retries with exponential backoff
  - circuit breaker (``shared.circuit_breaker``)
  - rate limiting (``TokenBucket``)
  - secret redaction of URLs, headers and bodies for every log message
  - latency + outcome metrics (``ProviderMetrics``)

Providers construct a :class:`HttpTransport` with their credentials and
call :meth:`request`; all cross-cutting concerns are handled here. The
transport never logs full URLs or authorization headers. ``http_client``
is injectable so tests can use ``httpx.MockTransport`` without any network.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from shared.circuit_breaker import CircuitBreaker

from .base import ProviderMetrics, Redactor, TokenBucket

logger = logging.getLogger("gula.communication.providers.transport")

_DEFAULT_TIMEOUT = 10.0
_TRANSIENT_STATUS = frozenset({408, 409, 429, 425, 500, 502, 503, 504})


class HttpClient(Protocol):
    """Minimal httpx-compatible client surface used by the transport."""

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any = None,
        content: bytes | None = None,
        files: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Any: ...


@dataclass
class TransportResponse:
    """Normalised response returned to providers (never raises on HTTP)."""

    status_code: int
    headers: dict[str, str] = field(default_factory=dict)
    json: Any = None
    text: str = ""
    request_id: str = ""

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300


@dataclass(frozen=True)
class TransportSettings:
    """Tuning knobs for a transport instance (DI / env-derived)."""

    timeout_seconds: float = _DEFAULT_TIMEOUT
    max_retries: int = 2
    backoff_base_seconds: float = 0.5
    backoff_max_seconds: float = 30.0
    rate_per_minute: int = 60
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout: float = 30.0


class HttpTransport:
    """Provider transport with retries, circuit breaker and redaction."""

    def __init__(
        self,
        *,
        name: str,
        settings: TransportSettings | None = None,
        http_client: HttpClient | None = None,
        redactor: Redactor | None = None,
        rate_limiter: TokenBucket | None = None,
        circuit_breaker: CircuitBreaker | None = None,
        metrics: ProviderMetrics | None = None,
        logger_obj: logging.Logger | None = None,
    ) -> None:
        self.name = name
        self._settings = settings or TransportSettings()
        self._client = http_client or httpx.Client(
            timeout=self._settings.timeout_seconds,
            follow_redirects=True,
        )
        self.redactor = redactor or Redactor()
        self._rate_limiter = rate_limiter or TokenBucket(self._settings.rate_per_minute)
        self._circuit = circuit_breaker or CircuitBreaker(
            name=f"transport:{name}",
            failure_threshold=self._settings.circuit_failure_threshold,
            recovery_timeout=self._settings.circuit_recovery_timeout,
        )
        self.metrics = metrics or ProviderMetrics(name)
        self._log = logger_obj or logger

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any = None,
        content: bytes | None = None,
        files: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> TransportResponse:
        """Perform a request with full cross-cutting behaviour.

        Raises nothing for non-2xx responses; raises :class:`CircuitOpenError`
        when the circuit is open and the caller opted into circuit protection.
        """
        effective_timeout = timeout or self._settings.timeout_seconds
        safe_url = self._safe_url(url)

        if not self._rate_limiter.consume(1):
            self.metrics.record_rate_limited()
            return TransportResponse(status_code=429, text="rate limit exceeded")

        if not self._circuit.allow_request():
            self.metrics.record_circuit_open()
            raise CircuitOpenError(f"circuit open: {self.name}")

        attempts = 0
        last_exc: Exception | None = None
        while True:
            attempts += 1
            start = time.monotonic()
            try:
                response = self._client.request(
                    method,
                    url,
                    headers=self._safe_headers(headers),
                    json=json,
                    content=content,
                    files=files,
                    timeout=effective_timeout,
                )
                result = TransportResponse(
                    status_code=getattr(response, "status_code", 0),
                    headers=_headers_to_dict(getattr(response, "headers", {})),
                    json=_safe_json(response),
                    text=self.redactor.redact(_safe_text(response)),
                    request_id=str(getattr(response, "request", "") or "").strip(),
                )
                self.metrics.record_latency(time.monotonic() - start)
                self.metrics.record_attempt(result.ok)
                if result.ok:
                    self._circuit.record_success()
                else:
                    self._circuit.record_failure()
                    if self._retryable_status(result.status_code) and attempts <= self._settings.max_retries:
                        self._log.warning(
                            "communication_transport_retry name=%s method=%s status=%d attempt=%d",
                            self.name,
                            method,
                            result.status_code,
                            attempts,
                        )
                        self._sleep_backoff(attempts)
                        continue
                    self._log.warning(
                        "communication_transport_response name=%s method=%s status=%d attempts=%d",
                        self.name,
                        method,
                        result.status_code,
                        attempts,
                    )
                return result
            except (httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError, httpx.ReadError) as exc:
                last_exc = exc
                self.metrics.record_latency(time.monotonic() - start)
                self.metrics.record_attempt(False)
                self.metrics.record_failure("network")
                self._circuit.record_failure()
                if attempts <= self._settings.max_retries:
                    self._log.warning(
                        "communication_transport_network_retry name=%s method=%s attempt=%d error_type=%s",
                        self.name,
                        method,
                        attempts,
                        type(exc).__name__,
                    )
                    self._sleep_backoff(attempts)
                    continue
                self._log.error(
                    "communication_transport_network_failed name=%s method=%s attempts=%d url=%s",
                    self.name,
                    method,
                    attempts,
                    safe_url,
                )
                return TransportResponse(
                    status_code=0,
                    text=self.redactor.redact(
                        f"{type(exc).__name__}: {exc}",
                    ),
                )

    def _sleep_backoff(self, attempt: int) -> None:
        delay = min(
            self._settings.backoff_base_seconds * (2 ** (attempt - 1)),
            self._settings.backoff_max_seconds,
        )
        if delay > 0:
            time.sleep(delay)

    # ── redaction helpers ──────────────────────────────────────────────────

    def _safe_url(self, url: str) -> str:
        """Keep scheme+host, drop credentials/query tokens for logs."""
        try:
            parsed = httpx.URL(url)
            masked = self.redactor.redact(f"scheme={parsed.scheme} host={parsed.host or ''}")
            return masked
        except Exception:
            return "[invalid-url]"

    def _safe_headers(self, headers: dict[str, str] | None) -> dict[str, str] | None:
        """Redact authorization / bearer header values before logging."""
        if not headers:
            return headers
        return {
            key: ("[REDACTED]" if key.lower() in ("authorization", "x-api-key", "proxy-authorization") else value)
            for key, value in headers.items()
        }

    @staticmethod
    def _retryable_status(status: int) -> bool:
        return status in _TRANSIENT_STATUS


class CircuitOpenError(RuntimeError):
    """Raised when a transport call is rejected by its circuit breaker."""


def _headers_to_dict(headers: Any) -> dict[str, str]:
    try:
        return {key: str(value) for key, value in headers.items()}
    except Exception:
        return {}


def _safe_text(response: Any) -> str:
    try:
        return getattr(response, "text", "")
    except Exception:
        return ""


def _safe_json(response: Any) -> Any:
    try:
        if hasattr(response, "json"):
            return response.json()
    except Exception:
        return None
    return None


__all__ = [
    "CircuitOpenError",
    "HttpClient",
    "HttpTransport",
    "TransportResponse",
    "TransportSettings",
]