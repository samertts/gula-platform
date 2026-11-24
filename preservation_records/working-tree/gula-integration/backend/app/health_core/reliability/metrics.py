"""In-memory counters, gauges and timers with a PII-safe snapshot/export.

Metric names are restricted to lowercase snake-case codes and metric values are
strictly numeric, so patient identifiers, free text and labels cannot enter the
registry. Nothing is sent to any telemetry backend.
"""

from __future__ import annotations

import math
import re

from app.health_core.reliability.errors import InvalidMetricNameError
from app.health_core.reliability.hashing import canonical_json_bytes

_METRIC_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")


class MetricsRegistry:
    """Process-local numeric metrics with deterministic JSON export."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = {}
        self._gauges: dict[str, float] = {}
        self._timers: dict[str, list[float]] = {}

    @staticmethod
    def _check_name(name: object) -> str:
        if not isinstance(name, str) or not _METRIC_NAME_RE.fullmatch(name):
            raise InvalidMetricNameError(
                "metric name must be a lowercase snake-case code",
                details={"field": "name"},
            )
        return name

    @staticmethod
    def _check_number(value: object, *, field: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise InvalidMetricNameError(
                f"{field} must be numeric", details={"field": field}
            )
        number = float(value)
        if not math.isfinite(number):
            raise InvalidMetricNameError(f"{field} must be finite", details={"field": field})
        return number

    def increment(self, name: str, value: int = 1) -> None:
        """Increment a counter by a positive integer."""
        safe_name = self._check_name(name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise InvalidMetricNameError("counter increment must be a positive integer")
        self._counters[safe_name] = self._counters.get(safe_name, 0) + value

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge to a finite numeric value."""
        safe_name = self._check_name(name)
        self._gauges[safe_name] = self._check_number(value, field="value")

    def record_duration(self, name: str, duration_ms: float) -> None:
        """Record one non-negative finite duration (in milliseconds)."""
        safe_name = self._check_name(name)
        duration = self._check_number(duration_ms, field="duration_ms")
        if duration < 0:
            raise InvalidMetricNameError("duration_ms must be non-negative")
        self._timers.setdefault(safe_name, []).append(duration)

    @property
    def counters(self) -> dict[str, int]:
        """Defensive copy of counters."""
        return dict(self._counters)

    @property
    def gauges(self) -> dict[str, float]:
        """Defensive copy of gauges."""
        return dict(self._gauges)

    def timer_stats(self) -> dict[str, dict[str, float | int]]:
        """Count, total, min and max for each recorded timer."""
        stats: dict[str, dict[str, float | int]] = {}
        for name, values in self._timers.items():
            stats[name] = {
                "count": len(values),
                "total_ms": sum(values),
                "min_ms": min(values),
                "max_ms": max(values),
            }
        return stats

    def snapshot(self) -> dict[str, object]:
        """Return a stable, JSON-compatible snapshot of all metrics."""
        return {
            "schema": "gula-reliability-metrics-v1",
            "counters": self.counters,
            "gauges": self.gauges,
            "timers": self.timer_stats(),
        }

    def export_bytes(self) -> bytes:
        """Export the snapshot as deterministic, numeric-only JSON bytes."""
        return canonical_json_bytes(self.snapshot())
