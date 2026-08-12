from __future__ import annotations

import logging
import time
from enum import Enum, auto

logger = logging.getLogger("gula.kernel.gateway.circuit_breaker")


class CircuitState(Enum):
    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.name = name
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time: float = 0.0

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def record_success(self) -> None:
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED

    def can_proceed(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True


class CircuitBreakerManager:
    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}

    def get(self, name: str) -> CircuitBreaker | None:
        return self._breakers.get(name)

    def register(self, breaker: CircuitBreaker) -> None:
        self._breakers[breaker.name] = breaker

    def can_proceed(self, name: str) -> bool:
        breaker = self._breakers.get(name)
        if not breaker:
            return True
        return breaker.can_proceed()

    def record_failure(self, name: str) -> None:
        breaker = self._breakers.get(name)
        if breaker:
            breaker.record_failure()

    def record_success(self, name: str) -> None:
        breaker = self._breakers.get(name)
        if breaker:
            breaker.record_success()
