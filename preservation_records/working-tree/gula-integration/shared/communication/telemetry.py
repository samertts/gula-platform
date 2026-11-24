"""Dependency-free telemetry for the GULA Communication Platform Core.

Thread-safe counters + latency summary with a Prometheus text exposition
hook — no external libraries, cloud-independent, pluggable into the
platform /metrics endpoint.
"""

from __future__ import annotations

import threading
from typing import Any, ClassVar


class CommunicationTelemetry:
    _lock = threading.Lock()
    _dispatches_total: ClassVar[dict[str, int]] = {}
    _attempts_total: ClassVar[dict[str, int]] = {}
    _latency_sum = 0.0
    _latency_count = 0
    _failures_total: ClassVar[dict[str, int]] = {}
    _escalations_total = 0

    @classmethod
    def record_dispatch(cls, policy_id: str) -> None:
        with cls._lock:
            cls._dispatches_total[policy_id] = cls._dispatches_total.get(policy_id, 0) + 1

    @classmethod
    def record_attempt(cls, channel: str, ok: bool) -> None:
        with cls._lock:
            state = "ok" if ok else "fail"
            cls._attempts_total[(channel, state)] = cls._attempts_total.get((channel, state), 0) + 1

    @classmethod
    def record_latency(cls, seconds: float) -> None:
        with cls._lock:
            cls._latency_sum += seconds
            cls._latency_count += 1

    @classmethod
    def record_failure(cls, stage: str) -> None:
        with cls._lock:
            cls._failures_total[stage] = cls._failures_total.get(stage, 0) + 1

    @classmethod
    def record_escalation(cls) -> None:
        with cls._lock:
            cls._escalations_total += 1

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._dispatches_total.clear()
            cls._attempts_total.clear()
            cls._latency_sum = 0.0
            cls._latency_count = 0
            cls._failures_total.clear()
            cls._escalations_total = 0

    @classmethod
    def snapshot(cls) -> dict[str, Any]:
        with cls._lock:
            return {
                "dispatches_total": dict(cls._dispatches_total),
                "attempts_total": dict(cls._attempts_total),
                "latency_sum": cls._latency_sum,
                "latency_count": cls._latency_count,
                "failures_total": dict(cls._failures_total),
                "escalations_total": cls._escalations_total,
            }


def _escape_label(value: Any) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def append_prometheus_metrics() -> str:
    """Prometheus text exposition for communication-core metrics."""
    snap = CommunicationTelemetry.snapshot()
    lines: list[str] = []
    lines.append("# HELP gula_communication_dispatches_total Dispatches by policy")
    lines.append("# TYPE gula_communication_dispatches_total counter")
    for policy_id, count in sorted(snap["dispatches_total"].items()):
        lines.append(
            f'gula_communication_dispatches_total{{policy="{_escape_label(policy_id)}"}} {count}',
        )
    lines.append("")
    lines.append("# HELP gula_communication_attempts_total Provider attempts by channel/result")
    lines.append("# TYPE gula_communication_attempts_total counter")
    for (channel, state), count in sorted(snap["attempts_total"].items()):
        lines.append(
            f'gula_communication_attempts_total{{channel="{_escape_label(channel)}",'
            f'state="{_escape_label(state)}"}} {count}',
        )
    lines.append("")
    count = snap["latency_count"]
    lines.append("# HELP gula_communication_latency_seconds Dispatch latency")
    lines.append("# TYPE gula_communication_latency_seconds summary")
    lines.append(f"gula_communication_latency_seconds_sum {round(snap['latency_sum'], 9)}")
    lines.append(f"gula_communication_latency_seconds_count {count}")
    lines.append("")
    lines.append("# HELP gula_communication_failures_total Core failures by stage")
    lines.append("# TYPE gula_communication_failures_total counter")
    for stage, cnt in sorted(snap["failures_total"].items()):
        lines.append(f'gula_communication_failures_total{{stage="{_escape_label(stage)}"}} {cnt}')
    lines.append("")
    lines.append("# HELP gula_communication_escalations_total Policy escalations triggered")
    lines.append("# TYPE gula_communication_escalations_total counter")
    lines.append(f"gula_communication_escalations_total {snap['escalations_total']}")
    lines.append("")
    return "\n".join(lines) + "\n"


__all__ = ["CommunicationTelemetry", "append_prometheus_metrics"]
