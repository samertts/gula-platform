from __future__ import annotations

import os
import threading
import time

import pytest

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

from shared.circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState


def test_initial_state_closed() -> None:
    cb = CircuitBreaker("t", failure_threshold=3, recovery_timeout=30)
    assert cb.state == CircuitState.CLOSED
    assert cb.allow_request() is True


def test_allow_request_open_after_threshold() -> None:
    cb = CircuitBreaker("t", failure_threshold=3, recovery_timeout=30)
    for _ in range(3):
        cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.allow_request() is False


def test_record_success_closes_half_open() -> None:
    cb = CircuitBreaker("t", failure_threshold=2, recovery_timeout=0.05)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    time.sleep(0.06)
    assert cb.state == CircuitState.HALF_OPEN
    assert cb.allow_request() is True
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


def test_half_open_capacity_limited() -> None:
    cb = CircuitBreaker("t", failure_threshold=2, recovery_timeout=0.05, half_open_max_calls=1)
    cb.record_failure()
    cb.record_failure()
    time.sleep(0.06)
    assert cb.allow_request() is True
    assert cb.allow_request() is False
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


def test_reset() -> None:
    cb = CircuitBreaker("t", failure_threshold=1, recovery_timeout=30)
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert cb.allow_request() is True


def test_call_success_and_failure_paths() -> None:
    cb = CircuitBreaker("t", failure_threshold=2, recovery_timeout=30)
    assert cb.call(lambda: 42) == 42
    for _ in range(2):
        with pytest.raises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert cb.state == CircuitState.OPEN
    with pytest.raises(CircuitOpenError):
        cb.call(lambda: 1)


def test_concurrent_record_failure_is_safe() -> None:
    cb = CircuitBreaker("t", failure_threshold=10, recovery_timeout=30)
    errors: list[Exception] = []

    def worker() -> None:
        try:
            for _ in range(50):
                cb.record_failure()
                cb.allow_request()
        except Exception as exc:  # pragma: no cover - assertion only
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert cb._failure_count == 400


def test_notifications_style_protocol() -> None:
    """Regression: notifications/service.py calls allow_request/record_* directly."""
    cb = CircuitBreaker("notification", failure_threshold=10, recovery_timeout=30)
    assert cb.allow_request()
    cb.record_success()
    for _ in range(10):
        cb.record_failure()
    assert not cb.allow_request()
    assert cb.record_success is not None
    assert cb.record_failure is not None
    assert cb.allow_request is not None
