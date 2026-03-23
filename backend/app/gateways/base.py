"""
External API Safe Layer — GULA Platform
========================================
Every external API call goes through this base class, which enforces:

  1. Rate limiting   — sliding-window counter, rejects bursts before they hit the network
  2. Circuit breaker — CLOSED → OPEN after N failures, auto-recovers via HALF_OPEN
  3. Caching         — MD5-keyed in-memory TTL cache, avoids redundant network calls
  4. Retry + backoff — up to max_retries attempts with linear back-off
  5. Response validation — subclass hook to reject unexpected/untrusted shapes
  6. Fallback        — caller supplies a safe default; returned when circuit is open
                       or when all retries fail
  7. Audit logging   — every call (hit, miss, error) is logged with duration_ms

Design principle: external APIs are UNTRUSTED. We validate their output before
using it, and we never allow a third-party outage to cascade into core logic.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger("gula.external_api")


# ─── Circuit Breaker ──────────────────────────────────────────────────────────

class CircuitState(Enum):
    CLOSED    = "closed"     # Normal operation — requests pass through
    OPEN      = "open"       # Too many failures — requests blocked immediately
    HALF_OPEN = "half_open"  # Recovery probe — one request allowed through


@dataclass
class CircuitBreaker:
    failure_threshold: int   = 5
    recovery_timeout:  float = 60.0   # seconds before OPEN → HALF_OPEN

    _state:             CircuitState = field(default=CircuitState.CLOSED, init=False, repr=False)
    _failure_count:     int          = field(default=0,   init=False, repr=False)
    _last_failure_time: float        = field(default=0.0, init=False, repr=False)

    @property
    def state(self) -> CircuitState:
        if (
            self._state == CircuitState.OPEN
            and time.monotonic() - self._last_failure_time >= self.recovery_timeout
        ):
            self._state = CircuitState.HALF_OPEN
        return self._state

    @property
    def is_allowed(self) -> bool:
        return self.state != CircuitState.OPEN

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN


# ─── Rate Limiter ─────────────────────────────────────────────────────────────

@dataclass
class SlidingWindowRateLimiter:
    calls_per_minute: int = 60

    _timestamps: list = field(default_factory=list, init=False, repr=False)

    @property
    def is_allowed(self) -> bool:
        now = time.monotonic()
        self._timestamps = [t for t in self._timestamps if now - t < 60.0]
        if len(self._timestamps) >= self.calls_per_minute:
            return False
        self._timestamps.append(now)
        return True


# ─── Errors ───────────────────────────────────────────────────────────────────

class ExternalGatewayError(Exception):
    """Raised when an external gateway call fails after all safeguards."""


# ─── Base Gateway ─────────────────────────────────────────────────────────────

class ExternalGateway:
    """
    Base class for all external API integrations.

    Subclasses must:
      - Set ``name`` (used in logs)
      - Implement ``_do_call(action, **kwargs) -> Any``
      - Optionally override ``_validate_response(response) -> bool``

    Usage::

        result = gateway.call(
            action="verify",
            cache_key="nid:12345",
            fallback={"valid": False, "source": "fallback"},
            national_id="12345",
        )
    """

    # ── Tunable class-level defaults (override in subclasses) ────────────────
    name:                      str   = "external"
    timeout:                   float = 10.0   # seconds per HTTP attempt
    max_retries:               int   = 2
    calls_per_minute:          int   = 60
    circuit_failure_threshold: int   = 5
    circuit_recovery_timeout:  float = 60.0
    cache_ttl:                 float = 300.0  # seconds (5 min default)

    def __init__(self) -> None:
        self._circuit = CircuitBreaker(
            failure_threshold=self.circuit_failure_threshold,
            recovery_timeout=self.circuit_recovery_timeout,
        )
        self._rate_limiter = SlidingWindowRateLimiter(
            calls_per_minute=self.calls_per_minute
        )
        self._cache: Dict[str, tuple[Any, float]] = {}

    # ── Cache helpers ─────────────────────────────────────────────────────────

    def _cache_get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() < expires_at:
            return value
        del self._cache[key]
        return None

    def _cache_set(self, key: str, value: Any) -> None:
        self._cache[key] = (value, time.monotonic() + self.cache_ttl)

    @staticmethod
    def _make_cache_key(gateway_name: str, **kwargs: Any) -> str:
        raw = f"{gateway_name}:{sorted(kwargs.items())}"
        return hashlib.md5(raw.encode()).hexdigest()

    # ── Audit ─────────────────────────────────────────────────────────────────

    def _audit(
        self,
        action: str,
        success: bool,
        duration_ms: float,
        details: str = "",
    ) -> None:
        lvl = logging.INFO if success else logging.WARNING
        logger.log(
            lvl,
            "[EXTERNAL_API] gateway=%s action=%s success=%s duration_ms=%.1f%s",
            self.name,
            action,
            success,
            duration_ms,
            f" details={details!r}" if details else "",
        )

    # ── Response validation hook ──────────────────────────────────────────────

    def _validate_response(self, response: Any) -> bool:
        """
        Override to add schema / range checks.
        Return False to reject the response (treated as a failure).
        """
        return response is not None

    # ── HTTP helper ───────────────────────────────────────────────────────────

    def _http(self, method: str, url: str, **kwargs: Any) -> Any:
        """
        Synchronous HTTP call with retry + linear back-off.
        Uses httpx (already in requirements).
        Raises the last exception if all attempts fail.
        """
        last_exc: Exception = RuntimeError("no attempts made")
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = getattr(client, method)(url, **kwargs)
                    resp.raise_for_status()
                    return resp.json()
            except Exception as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    time.sleep(0.5 * (attempt + 1))
        raise last_exc

    # ── Main entry point ──────────────────────────────────────────────────────

    def call(
        self,
        action: str,
        *,
        cache_key: Optional[str] = None,
        fallback: Optional[Any] = None,
        **call_kwargs: Any,
    ) -> Any:
        """
        Safe wrapper around ``_do_call``.

        Flow:
          rate_limiter → circuit_breaker → cache → _do_call →
          _validate_response → cache_set → audit

        If ``fallback`` is provided it is returned instead of raising when:
          - rate limit is exceeded
          - circuit is OPEN
          - all retries fail
        """
        start = time.monotonic()

        # 1. Rate limit
        if not self._rate_limiter.is_allowed:
            self._audit(action, False, 0.0, "rate_limit_exceeded")
            if fallback is not None:
                return fallback
            raise ExternalGatewayError(f"[{self.name}] rate limit exceeded")

        # 2. Circuit breaker
        if not self._circuit.is_allowed:
            self._audit(
                action, False, 0.0,
                f"circuit_open state={self._circuit.state.value}"
            )
            if fallback is not None:
                return fallback
            raise ExternalGatewayError(f"[{self.name}] circuit open — service unavailable")

        # 3. Cache
        if cache_key:
            cached = self._cache_get(cache_key)
            if cached is not None:
                self._audit(action, True, (time.monotonic() - start) * 1000, "cache_hit")
                return cached

        # 4. Actual call
        try:
            result = self._do_call(action, **call_kwargs)
        except ExternalGatewayError:
            raise
        except Exception as exc:
            self._circuit.record_failure()
            duration_ms = (time.monotonic() - start) * 1000
            self._audit(action, False, duration_ms, str(exc))
            if fallback is not None:
                return fallback
            raise ExternalGatewayError(f"[{self.name}] {exc}") from exc

        # 5. Validate (reject untrusted shapes)
        if not self._validate_response(result):
            self._circuit.record_failure()
            duration_ms = (time.monotonic() - start) * 1000
            self._audit(action, False, duration_ms, "response_validation_failed")
            if fallback is not None:
                return fallback
            raise ExternalGatewayError(f"[{self.name}] response validation failed")

        # 6. All good
        self._circuit.record_success()
        duration_ms = (time.monotonic() - start) * 1000
        self._audit(action, True, duration_ms)

        if cache_key:
            self._cache_set(cache_key, result)

        return result

    def _do_call(self, action: str, **kwargs: Any) -> Any:
        """Implement the actual external API call. Must be overridden."""
        raise NotImplementedError(f"{self.__class__.__name__}._do_call not implemented")
