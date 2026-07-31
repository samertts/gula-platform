from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

logger = logging.getLogger("gula.circuit_breaker")


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitOpenError(RuntimeError):
    """Raised when a call is rejected because the circuit is OPEN."""


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3,
    ):
        self._name = name
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._half_open_max_calls = half_open_max_calls
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._half_open_calls = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if (
                self._state == CircuitState.OPEN
                and time.time() - self._last_failure_time >= self._recovery_timeout
            ):
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                logger.info("Circuit '%s' → HALF_OPEN (recovery timeout elapsed)", self._name)
            return self._state

    def allow_request(self) -> bool:
        """Check whether a request may proceed (CLOSED, or HALF_OPEN with spare capacity)."""
        with self._lock:
            current = self._state
            if (
                current == CircuitState.OPEN
                and time.time() - self._last_failure_time >= self._recovery_timeout
            ):
                current = CircuitState.HALF_OPEN
                self._state = current
                self._half_open_calls = 0
                logger.info("Circuit '%s' → HALF_OPEN (recovery timeout elapsed)", self._name)
            if current == CircuitState.OPEN:
                return False
            if current == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                if self._half_open_calls > self._half_open_max_calls:
                    return False
            return True

    def record_success(self) -> None:
        with self._lock:
            self._on_success()

    def record_failure(self) -> None:
        with self._lock:
            self._on_failure()

    def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        current = self.state
        if current == CircuitState.OPEN:
            raise CircuitOpenError(f"Circuit '{self._name}' is OPEN")
        if current == CircuitState.HALF_OPEN:
            with self._lock:
                self._half_open_calls += 1
                if self._half_open_calls > self._half_open_max_calls:
                    raise CircuitOpenError(f"Circuit '{self._name}' HALF_OPEN max calls exceeded")
        try:
            result = fn(*args, **kwargs)
            self.record_success()
            return result
        except Exception:
            self.record_failure()
            raise

    def _on_success(self) -> None:
        self._failure_count = 0
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            logger.info("Circuit '%s' → CLOSED (success in HALF_OPEN)", self._name)

    def _on_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self._failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning("Circuit '%s' → OPEN (threshold=%d)", self._name, self._failure_threshold)

    def reset(self) -> None:
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._half_open_calls = 0
            logger.info("Circuit '%s' reset to CLOSED", self._name)
