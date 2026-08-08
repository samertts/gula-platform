import time
from enum import Enum
from typing import Any


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class Metric:
    def __init__(self, name: str, metric_type: MetricType, value: float, labels: dict[str, str] | None = None):
        self.name = name
        self.type = metric_type
        self.value = value
        self.labels = labels or {}
        self.timestamp = time.time()


class MetricsCollector:
    def __init__(self):
        self._counters: dict[str, dict[str, float]] = {}
        self._gauges: dict[str, dict[str, float]] = {}
        self._histograms: dict[str, dict[str, list[float]]] = {}

    def increment(self, name: str, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        key = str(sorted((labels or {}).items()))
        self._counters.setdefault(name, {}).setdefault(key, 0.0)
        self._counters[name][key] += value

    def gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = str(sorted((labels or {}).items()))
        self._gauges.setdefault(name, {})[key] = value

    def observe(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = str(sorted((labels or {}).items()))
        self._histograms.setdefault(name, {}).setdefault(key, []).append(value)

    def get_counter(self, name: str, labels: dict[str, str] | None = None) -> float:
        key = str(sorted((labels or {}).items()))
        return self._counters.get(name, {}).get(key, 0.0)

    def get_gauge(self, name: str, labels: dict[str, str] | None = None) -> float | None:
        key = str(sorted((labels or {}).items()))
        return self._gauges.get(name, {}).get(key)

    def snapshot(self) -> dict[str, Any]:
        return {
            "counters": {k: dict(v) for k, v in self._counters.items()},
            "gauges": {k: dict(v) for k, v in self._gauges.items()},
            "histograms": {
                k: {sk: {"count": len(sv), "sum": sum(sv), "avg": sum(sv) / len(sv) if sv else 0}
                    for sk, sv in svs.items()}
                for k, svs in self._histograms.items()
            },
        }

    def reset(self) -> None:
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
