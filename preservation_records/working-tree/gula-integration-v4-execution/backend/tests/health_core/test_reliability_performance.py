"""Measured in-memory load harness tests (honest numbers, loose sanity bounds)."""

from __future__ import annotations

import math

import pytest
from app.health_core.reliability import (
    percentile,
    run_pipeline_load,
    summarize_durations,
)


def test_measured_pipeline_load_1000_events() -> None:
    measurement = run_pipeline_load(1000)
    assert measurement.scenario == "synthetic_enqueue_replay"
    assert measurement.operations == 2000
    assert len(measurement.durations_ms) == 2000
    assert measurement.elapsed_ms > 0
    assert measurement.finalize_ms >= 0
    assert measurement.throughput_ops_per_sec == pytest.approx(
        measurement.operations / (measurement.elapsed_ms / 1000.0)
    )
    assert measurement.latency_p50_ms <= measurement.latency_p95_ms <= measurement.latency_max_ms
    assert math.isfinite(measurement.throughput_ops_per_sec)
    # Deliberately loose sanity bound: in-memory work must be meaningfully faster
    # than 1 op/s. No tight latency threshold is asserted (it would be flaky).
    assert measurement.throughput_ops_per_sec > 1.0


def test_statistics_are_derived_from_supplied_measurements() -> None:
    durations = (4.0, 1.0, 3.0, 2.0)
    measurement = summarize_durations(
        durations, scenario="unit_statistics", elapsed_ms=20.0, finalize_ms=1.5
    )
    assert measurement.operations == 4
    assert measurement.throughput_ops_per_sec == pytest.approx(4 / 0.020)
    assert measurement.latency_p50_ms == percentile(durations, 0.50)
    assert measurement.latency_p95_ms == percentile(durations, 0.95)
    assert measurement.latency_max_ms == 4.0
    assert measurement.durations_ms == durations
    assert measurement.finalize_ms == 1.5


def test_injected_deterministic_clock_produces_exact_durations() -> None:
    class SteppingClock:
        def __init__(self) -> None:
            self.calls = 0

        def __call__(self) -> float:
            self.calls += 1
            return self.calls * 0.001

    clock = SteppingClock()
    measurement = run_pipeline_load(4, clock=clock)
    assert measurement.operations == 8
    # Exact clock subtraction is subject to IEEE-754 rounding, hence approx here.
    assert measurement.durations_ms == pytest.approx((1.0,) * 8)
    assert measurement.latency_p50_ms == pytest.approx(1.0)
    assert measurement.latency_p95_ms == pytest.approx(1.0)
    assert measurement.latency_max_ms == pytest.approx(1.0)
    assert measurement.throughput_ops_per_sec == pytest.approx(
        measurement.operations / (measurement.elapsed_ms / 1000.0)
    )
    assert measurement.finalize_ms == pytest.approx(1.0)


def test_invalid_harness_inputs_are_rejected() -> None:
    with pytest.raises(ValueError):
        run_pipeline_load(0)
    with pytest.raises(ValueError):
        summarize_durations((), scenario="empty", elapsed_ms=1.0, finalize_ms=0.0)
    with pytest.raises(ValueError):
        percentile((1.0, 2.0), 0.0)
