"""
Self-Healing System — GULA Platform
=====================================
Keeps the backend alive and functional under partial infrastructure failures.

Components:
  1. CircuitBreaker      — tracks consecutive failures per service, opens/closes
                           circuit to prevent cascade failures
  2. SystemHealth        — shared health state, thread-safe
  3. DegradedModeMiddleware — routes degraded requests to read-only fallback
  4. RecoveryWorker      — background coroutine that probes failed services
                           and resets circuit breakers when they recover

Circuit Breaker States:
  CLOSED  → normal operation (requests pass through)
  OPEN    → failure threshold exceeded (requests rejected immediately)
  HALF_OPEN → recovery probe in progress (one test request allowed through)

Degraded Mode:
  When DB circuit opens, the system enters read-only/degraded mode:
    - GET requests: served from cache where possible
    - POST/PUT/DELETE: rejected with 503 + Retry-After header
    - Health/probe paths: always pass through
"""
import asyncio
import logging
import threading
import time
from enum import Enum
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("gula.self_healing")


# ─── Circuit Breaker ─────────────────────────────────────────────────────────

class CircuitState(Enum):
    CLOSED = "closed"       # Normal — requests pass through
    OPEN = "open"           # Failed — requests rejected immediately
    HALF_OPEN = "half_open" # Recovery probe in progress


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
        self._last_failure_time: Optional[float] = None
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
                    self.name, self._state.value,
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
                        self.name, self._failure_count,
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


# ─── Shared System Health State ──────────────────────────────────────────────

class SystemHealth:
    """Singleton that holds circuit breakers and degraded-mode flag."""

    _instance: Optional["SystemHealth"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "SystemHealth":
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
        self._degraded = False
        self._lock = threading.Lock()

    @property
    def degraded(self) -> bool:
        with self._lock:
            return self._degraded

    def enter_degraded_mode(self, reason: str) -> None:
        with self._lock:
            if not self._degraded:
                logger.error(
                    "[SELF-HEALING] Entering DEGRADED MODE: %s", reason
                )
                self._degraded = True

    def exit_degraded_mode(self) -> None:
        with self._lock:
            if self._degraded:
                logger.info("[SELF-HEALING] Exiting degraded mode — all systems restored")
                self._degraded = False

    def update_degraded_state(self) -> None:
        """Recompute degraded flag from circuit breaker states."""
        db_open = self.db_circuit.is_open()
        if db_open:
            self.enter_degraded_mode("DB circuit open")
        else:
            # Only exit degraded mode if all circuits are closed
            if not self.redis_circuit.is_open():
                self.exit_degraded_mode()

    def to_dict(self) -> dict:
        return {
            "degraded_mode": self.degraded,
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

# Paths that are ALWAYS allowed regardless of degraded mode
_ALWAYS_ALLOWED: frozenset[str] = frozenset({
    "/health",
    "/health/ready",
    "/health/live",
})

# HTTP methods that are safe in degraded mode (read-only)
_SAFE_METHODS: frozenset[str] = frozenset({"GET", "HEAD", "OPTIONS"})


class DegradedModeMiddleware(BaseHTTPMiddleware):
    """Reject write operations when the system is in degraded mode.

    In degraded mode (DB circuit open):
      - GET requests pass through (may serve cached data)
      - POST/PUT/DELETE/PATCH are rejected with 503 + Retry-After header
      - Health probes always pass
    """

    async def dispatch(self, request: Request, call_next):
        if request.url.path in _ALWAYS_ALLOWED:
            return await call_next(request)

        if health.degraded and request.method not in _SAFE_METHODS:
            return JSONResponse(
                status_code=503,
                headers={"Retry-After": "30"},
                content={
                    "detail": (
                        "System is in degraded mode (database unavailable). "
                        "Write operations are temporarily suspended."
                    ),
                    "detail_ar": (
                        "النظام في وضع مخفّض (قاعدة البيانات غير متاحة). "
                        "عمليات الكتابة معلّقة مؤقتاً."
                    ),
                    "degraded": True,
                    "retry_after_seconds": 30,
                },
            )

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

            interval = (
                cls._DEGRADED_POLL_INTERVAL if health.degraded
                else cls._POLL_INTERVAL
            )
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
