from __future__ import annotations

"""
Self-Healing System — GULA Platform
=====================================
Keeps the backend alive and functional under partial infrastructure failures.

Components:
  1. CircuitBreaker      — tracks consecutive failures per service, opens/closes
                            circuit to prevent cascade failures
  2. SystemHealth        — shared health state, thread-safe
  3. DegradedModeMiddleware — routes degraded requests per degradation level
  4. RecoveryWorker      — background coroutine that probes failed services
                            and resets circuit breakers when they recover

Circuit Breaker States:
  CLOSED  → normal operation (requests pass through)
  OPEN    → failure threshold exceeded (requests rejected immediately)
  HALF_OPEN → recovery probe in progress (one test request allowed through)

Degradation Levels (escalating severity):
  NONE           → all operations pass (normal)
  L1_CACHE_HEAVY → writes pass with warning; reads prefer cache
  L2_READ_ONLY   → POST/PUT/DELETE/PATCH rejected (DB circuit opened)
  L3_CRITICAL_ONLY → only health + auth + kill-switch paths pass (DB storm)
"""

import asyncio
import logging
import threading
import time
from enum import Enum

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("gula.self_healing")


# ─── Circuit Breaker ─────────────────────────────────────────────────────────


class CircuitState(Enum):
    CLOSED = "closed"  # Normal — requests pass through
    OPEN = "open"  # Failed — requests rejected immediately
    HALF_OPEN = "half_open"  # Recovery probe in progress


class CircuitBreaker:
    """Thread-safe circuit breaker for a single service dependency."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._get_state()

    def _get_state(self) -> CircuitState:
        """Internal state reader — call with lock held."""
        if self._state == CircuitState.OPEN:
            # Auto-transition to HALF_OPEN after recovery timeout
            if (
                self._last_failure_time is not None
                and (time.monotonic() - self._last_failure_time) >= self.recovery_timeout
            ):
                self._state = CircuitState.HALF_OPEN
                logger.info(
                    "[CIRCUIT BREAKER] %s: OPEN → HALF_OPEN (probing recovery)",
                    self.name,
                )
        return self._state

    def record_success(self) -> None:
        """Call after a successful operation. Closes an open/half-open circuit."""
        with self._lock:
            if self._state != CircuitState.CLOSED:
                logger.info(
                    "[CIRCUIT BREAKER] %s: %s → CLOSED (recovered)",
                    self.name,
                    self._state.value,
                )
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None

    def record_failure(self) -> None:
        """Call after a failed operation. Opens circuit when threshold is hit."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._failure_count >= self.failure_threshold:
                if self._state != CircuitState.OPEN:
                    logger.error(
                        "[CIRCUIT BREAKER] %s: → OPEN after %d failures",
                        self.name,
                        self._failure_count,
                    )
                self._state = CircuitState.OPEN

    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    def allow_probe(self) -> bool:
        """Return True if a recovery probe should be attempted."""
        return self.state == CircuitState.HALF_OPEN

    def reset(self) -> None:
        """Force-reset to CLOSED (use with care — for admin/recovery only)."""
        with self._lock:
            logger.warning("[CIRCUIT BREAKER] %s: force-reset to CLOSED", self.name)
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "name": self.name,
                "state": self._get_state().value,
                "failure_count": self._failure_count,
                "last_failure_time": self._last_failure_time,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout_s": self.recovery_timeout,
            }


# ─── Degradation Level ────────────────────────────────────────────────────────


class DegradationLevel(Enum):
    """Ordered severity levels for graceful degradation.

    The system escalates through levels as conditions worsen and
    de-escalates back to NONE when all circuits recover.

    NONE           → normal; all requests pass
    L1_CACHE_HEAVY → writes allowed but warned; cache preferred for reads
    L2_READ_ONLY   → write mutations rejected; reads pass (DB circuit opened)
    L3_CRITICAL_ONLY → only a small set of critical paths pass (DB storm)
    """

    NONE = 0
    L1_CACHE_HEAVY = 1
    L2_READ_ONLY = 2
    L3_CRITICAL_ONLY = 3


# ─── Shared System Health State ──────────────────────────────────────────────


