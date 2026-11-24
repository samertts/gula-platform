"""Honest in-memory load harness with measured latency and throughput.

The harness processes synthetic events through the idempotency processor, the WAL
store and the hash-chained audit log, then replays the same keys to exercise the
duplicate path. Every reported number is derived from ``time.perf_counter`` readings
taken by this module; there are no hardcoded or estimated performance figures and
no sleeping. An optional injected clock exists only to unit-test the statistics.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from app.health_core.reliability.audit import AuditLog
from app.health_core.reliability.durable import InMemoryWALStore
from app.health_core.reliability.idempotency import IdempotentProcessor, ProcessStatus

Clock = Callable[[], float]


@dataclass(frozen=True, slots=True)
class PerformanceMeasurement:
    """Measured results; all latency fields are in milliseconds."""

    scenario: str
    operations: int
    elapsed_ms: float
    throughput_ops_per_sec: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_max_ms: float
    finalize_ms: float
    durations_ms: tuple[float, ...]


def percentile(values: Sequence[float], fraction: float) -> float:
    """Nearest-rank percentile of a numeric sequence (no interpolation)."""
    if not values or not 0 < fraction <= 1:
        raise ValueError("percentile requires values and a fraction in (0, 1]")
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))
    return ordered[index]


def summarize_durations(
    durations: Sequence[float],
    *,
    scenario: str,
    elapsed_ms: float,
    finalize_ms: float,
) -> PerformanceMeasurement:
    """Derive a measurement from actually collected per-operation durations."""
    if not durations:
        raise ValueError("at least one duration is required")
    if elapsed_ms <= 0 or finalize_ms < 0:
        raise ValueError("elapsed_ms must be positive and finalize_ms non-negative")
    if any(not math.isfinite(value) or value < 0 for value in durations):
        raise ValueError("durations must be finite and non-negative")
    return PerformanceMeasurement(
        scenario=scenario,
        operations=len(durations),
        elapsed_ms=elapsed_ms,
        throughput_ops_per_sec=len(durations) / (elapsed_ms / 1000.0),
        latency_p50_ms=percentile(durations, 0.50),
        latency_p95_ms=percentile(durations, 0.95),
        latency_max_ms=max(durations),
        finalize_ms=finalize_ms,
        durations_ms=tuple(durations),
    )


def run_pipeline_load(event_count: int, *, clock: Clock = time.perf_counter) -> PerformanceMeasurement:
    """Measure enqueue and replay of ``event_count`` synthetic events.

    Internal correctness checks raise if any event is dropped, duplicated, missing
    or if the audit chain or restart recovery fails; a returned measurement always
    represents a functionally correct run.
    """
    if event_count < 1:
        raise ValueError("event_count must be at least 1")
    processor = IdempotentProcessor()
    store = InMemoryWALStore()
    audit = AuditLog()
    durations: list[float] = []
    recorded_at = "2026-01-01T00:00:00+00:00"

    def request_payload(index: int) -> dict[str, object]:
        return {"sequence": index, "event_id": f"SYN-EVT-{index:06d}"}

    run_start = clock()
    for index in range(event_count):
        key = f"SYN-KEY-{index:06d}"
        event_id = f"SYN-EVT-{index:06d}"
        started = clock()
        processor.process(key, request_payload(index))
        store.put(event_id, {"sequence": index, "action": "synthetic_enqueue"})
        audit.append(
            subject_id=f"SYN-SUB-{index:06d}",
            actor="SYN-NODE-LOAD",
            action="event_enqueued",
            summary="synthetic_enqueue",
            recorded_at=recorded_at,
            payload={"event_id": event_id},
        )
        durations.append((clock() - started) * 1000.0)

    for index in range(event_count):
        key = f"SYN-KEY-{index:06d}"
        event_id = f"SYN-EVT-{index:06d}"
        started = clock()
        replay = processor.process(key, request_payload(index))
        stored = store.get(event_id)
        durations.append((clock() - started) * 1000.0)
        if replay.status is not ProcessStatus.DUPLICATE or stored is None:
            raise AssertionError("replay did not resolve to the original stored effect")

    elapsed_ms = (clock() - run_start) * 1000.0
    finalize_started = clock()
    store.commit()
    verification = audit.verify()
    restarted = store.simulate_restart()
    finalize_ms = (clock() - finalize_started) * 1000.0
    if processor.effect_count != event_count:
        raise AssertionError("idempotency processor created an unexpected number of effects")
    if len(store.data) != event_count or not verification.ok:
        raise AssertionError("store or audit verification failed during load run")
    if restarted.data != store.data or len(restarted.data) != event_count:
        raise AssertionError("simulated restart did not preserve committed state")

    return summarize_durations(
        durations,
        scenario="synthetic_enqueue_replay",
        elapsed_ms=elapsed_ms,
        finalize_ms=finalize_ms,
    )
