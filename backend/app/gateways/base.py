"""
External API Clinical-Grade Safe Layer — GULA Platform
=======================================================

Every external API call passes through this base class, which enforces:

  NETWORK RESILIENCE
  ──────────────────
  1. Rate limiting       — sliding-window counter, rejects bursts before the network
  2. Circuit breaker     — CLOSED → OPEN after N failures, auto-recovers via HALF_OPEN
  3. Retry + back-off    — configurable attempts with linear delay
  4. Timeout             — hard deadline on every HTTP attempt

  DATA SAFETY (clinical-grade additions)
  ───────────────────────────────────────
  5. Data Trust Level    — ENRICHMENT | NON_CRITICAL | CRITICAL
                           CRITICAL data from external sources is always BLOCKED
  6. Strict validation   — subclass defines required fields + value ranges;
                           anything outside the schema is rejected, not silently accepted
  7. Freshness tracking  — every cached value carries a timestamp;
                           stale responses are flagged explicitly, not silently returned
  8. ExternalDataResult  — every response is wrapped with provenance metadata:
                           source, is_stale, trust_level, requires_verification
  9. Shadow mode         — run the external call, log the result, but return
                           internal_data unchanged (safe comparison without risk)
  10. Clinical guard     — hard block: CRITICAL trust level always raises,
                           ensuring external data never flows into clinical decisions
  11. Fallback with context — fallback returns ExternalDataResult with
                              requires_verification=True so callers know it's degraded
  12. Audit log          — every call logged: gateway, action, trust_level,
                           success, duration_ms, source

Design law: external APIs are UNTRUSTED sources.
We validate, classify, and gate every response before it touches core logic.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("gula.external_api")


# ─── Data Trust Classification ────────────────────────────────────────────────

class DataTrustLevel(str, Enum):
    """
    Classifies what a piece of external data may influence.

    ENRICHMENT   — UI decoration only (city name, weather, icons).
                   Safe to use and display. Never drives logic.

    NON_CRITICAL — Operational, non-clinical data (insurance status, SMS status).
                   May be used with a verified fallback.

    CRITICAL     — Anything that could influence a clinical decision.
                   ALWAYS blocked from external sources. No exceptions.
    """
    ENRICHMENT    = "enrichment"
    NON_CRITICAL  = "non_critical"
    CRITICAL      = "critical"


# ─── External Data Result ─────────────────────────────────────────────────────

@dataclass
class ExternalDataResult:
    """
    Every response from an external gateway is wrapped in this object.
    Callers must inspect ``trust_level`` and ``requires_verification``
    before using the data in any decision.
    """
    data:                  Any
    source:                str           # "api" | "cache" | "fallback" | "shadow_blocked"
    trust_level:           DataTrustLevel
    gateway:               str
    action:                str
    timestamp:             float = field(default_factory=time.time)
    is_stale:              bool  = False
    requires_verification: bool  = False
    cache_age_seconds:     float = 0.0

    def as_dict(self) -> dict:
        return {
            "data":                  self.data,
            "source":                self.source,
            "trust_level":           self.trust_level.value,
            "gateway":               self.gateway,
            "action":                self.action,
            "timestamp":             self.timestamp,
            "is_stale":              self.is_stale,
            "requires_verification": self.requires_verification,
            "cache_age_seconds":     self.cache_age_seconds,
        }


# ─── Validation ───────────────────────────────────────────────────────────────

class ValidationError(ValueError):
    """Raised when an external response fails schema or range checks."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"External data validation failed: {reason}")


@dataclass
class FieldRule:
    """Declares one required field and its optional value constraints."""
    name:        str
    type:        type
    required:    bool           = True
    allowed:     Optional[List] = None   # whitelist of allowed values
    min_value:   Optional[float] = None
    max_value:   Optional[float] = None


def validate_schema(data: Any, rules: List[FieldRule], context: str = "") -> None:
    """
    Strict schema validator.  Raises ValidationError on the first violation.
    Used by gateways to reject unexpected external shapes before they touch logic.
    """
    if not isinstance(data, dict):
        raise ValidationError(f"[{context}] expected dict, got {type(data).__name__}")

    for rule in rules:
        if rule.name not in data:
            if rule.required:
                raise ValidationError(f"[{context}] missing required field '{rule.name}'")
            continue

        value = data[rule.name]

        if not isinstance(value, rule.type):
            raise ValidationError(
                f"[{context}] field '{rule.name}': expected {rule.type.__name__}, "
                f"got {type(value).__name__}"
            )

        if rule.allowed is not None and value not in rule.allowed:
            raise ValidationError(
                f"[{context}] field '{rule.name}': value {value!r} not in allowed set"
            )

        if rule.min_value is not None and isinstance(value, (int, float)):
            if value < rule.min_value:
                raise ValidationError(
                    f"[{context}] field '{rule.name}': {value} < min {rule.min_value}"
                )

        if rule.max_value is not None and isinstance(value, (int, float)):
            if value > rule.max_value:
                raise ValidationError(
                    f"[{context}] field '{rule.name}': {value} > max {rule.max_value}"
                )