class SystemHealth:
    """Singleton that holds circuit breakers and degradation level."""

    _instance: SystemHealth | None = None
    _lock = threading.Lock()

    def __new__(cls) -> SystemHealth:
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._init()
                cls._instance = inst
        return cls._instance

    def _init(self) -> None:
        self.db_circuit = CircuitBreaker(
            "postgresql",
            failure_threshold=3,
            recovery_timeout=30.0,
        )
        self.redis_circuit = CircuitBreaker(
            "redis",
            failure_threshold=5,
            recovery_timeout=20.0,
        )
        self._degradation_level = DegradationLevel.NONE
        self._lock = threading.Lock()

    # ── Backward-compat bool property ────────────────────────────────────────
    @property
    def degraded(self) -> bool:
        """True when any degradation level is active (compat with existing code)."""
        with self._lock:
            return self._degradation_level != DegradationLevel.NONE

    @property
    def degradation_level(self) -> DegradationLevel:
        with self._lock:
            return self._degradation_level

    def enter_degraded_mode(
        self,
        reason: str,
        level: DegradationLevel = DegradationLevel.L2_READ_ONLY,
    ) -> None:
        """Escalate degradation level.  Never downgrades during an active incident."""
        with self._lock:
            current = self._degradation_level
            if level.value <= current.value:
                return  # already at equal or worse level
            self._degradation_level = level
            logger.error(
                "[SELF-HEALING] Degradation %s → %s: %s",
                current.name,
                level.name,
                reason,
            )

    def exit_degraded_mode(self) -> None:
        """Reset to NONE.  Called when all circuits recover."""
        with self._lock:
            if self._degradation_level != DegradationLevel.NONE:
                logger.info(
                    "[SELF-HEALING] Degradation %s → NONE — all systems restored",
                    self._degradation_level.name,
                )
                self._degradation_level = DegradationLevel.NONE

    def update_degraded_state(self) -> None:
        """Recompute degradation level from circuit breaker states.

        Priority (highest wins):
          DB open    → L2_READ_ONLY  (writes blocked)
          Redis open → L1_CACHE_HEAVY (cache unavailable; DB still serves reads)
          All closed → exit to NONE (unless already at L2/L3 via explicit trigger)
        """
        db_open = self.db_circuit.is_open()
        redis_open = self.redis_circuit.is_open()

        if db_open:
            self.enter_degraded_mode("DB circuit open", DegradationLevel.L2_READ_ONLY)
        elif redis_open:
            # DB alive but Redis down → cache unavailable → L1 (writes still pass)
            self.enter_degraded_mode(
                "Redis circuit open — cache unavailable",
                DegradationLevel.L1_CACHE_HEAVY,
            )
        else:
            # All circuits closed — this means the RecoveryWorker confirmed that
            # DB and Redis are both reachable again.  Exit from any level back to NONE.
            # (L2/L3 are entered when circuits open; they exit when circuits close here.)
            self.exit_degraded_mode()

    def to_dict(self) -> dict:
        lv = self.degradation_level
        return {
            "degraded_mode": self.degraded,
            "degradation_level": lv.name,
            "degradation_value": lv.value,
            "circuits": {
                "db": self.db_circuit.to_dict(),
                "redis": self.redis_circuit.to_dict(),
            },
        }


# Module-level singleton
health = SystemHealth()


# ─── DB / Redis wrappers with circuit-breaker recording ──────────────────────


def checked_db_connection() -> bool:
    """Run DB ping and record result in the circuit breaker."""
    try:
        from ..database import check_db_connection

        ok = check_db_connection()
        if ok:
            health.db_circuit.record_success()
        else:
            health.db_circuit.record_failure()
        health.update_degraded_state()
        return ok
    except Exception as exc:
        logger.warning("[SELF-HEALING] DB check exception: %s", exc)
        health.db_circuit.record_failure()
        health.update_degraded_state()
        return False


def checked_redis_connection() -> bool:
    """Run Redis ping and record result in the circuit breaker."""
    try:
        from ..security.redis_client import cache as _redis

        _redis.ping()
        health.redis_circuit.record_success()
        return True
    except Exception as exc:
        logger.warning("[SELF-HEALING] Redis check exception: %s", exc)
        health.redis_circuit.record_failure()
        health.update_degraded_state()
        return False


# ─── Degraded Mode Middleware ─────────────────────────────────────────────────

# Paths that bypass ALL degradation checks (healthz + liveness always reachable)
_ALWAYS_ALLOWED: frozenset[str] = frozenset(
    {
        "/health",
        "/health/ready",
        "/health/live",
    },
)

# Paths allowed even in L3_CRITICAL_ONLY — the minimum viable platform surface
_CRITICAL_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/health/ready",
        "/health/live",
        "/health/status",
        "/auth/login",
        "/auth/refresh",
        "/admin/kill-switch/deactivate",  # operator must always be able to recover
        "/metrics/prom",  # Prometheus scraping must continue
    },
)

# HTTP methods that are safe in L2 read-only mode
_SAFE_METHODS: frozenset[str] = frozenset({"GET", "HEAD", "OPTIONS"})

