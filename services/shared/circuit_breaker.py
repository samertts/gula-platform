"""
GULA Platform - Circuit Breaker Implementation
Executive Order 7: Prevent cascading service failures
Executive Order 8: Retry Queue for failed requests
"""

import time
import logging
import functools
from enum import Enum
from typing import Callable, Any, Optional
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

FAILURE_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
RECOVERY_TIMEOUT  = int(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "30"))
RETRY_MAX         = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
RETRY_BACKOFF     = int(os.getenv("RETRY_BACKOFF_SECONDS", "2"))


class CircuitState(str, Enum):
    CLOSED    = "closed"      # Normal operation
    OPEN      = "open"        # Blocking calls after threshold exceeded
    HALF_OPEN = "half-open"   # Testing if service recovered


class CircuitBreaker:
    """
    Circuit Breaker Pattern Implementation.
    - CLOSED: All requests pass through.
    - OPEN: Requests fail fast after FAILURE_THRESHOLD failures.
    - HALF_OPEN: One probe request allowed after RECOVERY_TIMEOUT seconds.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = FAILURE_THRESHOLD,
        recovery_timeout: int = RECOVERY_TIMEOUT,
        fallback: Optional[Callable] = None,
    ):
        self.name             = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.fallback         = fallback
        self._state           = CircuitState.CLOSED
        self._failure_count   = 0
        self._last_failure    = None
        self._opened_at       = None

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if self._opened_at and datetime.utcnow() >= self._opened_at + timedelta(seconds=self.recovery_timeout):
                self._state = CircuitState.HALF_OPEN
                logger.info(f"[CircuitBreaker:{self.name}] → HALF_OPEN (testing recovery)")
        return self._state

    def record_success(self):
        self._failure_count = 0
        if self._state != CircuitState.CLOSED:
            logger.info(f"[CircuitBreaker:{self.name}] → CLOSED (recovered)")
        self._state = CircuitState.CLOSED

    def record_failure(self):
        self._failure_count += 1
        self._last_failure = datetime.utcnow()
        logger.warning(f"[CircuitBreaker:{self.name}] failure #{self._failure_count}")

        if self._failure_count >= self.failure_threshold:
            self._state     = CircuitState.OPEN
            self._opened_at = datetime.utcnow()
            logger.error(
                f"[CircuitBreaker:{self.name}] → OPEN "
                f"(retry after {self.recovery_timeout}s)"
            )

    def call(self, func: Callable, *args, **kwargs) -> Any:
        current_state = self.state

        if current_state == CircuitState.OPEN:
            logger.warning(f"[CircuitBreaker:{self.name}] OPEN — fast-failing request")
            if self.fallback:
                return self.fallback(*args, **kwargs)
            raise CircuitOpenError(f"Circuit '{self.name}' is OPEN. Retry after {self.recovery_timeout}s.")

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as exc:
            self.record_failure()
            if self.fallback:
                return self.fallback(*args, **kwargs)
            raise

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper


class CircuitOpenError(Exception):
    """Raised when a circuit breaker is OPEN."""
    pass


def with_retry(
    max_attempts: int = RETRY_MAX,
    backoff_seconds: float = RETRY_BACKOFF,
    exceptions: tuple = (Exception,),
):
    """
    Retry decorator with exponential backoff.
    Executive Order 8: Any failed request goes to retry.queue.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt >= max_attempts:
                        logger.error(f"[Retry] {func.__name__} failed after {max_attempts} attempts: {exc}")
                        raise
                    wait = backoff_seconds * (2 ** (attempt - 1))
                    logger.warning(f"[Retry] {func.__name__} attempt {attempt}/{max_attempts} failed. Retrying in {wait}s...")
                    time.sleep(wait)
            raise last_exc  # Should never reach here, but safety net
        return wrapper
    return decorator


# Global circuit breaker registry
_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(service_name: str, **kwargs) -> CircuitBreaker:
    if service_name not in _breakers:
        _breakers[service_name] = CircuitBreaker(name=service_name, **kwargs)
    return _breakers[service_name]