# ─── Circuit Breaker ──────────────────────────────────────────────────────────

class CircuitState(Enum):
    CLOSED    = "closed"
    OPEN      = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    failure_threshold: int   = 5
    recovery_timeout:  float = 60.0

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


# ─── Cache Entry ──────────────────────────────────────────────────────────────

@dataclass
class CacheEntry:
    value:      Any
    stored_at:  float  # time.monotonic() at storage time
    wall_clock: float  # time.time() at storage time — for freshness display
    expires_at: float  # time.monotonic() deadline

    @property
    def is_expired(self) -> bool:
        return time.monotonic() >= self.expires_at

    @property
    def age_seconds(self) -> float:
        return time.monotonic() - self.stored_at


# ─── Errors ───────────────────────────────────────────────────────────────────

class ExternalGatewayError(Exception):
    """Raised when an external gateway call fails after all safeguards."""


class ClinicalDataViolation(RuntimeError):
    """
    Raised when external data marked CRITICAL is about to enter core logic.
    This exception should NEVER be caught silently — it is a design violation.
    """


# ─── Base Gateway ─────────────────────────────────────────────────────────────

class ExternalGateway:
    """
    Clinical-grade base class for all external API integrations.

    Subclasses must:
      - Set ``name`` and ``trust_level``
      - Implement ``_do_call(action, **kwargs) -> Any``
      - Override ``_validate_response(response)`` with strict field rules

    Usage (recommended)::

        result: ExternalDataResult = gateway.call(
            action="verify",
            cache_key="nid:hash",
            fallback={"valid": False},
        )

        # Always check provenance before using data
        if result.trust_level == DataTrustLevel.CRITICAL:
            raise ClinicalDataViolation("...")   # should never reach here

        if result.requires_verification:
            log_for_manual_review(result)

        return result.data
    """

    # ── Class-level defaults (override in subclasses) ─────────────────────────
    name:                      str            = "external"
    trust_level:               DataTrustLevel = DataTrustLevel.NON_CRITICAL
    timeout:                   float          = 10.0
    max_retries:               int            = 2
    calls_per_minute:          int            = 60
    circuit_failure_threshold: int            = 5
    circuit_recovery_timeout:  float          = 60.0
    cache_ttl:                 float          = 300.0
    stale_threshold:           float          = 60.0   # seconds before "recently cached" becomes "stale"

    def __init__(self) -> None:
        self._circuit = CircuitBreaker(
            failure_threshold=self.circuit_failure_threshold,
            recovery_timeout=self.circuit_recovery_timeout,
        )
        self._rate_limiter = SlidingWindowRateLimiter(
            calls_per_minute=self.calls_per_minute
        )
        self._cache: Dict[str, CacheEntry] = {}

    # ── Clinical Guard ────────────────────────────────────────────────────────

    def _enforce_clinical_guard(self) -> None:
        """
        Hard block: CRITICAL data cannot come from external sources.
        If a gateway is misconfigured with trust_level=CRITICAL, this fires.
        """
        if self.trust_level == DataTrustLevel.CRITICAL:
            raise ClinicalDataViolation(
                f"Gateway '{self.name}' is classified CRITICAL. "
                "External APIs must not supply clinical data. "
                "Use internal validated sources only."
            )

    # ── Cache helpers ─────────────────────────────────────────────────────────

    def _cache_get(self, key: str) -> Optional[CacheEntry]:
        entry = self._cache.get(key)
        if entry is None:
            return None
        if entry.is_expired:
            del self._cache[key]
            return None
        return entry

    def _cache_set(self, key: str, value: Any) -> None:
        now = time.monotonic()
        self._cache[key] = CacheEntry(
            value=value,
            stored_at=now,
            wall_clock=time.time(),
            expires_at=now + self.cache_ttl,
        )

    @staticmethod
    def _make_cache_key(gateway_name: str, **kwargs: Any) -> str:
        raw = f"{gateway_name}:{sorted(kwargs.items())}"
        return hashlib.md5(raw.encode()).hexdigest()

    # ── Audit ─────────────────────────────────────────────────────────────────

    def _audit(
        self,
        action:      str,
        success:     bool,
        duration_ms: float,
        source:      str = "api",
        details:     str = "",
    ) -> None:
        lvl = logging.INFO if success else logging.WARNING
        logger.log(
            lvl,
            "[EXTERNAL_API] gateway=%s trust=%s action=%s success=%s "
            "source=%s duration_ms=%.1f%s",
            self.name,
            self.trust_level.value,
            action,
            success,
            source,
            duration_ms,
            f" details={details!r}" if details else "",
        )

    # ── Validation hook ───────────────────────────────────────────────────────

    def _validate_response(self, response: Any) -> None:
        """
        Override to apply strict schema + range checks via validate_schema().
        Raise ValidationError to reject the response.
        Default: only checks that the response is not None.
        """
        if response is None:
            raise ValidationError(f"[{self.name}] response is None")

    # ── HTTP helper ───────────────────────────────────────────────────────────

    def _http(self, method: str, url: str, **kwargs: Any) -> Any:
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

    # ── Shadow mode ───────────────────────────────────────────────────────────

    def call_shadow(
        self,
        action:        str,
        internal_data: Any,
        **call_kwargs: Any,
    ) -> ExternalDataResult:
        """
        Shadow mode: execute the external call, log the result for comparison,
        but always return ``internal_data`` unchanged.

        Use this when you want to validate that the external API matches
        your internal data before switching to live mode — with zero risk.
        """
        try:
            external = self._do_call(action, **call_kwargs)
            logger.info(
                "[SHADOW] gateway=%s action=%s external=%r internal=%r",
                self.name, action, external, internal_data,
            )
        except Exception as exc:
            logger.warning(
                "[SHADOW] gateway=%s action=%s external_error=%r",
                self.name, action, str(exc),
            )

        return ExternalDataResult(
            data=internal_data,
            source="shadow_blocked",
            trust_level=self.trust_level,
            gateway=self.name,
            action=action,
            requires_verification=False,
        )

    # ── Main entry point ──────────────────────────────────────────────────────

    def call(
        self,
        action:     str,
        *,
        cache_key:  Optional[str] = None,
        fallback:   Optional[Any] = None,
        **call_kwargs: Any,
    ) -> ExternalDataResult:
        """
        Clinical-grade safe call wrapper.

        Flow:
          clinical_guard → rate_limiter → circuit_breaker → cache →
          _do_call → _validate_response → cache_set → audit

        Always returns an ExternalDataResult. Never raises for network errors
        (falls back instead). ClinicalDataViolation is intentionally NOT caught.
        """
        start = time.monotonic()

        # 0. Clinical guard — hard block for CRITICAL trust level
        self._enforce_clinical_guard()

        # 1. Rate limit
        if not self._rate_limiter.is_allowed:
            self._audit(action, False, 0.0, "rate_limited", "rate_limit_exceeded")
            return self._fallback_result(action, fallback, "rate_limited")

        # 2. Circuit breaker
        if not self._circuit.is_allowed:
            self._audit(
                action, False, 0.0, "circuit_open",
                f"state={self._circuit.state.value}"
            )
            return self._fallback_result(action, fallback, "circuit_open")

        # 3. Cache — return with freshness metadata
        if cache_key:
            entry = self._cache_get(cache_key)
            if entry is not None:
                age = entry.age_seconds
                is_stale = age > self.stale_threshold
                self._audit(action, True, (time.monotonic() - start) * 1000,
                            "cache", f"age={age:.0f}s stale={is_stale}")
                return ExternalDataResult(
                    data=entry.value,
                    source="cache",
                    trust_level=self.trust_level,
                    gateway=self.name,
                    action=action,
                    timestamp=entry.wall_clock,
                    is_stale=is_stale,
                    requires_verification=is_stale,
                    cache_age_seconds=age,
                )

        # 4. Actual call
        try:
            raw = self._do_call(action, **call_kwargs)
        except Exception as exc:
            self._circuit.record_failure()
            duration_ms = (time.monotonic() - start) * 1000
            self._audit(action, False, duration_ms, "api", str(exc))
            return self._fallback_result(action, fallback, "api_error")

        # 5. Strict schema + range validation — reject untrusted shapes
        try:
            self._validate_response(raw)
        except ValidationError as exc:
            self._circuit.record_failure()
            duration_ms = (time.monotonic() - start) * 1000
            self._audit(action, False, duration_ms, "api", str(exc))
            logger.error(
                "[EXTERNAL_API] VALIDATION_REJECTED gateway=%s action=%s reason=%s",
                self.name, action, exc.reason,
            )
            return self._fallback_result(action, fallback, "validation_rejected")

        # 6. All good
        self._circuit.record_success()
        duration_ms = (time.monotonic() - start) * 1000
        self._audit(action, True, duration_ms, "api")

        if cache_key:
            self._cache_set(cache_key, raw)

        return ExternalDataResult(
            data=raw,
            source="api",
            trust_level=self.trust_level,
            gateway=self.name,
            action=action,
            requires_verification=False,
        )

    # ── Fallback builder ──────────────────────────────────────────────────────

    def _fallback_result(
        self,
        action:  str,
        fallback: Optional[Any],
        source:  str,
    ) -> ExternalDataResult:
        if fallback is None:
            raise ExternalGatewayError(
                f"[{self.name}] service unavailable and no fallback provided"
            )
        return ExternalDataResult(
            data=fallback,
            source=source,
            trust_level=self.trust_level,
            gateway=self.name,
            action=action,
            is_stale=True,
            requires_verification=True,
        )

    def _do_call(self, action: str, **kwargs: Any) -> Any:
        raise NotImplementedError(f"{self.__class__.__name__}._do_call not implemented")
