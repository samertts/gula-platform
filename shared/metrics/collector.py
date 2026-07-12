from __future__ import annotations

import logging
import time
from collections import defaultdict
from threading import Lock
from typing import Any

logger = logging.getLogger("gula.metrics")


class Counter:
    def __init__(self, name: str, help_text: str = "", labels: dict[str, str] | None = None):
        self.name = name
        self.help_text = help_text
        self.labels = labels or {}
        self._value: float = 0
        self._lock = Lock()

    def inc(self, amount: float = 1.0) -> None:
        with self._lock:
            self._value += amount

    def value(self) -> float:
        with self._lock:
            return self._value

    def reset(self) -> None:
        with self._lock:
            self._value = 0


class Gauge:
    def __init__(self, name: str, help_text: str = "", labels: dict[str, str] | None = None):
        self.name = name
        self.help_text = help_text
        self.labels = labels or {}
        self._value: float = 0
        self._lock = Lock()

    def set(self, value: float) -> None:
        with self._lock:
            self._value = value

    def inc(self, amount: float = 1.0) -> None:
        with self._lock:
            self._value += amount

    def dec(self, amount: float = 1.0) -> None:
        with self._lock:
            self._value -= amount

    def value(self) -> float:
        with self._lock:
            return self._value


class Histogram:
    def __init__(self, name: str, help_text: str = "", buckets: list[float] | None = None):
        self.name = name
        self.help_text = help_text
        self.buckets = sorted(buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
        self._counts: dict[float, float] = {b: 0.0 for b in self.buckets}
        self._total: float = 0.0
        self._sum: float = 0.0
        self._lock = Lock()

    def observe(self, value: float) -> None:
        with self._lock:
            self._sum += value
            self._total += 1.0
            for b in self.buckets:
                if value <= b:
                    self._counts[b] += 1.0
                    break

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "buckets": dict(self._counts),
                "total": self._total,
                "sum": self._sum,
            }


class MetricsCollector:
    def __init__(self, prefix: str = "gula"):
        self._prefix = prefix
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}
        self._lock = Lock()

    def counter(self, name: str, help_text: str = "", labels: dict[str, str] | None = None) -> Counter:
        full = f"{self._prefix}_{name}"
        with self._lock:
            if full not in self._counters:
                self._counters[full] = Counter(full, help_text, labels)
            return self._counters[full]

    def gauge(self, name: str, help_text: str = "", labels: dict[str, str] | None = None) -> Gauge:
        full = f"{self._prefix}_{name}"
        with self._lock:
            if full not in self._gauges:
                self._gauges[full] = Gauge(full, help_text, labels)
            return self._gauges[full]

    def histogram(self, name: str, help_text: str = "", buckets: list[float] | None = None) -> Histogram:
        full = f"{self._prefix}_{name}"
        with self._lock:
            if full not in self._histograms:
                self._histograms[full] = Histogram(full, help_text, buckets)
            return self._histograms[full]

    def prometheus_output(self) -> str:
        lines: list[str] = []
        for c in self._counters.values():
            lines.append(f"# HELP {c.name} {c.help_text}")
            lines.append(f"# TYPE {c.name} counter")
            labels = ",".join(f'{k}="{v}"' for k, v in c.labels.items())
            suffix = "{" + labels + "}" if labels else ""
            lines.append(f"{c.name}{suffix} {c.value()}")
        for g in self._gauges.values():
            lines.append(f"# HELP {g.name} {g.help_text}")
            lines.append(f"# TYPE {g.name} gauge")
            labels = ",".join(f'{k}="{v}"' for k, v in g.labels.items())
            suffix = "{" + labels + "}" if labels else ""
            lines.append(f"{g.name}{suffix} {g.value()}")
        for h in self._histograms.values():
            snap = h.snapshot()
            lines.append(f"# HELP {h.name} {h.help_text}")
            lines.append(f"# TYPE {h.name} histogram")
            labels_str = ""
            for bucket, count in snap["buckets"].items():
                lines.append(f'{h.name}_bucket{{{labels_str}le="{bucket}"}} {int(count)}')
            lines.append(f'{h.name}_bucket{{{labels_str}le="+Inf"}} {int(snap["total"])}')
            lines.append(f"{h.name}_total {int(snap['total'])}")
            lines.append(f"{h.name}_sum {snap['sum']}")
        return "\n".join(lines) + "\n"


metrics = MetricsCollector()


def track_time(metric_name: str, labels: dict[str, str] | None = None):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = fn(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                metrics.histogram(metric_name, labels=labels).observe(duration)
        return wrapper
    return decorator
