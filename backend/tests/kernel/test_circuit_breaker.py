from __future__ import annotations

import time

import pytest
from app.kernel.gateway.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerManager,
    CircuitState,
)


class TestCircuitBreaker:
    def test_open_on_failures(self):
        cb = CircuitBreaker("test_service", failure_threshold=3, recovery_timeout=1.0)
        assert cb.can_proceed()
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert not cb.can_proceed()

    def test_recovery(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.01)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        time.sleep(0.02)
        assert cb.can_proceed()
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitState.CLOSED


class TestCircuitBreakerManager:
    def test_register_and_trip(self):
        cbm = CircuitBreakerManager()
        cb = CircuitBreaker("api_service", failure_threshold=2, recovery_timeout=30)
        cbm.register(cb)
        assert cbm.can_proceed("api_service")
        cbm.record_failure("api_service")
        cbm.record_failure("api_service")
        assert not cbm.can_proceed("api_service")
        assert cbm.get("api_service").state == CircuitState.OPEN

    def test_defaults_for_unregistered(self):
        cbm = CircuitBreakerManager()
        assert cbm.can_proceed("unregistered_service")
