"""Phase 13 — Observability Engine.

Metrics, tracing, logging, audit trail, timeline, and the five graphs:
mission, execution, resource, knowledge, and decision. Every execution is
observable, auditable, and reproducible.
"""

from __future__ import annotations

from typing import Any

from .core import MetricPoint, Span, utcnow


class MetricsRegistry:
    """Collect metric samples and produce summary snapshots."""

    def __init__(self) -> None:
        self._samples: list[MetricPoint] = []

    def record(self, metric: str, value: float, **tags: str) -> MetricPoint:
        point = MetricPoint(metric=metric, value=value, tags=tags)
        self._samples.append(point)
        return point

    def summary(self, metric: str | None = None) -> dict[str, float]:
        relevant = [s for s in self._samples if metric is None or s.metric == metric]
        if not relevant:
            return {}
        values = [s.value for s in relevant]
        return {
            "count": len(values),
            "sum": round(sum(values), 3),
            "mean": round(sum(values) / len(values), 3),
            "min": round(min(values), 3),
            "max": round(max(values), 3),
        }

    def export(self) -> list[dict[str, Any]]:
        return [vars(point) for point in self._samples]


class Tracer:
    """Nested span tracing for reproducible execution."""

    def __init__(self) -> None:
        self._spans: list[Span] = []
        self._open: dict[str, Span] = {}

    def start(self, span_id: str, name: str, engine: str, parent: str = "") -> Span:
        span = Span(span_id=span_id, name=name, engine=engine, parent=parent)
        self._open[span_id] = span
        return span

    def end(self, span_id: str, duration_ms: float = 0.0, status: str = "ok", detail: str = "") -> Span:
        span = self._open.pop(span_id, None)
        if span is None:
            raise KeyError(f"unknown span '{span_id}'")
        span.duration_ms = duration_ms
        span.status = status
        span.detail = detail
        self._spans.append(span)
        return span

    def export(self) -> list[dict[str, Any]]:
        return [vars(span) for span in self._spans]


class AuditLog:
    """Immutable-style audit trail: entries may only be appended."""

    def __init__(self) -> None:
        self._entries: list[dict[str, str]] = []

    def record(self, actor: str, action: str, resource: str = "", detail: str = "") -> dict[str, str]:
        entry = {
            "timestamp": utcnow(),
            "actor": actor,
            "action": action,
            "resource": resource,
            "detail": detail,
        }
        self._entries.append(entry)
        return entry

    def export(self) -> list[dict[str, str]]:
        return list(self._entries)

    def find(self, actor: str | None = None, action: str | None = None) -> list[dict[str, str]]:
        return [
            e for e in self._entries
            if (actor is None or e["actor"] == actor)
            and (action is None or e["action"] == action)
        ]


class Timeline:
    """An ordered execution timeline."""

    def __init__(self) -> None:
        self._events: list[dict[str, str]] = []

    def event(self, kind: str, detail: str = "") -> dict[str, str]:
        entry = {"timestamp": utcnow(), "kind": kind, "detail": detail}
        self._events.append(entry)
        return entry

    def export(self) -> list[dict[str, str]]:
        return list(self._events)


def mission_graph(nodes: list[str], edges: list[tuple[str, str]]) -> dict[str, Any]:
    return {"kind": "mission", "nodes": nodes, "edges": [list(e) for e in edges]}


def execution_graph(nodes: list[str], edges: list[tuple[str, str]]) -> dict[str, Any]:
    return {"kind": "execution", "nodes": nodes, "edges": [list(e) for e in edges]}


def resource_graph(usage: dict[str, float]) -> dict[str, Any]:
    return {"kind": "resource", "nodes": list(usage), "edges": []}


def knowledge_graph(artifacts: list[str], dependencies: dict[str, list[str]]) -> dict[str, Any]:
    edges = [(artifact, dep) for artifact, deps in dependencies.items() for dep in deps]
    return {"kind": "knowledge", "nodes": artifacts, "edges": [list(e) for e in edges]}


def decision_graph(decisions: list[str], outcomes: dict[str, str]) -> dict[str, Any]:
    return {
        "kind": "decision",
        "nodes": decisions,
        "edges": [[decision, outcome] for decision, outcome in outcomes.items()],
    }


class ObservabilitySuite:
    """Aggregate all observability primitives into one exportable suite."""

    def __init__(self) -> None:
        self.metrics = MetricsRegistry()
        self.tracer = Tracer()
        self.audit = AuditLog()
        self.timeline = Timeline()

    def export(self) -> dict[str, Any]:
        return {
            "metrics": self.metrics.export(),
            "spans": self.tracer.export(),
            "audit": self.audit.export(),
            "timeline": self.timeline.export(),
        }
