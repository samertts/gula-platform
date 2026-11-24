"""Deterministic retry/backoff, dead-lettering and in-memory metric tests."""

from __future__ import annotations

import json
from collections.abc import Callable

import pytest
from app.health_core.common.errors import InvalidSyntheticReferenceError
from app.health_core.reliability import (
    BackoffPolicy,
    InvalidMetricNameError,
    MetricsRegistry,
    RetryExecutor,
    RetryStatus,
)


def _always_fails() -> str:
    raise RuntimeError("synthetic downstream failure")


def test_backoff_is_bounded_exponential_and_jitter_free() -> None:
    policy = BackoffPolicy(base_delay_ms=2, multiplier=2, max_delay_ms=8, max_attempts=5)
    assert tuple(policy.delay_for(attempt) for attempt in range(1, 6)) == (2, 4, 8, 8, 0)
    assert policy.planned_delays() == (2, 4, 8, 8)
    assert policy.delay_for(1) == policy.delay_for(1)


def test_invalid_backoff_policy_is_rejected() -> None:
    with pytest.raises(ValueError):
        BackoffPolicy(base_delay_ms=0)
    with pytest.raises(ValueError):
        BackoffPolicy(max_attempts=0)


def test_success_after_two_retries_reports_attempts_and_delays() -> None:
    policy = BackoffPolicy(base_delay_ms=2, multiplier=2, max_delay_ms=16, max_attempts=4)
    calls = 0

    def flaky() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ValueError("synthetic transient failure")
        return "SYN-RESULT-OK"

    outcome = RetryExecutor(policy).execute("SYN-OP-000001", flaky, payload={"attempt": calls})
    assert outcome.status is RetryStatus.SUCCEEDED
    assert outcome.attempts == 3
    assert outcome.delays_ms == (2, 4)
    assert outcome.result == "SYN-RESULT-OK"
    assert outcome.last_error is None
    assert calls == 3


def test_terminal_failure_is_dead_lettered_with_deterministic_entry() -> None:
    policy = BackoffPolicy(base_delay_ms=2, multiplier=2, max_delay_ms=8, max_attempts=3)
    first = RetryExecutor(policy)
    second = RetryExecutor(policy)
    outcome_a = first.execute("SYN-OP-000002", _always_fails, payload={"v": 1})
    outcome_b = second.execute("SYN-OP-000002", _always_fails, payload={"v": 1})
    assert outcome_a.status is RetryStatus.DEAD_LETTERED
    assert outcome_a.attempts == 3
    assert outcome_a.delays_ms == (2, 4)
    assert outcome_a.result is None
    assert outcome_a.last_error and "synthetic downstream failure" in outcome_a.last_error
    assert outcome_a == outcome_b
    assert len(first.dead_letters) == 1
    letter = first.dead_letters[0]
    assert letter.letter_id.startswith("SYN-DLQ-")
    assert letter.operation_id == "SYN-OP-000002"
    assert letter.reason == "max_attempts_exhausted"
    assert letter.attempts == 3
    assert len(letter.payload_digest) == 64


def test_single_attempt_policy_applies_no_delay() -> None:
    outcome = RetryExecutor(BackoffPolicy(max_attempts=1)).execute(
        "SYN-OP-000003", _always_fails
    )
    assert outcome.attempts == 1
    assert outcome.delays_ms == ()
    assert outcome.status is RetryStatus.DEAD_LETTERED


def test_operation_id_must_be_synthetic() -> None:
    with pytest.raises(InvalidSyntheticReferenceError):
        RetryExecutor().execute("OP-1", lambda: "ok")


def test_counters_gauges_and_timers_snapshot() -> None:
    registry = MetricsRegistry()
    registry.increment("events_seen", 3)
    registry.increment("events_seen", 2)
    registry.set_gauge("queue_depth", 7.5)
    registry.record_duration("replay_ms", 4.0)
    registry.record_duration("replay_ms", 1.0)
    registry.record_duration("replay_ms", 3.0)
    snapshot = registry.snapshot()
    assert snapshot["counters"] == {"events_seen": 5}
    assert snapshot["gauges"] == {"queue_depth": 7.5}
    assert snapshot["timers"] == {
        "replay_ms": {"count": 3, "total_ms": 8.0, "min_ms": 1.0, "max_ms": 4.0}
    }
    exported = json.loads(registry.export_bytes())
    assert exported["counters"]["events_seen"] == 5


def test_metrics_reject_free_text_and_non_numeric_values() -> None:
    registry = MetricsRegistry()
    with pytest.raises(InvalidMetricNameError):
        registry.increment("SYN-PAT-000001")
    with pytest.raises(InvalidMetricNameError):
        registry.set_gauge("queue_depth", "42")  # type: ignore[arg-type]
    with pytest.raises(InvalidMetricNameError):
        registry.record_duration("replay_ms", -1.0)
    with pytest.raises(InvalidMetricNameError):
        registry.increment("events_seen", 0)
    assert registry.snapshot()["counters"] == {}


def test_metric_export_contains_no_pii_or_free_text() -> None:
    registry = MetricsRegistry()
    registry.increment("events_seen", 1)
    registry.set_gauge("queue_depth", 2)
    registry.record_duration("replay_ms", 0.5)
    raw = registry.export_bytes().decode("utf-8")
    assert "SYN-" not in raw
    assert "patient" not in raw
    assert all(isinstance(value, (int, float)) for value in registry.counters.values())
    assert all(isinstance(value, (int, float)) for value in registry.gauges.values())


def test_callable_operation_receives_no_arguments() -> None:
    marker: list[str] = []

    def operation() -> str:
        marker.append("called")
        return "SYN-OK"

    result: Callable[[], str] = operation
    assert RetryExecutor().execute("SYN-OP-000004", result).result == "SYN-OK"
    assert marker == ["called"]
