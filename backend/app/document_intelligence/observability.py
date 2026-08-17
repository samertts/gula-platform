from __future__ import annotations

import json
import logging
import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC

logger = logging.getLogger(__name__)

_current_span: ContextVar[str | None] = ContextVar("current_span", default=None)


@dataclass
class Span:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str | None = None
    operation: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    duration_ms: float = 0.0
    status: str = "ok"
    tags: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class MetricPoint:
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    def __init__(self):
        self._counters: dict[str, int] = defaultdict(int)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._points: list[MetricPoint] = []

    def increment(self, name: str, value: int = 1):
        self._counters[name] += value

    def gauge(self, name: str, value: float):
        self._gauges[name] = value

    def histogram(self, name: str, value: float):
        self._histograms[name].append(value)

    def record(self, name: str, value: float, tags: dict[str, str] | None = None):
        self._points.append(MetricPoint(name=name, value=value, tags=tags or {}))

    def snapshot(self) -> dict[str, Any]:
        histograms = {}
        for name, values in self._histograms.items():
            if values:
                sorted_vals = sorted(values)
                n = len(sorted_vals)
                histograms[name] = {
                    "min": sorted_vals[0],
                    "max": sorted_vals[-1],
                    "avg": sum(sorted_vals) / n,
                    "p50": sorted_vals[n // 2],
                    "p95": sorted_vals[int(n * 0.95)],
                    "p99": sorted_vals[int(n * 0.99)],
                    "count": n,
                }
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": histograms,
        }

    def reset(self):
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._points.clear()


_metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    return _metrics


class Tracer:
    def __init__(self):
        self._spans: dict[str, Span] = {}
        self._enabled = True

    def start_span(self, operation: str, tags: dict[str, Any] | None = None) -> Span:
        parent = _current_span.get()
        span = Span(
            operation=operation,
            parent_id=parent,
            tags=tags or {},
        )
        self._spans[span.id] = span
        _current_span.set(span.id)
        return span

    def end_span(self, span_id: str, status: str = "ok"):
        span = self._spans.get(span_id)
        if span:
            span.end_time = time.time()
            span.duration_ms = (span.end_time - span.start_time) * 1000
            span.status = status
            get_metrics().histogram(f"span.duration.{span.operation}", span.duration_ms)

    def add_event(self, span_id: str, name: str, attributes: dict[str, Any] | None = None):
        span = self._spans.get(span_id)
        if span:
            span.events.append({
                "name": name,
                "timestamp": time.time(),
                "attributes": attributes or {},
            })

    def get_span(self, span_id: str) -> Span | None:
        return self._spans.get(span_id)

    def trace(self, operation: str):
        def decorator(func: Callable) -> Callable:
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                span = self.start_span(operation)
                try:
                    result = await func(*args, **kwargs)
                    self.end_span(span.id, "ok")
                    return result
                except Exception as e:
                    self.end_span(span.id, "error")
                    self.add_event(span.id, "error", {"error": str(e)})
                    raise
            return wrapper
        return decorator

    def get_trace(self, span_id: str) -> list[dict[str, Any]]:
        trace: list[dict[str, Any]] = []
        current = self._spans.get(span_id)
        while current:
            trace.append({
                "id": current.id,
                "operation": current.operation,
                "duration_ms": current.duration_ms,
                "status": current.status,
                "tags": current.tags,
            })
            if current.parent_id:
                current = self._spans.get(current.parent_id)
            else:
                break
        return trace


_tracer = Tracer()


def get_tracer() -> Tracer:
    return _tracer


class HealthChecker:
    def __init__(self):
        self._checks: dict[str, Callable] = {}
        self._results: dict[str, dict[str, Any]] = {}

    def register(self, name: str, check_fn: Callable):
        self._checks[name] = check_fn

    def unregister(self, name: str):
        self._checks.pop(name, None)

    async def run_all(self) -> dict[str, Any]:
        results = {}
        all_ok = True
        for name, check_fn in self._checks.items():
            try:
                result = await check_fn()
                status = "healthy" if result.get("ok", False) else "unhealthy"
                if not result.get("ok", False):
                    all_ok = False
                results[name] = {"status": status, **result}
            except Exception as e:
                all_ok = False
                results[name] = {"status": "unhealthy", "error": str(e)}
        self._results = results
        return {
            "status": "healthy" if all_ok else "degraded",
            "checks": results,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def get_results(self) -> dict[str, Any]:
        return self._results

    def is_healthy(self) -> bool:
        return all(r.get("status") == "healthy" for r in self._results.values())


class StructuredLogger:
    def __init__(self, service_name: str = "document_intelligence"):
        self._service = service_name

    def _log(self, level: str, message: str, **kwargs: Any):
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "service": self._service,
            "level": level,
            "message": message,
            "tenant": _current_span.get(),
            **kwargs,
        }
        logger.log(
            getattr(logging, level.upper(), logging.INFO),
            json.dumps(record, default=str),
        )

    def info(self, message: str, **kwargs: Any):
        self._log("info", message, **kwargs)

    def error(self, message: str, **kwargs: Any):
        self._log("error", message, **kwargs)

    def warning(self, message: str, **kwargs: Any):
        self._log("warning", message, **kwargs)

    def debug(self, message: str, **kwargs: Any):
        self._log("debug", message, **kwargs)

    def critical(self, message: str, **kwargs: Any):
        self._log("critical", message, **kwargs)


_structured_logger = StructuredLogger()


def get_logger() -> StructuredLogger:
    return _structured_logger


class AlertManager:
    def __init__(self):
        self._rules: list[dict[str, Any]] = []
        self._alerts: list[dict[str, Any]] = []
        self._handlers: list[Callable] = []

    def add_rule(self, name: str, condition: Callable, severity: str = "warning", message: str = ""):
        self._rules.append({
            "name": name,
            "condition": condition,
            "severity": severity,
            "message": message,
        })

    def add_handler(self, handler: Callable):
        self._handlers.append(handler)

    async def evaluate(self, metrics_snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        triggered = []
        for rule in self._rules:
            try:
                if await rule["condition"](metrics_snapshot):
                    alert = {
                        "rule": rule["name"],
                        "severity": rule["severity"],
                        "message": rule["message"],
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                    triggered.append(alert)
                    self._alerts.append(alert)
                    for handler in self._handlers:
                        try:
                            await handler(alert)
                        except Exception:
                            logger.exception("Alert handler failed")
            except Exception as e:
                logger.error("Alert rule evaluation failed: %s", e)
        return triggered

    def get_alerts(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._alerts[-limit:]

    def clear_alerts(self):
        self._alerts.clear()
