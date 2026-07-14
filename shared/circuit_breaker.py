from __future__ import annotations

import logging
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

logger = logging.getLogger("gula.circuit_breaker")


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


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

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self._recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                logger.info("Circuit '%s' → HALF_OPEN (recovery timeout elapsed)", self._name)
        return self._state

    def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        current = self.state
        if current == CircuitState.OPEN:
            raise Exception(f"Circuit '{self._name}' is OPEN")
        if current == CircuitState.HALF_OPEN:
            self._half_open_calls += 1
            if self._half_open_calls > self._half_open_max_calls:
                raise Exception(f"Circuit '{self._name}' HALF_OPEN max calls exceeded")
        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
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
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._half_open_calls = 0
        logger.info("Circuit '%s' reset to CLOSED", self._name)