# Degradation level → human-readable message sent to callers
_LEVEL_MESSAGES: dict[DegradationLevel, tuple[str, str]] = {
    DegradationLevel.L2_READ_ONLY: (
        "System is in read-only mode (database unavailable). "
        "Write operations are temporarily suspended.",
        "النظام في وضع القراءة فقط (قاعدة البيانات غير متاحة). عمليات الكتابة معلّقة مؤقتاً.",
    ),
    DegradationLevel.L3_CRITICAL_ONLY: (
        "System is under critical load (database storm). Only essential endpoints are reachable.",
        "النظام تحت ضغط حرج (عاصفة قاعدة البيانات). المسارات الحيوية فقط متاحة.",
    ),
}


class DegradedModeMiddleware(BaseHTTPMiddleware):
    """Apply request filtering based on the current degradation level.

    L1_CACHE_HEAVY  → pass all; headers added for downstream cache preference
    L2_READ_ONLY    → block POST/PUT/DELETE/PATCH; GET passes
    L3_CRITICAL_ONLY → block everything except _CRITICAL_PATHS
    """

    async def dispatch(self, request: Request, call_next):
        if request.url.path in _ALWAYS_ALLOWED:
            return await call_next(request)

        level = health.degradation_level

        if level == DegradationLevel.NONE:
            return await call_next(request)

        if level == DegradationLevel.L1_CACHE_HEAVY:
            # Pass through — cache-preference is handled at the route level.
            # Add a response header so clients know the system is under pressure.
            response = await call_next(request)
            response.headers["X-Degradation-Level"] = "L1_CACHE_HEAVY"
            return response

        if level == DegradationLevel.L2_READ_ONLY:
            if request.method not in _SAFE_METHODS:
                msg, msg_ar = _LEVEL_MESSAGES[DegradationLevel.L2_READ_ONLY]
                return JSONResponse(
                    status_code=503,
                    headers={"Retry-After": "30", "X-Degradation-Level": "L2_READ_ONLY"},
                    content={
                        "detail": msg,
                        "detail_ar": msg_ar,
                        "degraded": True,
                        "degradation_level": "L2_READ_ONLY",
                        "retry_after_seconds": 30,
                    },
                )
            return await call_next(request)

        if level == DegradationLevel.L3_CRITICAL_ONLY:
            if request.url.path not in _CRITICAL_PATHS:
                msg, msg_ar = _LEVEL_MESSAGES[DegradationLevel.L3_CRITICAL_ONLY]
                return JSONResponse(
                    status_code=503,
                    headers={"Retry-After": "60", "X-Degradation-Level": "L3_CRITICAL_ONLY"},
                    content={
                        "detail": msg,
                        "detail_ar": msg_ar,
                        "degraded": True,
                        "degradation_level": "L3_CRITICAL_ONLY",
                        "retry_after_seconds": 60,
                    },
                )
            return await call_next(request)

        return await call_next(request)


# ─── Background Recovery Worker ──────────────────────────────────────────────


class RecoveryWorker:
    """Async background task that probes failed services and resets circuits."""

    # Polling interval in normal operation (seconds)
    _POLL_INTERVAL = 30
    # Shorter interval when degraded (faster recovery detection)
    _DEGRADED_POLL_INTERVAL = 10

    @classmethod
    async def background_loop(cls) -> None:
        """Run forever. Probes open circuits and updates system health."""
        logger.info("[RECOVERY WORKER] Started")
        while True:
            try:
                await cls._probe_services()
            except Exception:
                logger.exception("[RECOVERY WORKER] Unexpected error during probe")

            interval = cls._DEGRADED_POLL_INTERVAL if health.degraded else cls._POLL_INTERVAL
            await asyncio.sleep(interval)

    @classmethod
    async def _probe_services(cls) -> None:
        loop = asyncio.get_event_loop()

        # Probe DB if circuit is open or half-open
        db_state = health.db_circuit.state
        if db_state in (CircuitState.OPEN, CircuitState.HALF_OPEN):
            logger.info("[RECOVERY WORKER] Probing DB (circuit=%s)...", db_state.value)
            db_ok = await loop.run_in_executor(None, checked_db_connection)
            if db_ok:
                logger.info("[RECOVERY WORKER] DB recovered — circuit reset")
            else:
                logger.warning("[RECOVERY WORKER] DB still unreachable")

        # Probe Redis if circuit is open or half-open
        redis_state = health.redis_circuit.state
        if redis_state in (CircuitState.OPEN, CircuitState.HALF_OPEN):
            logger.info("[RECOVERY WORKER] Probing Redis (circuit=%s)...", redis_state.value)
            redis_ok = await loop.run_in_executor(None, checked_redis_connection)
            if redis_ok:
                logger.info("[RECOVERY WORKER] Redis recovered — circuit reset")
            else:
                logger.warning("[RECOVERY WORKER] Redis still unreachable")
