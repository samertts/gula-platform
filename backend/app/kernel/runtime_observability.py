from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.kernel import Kernel

logger = logging.getLogger("gula.kernel.runtime_observability")


@dataclass
class Span:
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = ""
    parent_span_id: str = ""
    name: str = ""
    service: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    duration_ms: float = 0.0
    status: str = "unknown"
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def finish(self, status: str = "ok") -> None:
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.events.append({"name": name, "timestamp": time.time(), "attributes": attributes or {}})


@dataclass
class ServiceNode:
    name: str = ""
    type: str = "service"
    version: str = ""
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    status: str = "unknown"
    latency_p99_ms: float = 0.0
    last_seen: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "version": self.version,
            "dependencies": self.dependencies,
            "dependents": self.dependents,
            "status": self.status,
            "latency_p99_ms": self.latency_p99_ms,
            "last_seen": self.last_seen,
        }


@dataclass
class SlowQueryRecord:
    query: str = ""
    database: str = ""
    duration_ms: float = 0.0
    executed_at: float = field(default_factory=time.time)
    caller: str = ""
    tenant_id: str = ""
    rows_affected: int = 0
    plan: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query[:500],
            "database": self.database,
            "duration_ms": round(self.duration_ms, 1),
            "executed_at": datetime.utcfromtimestamp(self.executed_at).isoformat(),
            "caller": self.caller,
            "rows_affected": self.rows_affected,
        }


class TopologyCollector:
    def __init__(self):
        self._nodes: dict[str, ServiceNode] = {}
        self._max_history: int = 1000

    def register_node(self, node: ServiceNode) -> None:
        self._nodes[node.name] = node
        logger.debug("Topology node registered", extra={"name": node.name, "type": node.type})

    def register_dependency(self, source: str, target: str) -> None:
        if source in self._nodes and target not in self._nodes[source].dependencies:
            self._nodes[source].dependencies.append(target)
        if target in self._nodes and source not in self._nodes[target].dependents:
            self._nodes[target].dependents.append(source)

    def update_status(self, name: str, status: str, latency_ms: float = 0.0) -> None:
        node = self._nodes.get(name)
        if node:
            node.status = status
            node.last_seen = time.time()
            if latency_ms > 0:
                node.latency_p99_ms = max(node.latency_p99_ms, latency_ms)

    def remove_node(self, name: str) -> bool:
        if name in self._nodes:
            del self._nodes[name]
            for node in self._nodes.values():
                node.dependencies = [d for d in node.dependencies if d != name]
                node.dependents = [d for d in node.dependents if d != name]
            return True
        return False

    def get_graph(self) -> dict[str, Any]:
        return {
            "nodes": {name: node.to_dict() for name, node in self._nodes.items()},
            "edges": [
                {"source": source, "target": dep}
                for source, node in self._nodes.items()
                for dep in node.dependencies
            ],
            "node_count": len(self._nodes),
            "edge_count": sum(len(n.dependencies) for n in self._nodes.values()),
        }

    def get_impact_analysis(self, node_name: str) -> dict[str, Any]:
        affected: set[str] = set()
        queue = [node_name]
        visited: set[str] = set()
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            node = self._nodes.get(current)
            if node:
                for dep in node.dependents:
                    if dep not in visited:
                        affected.add(dep)
                        queue.append(dep)
        return {
            "target": node_name,
            "direct_affected": self._nodes.get(node_name, ServiceNode()).dependents,
            "transitive_affected": list(affected),
            "total_affected": len(affected),
        }


class SlowQueryDetector:
    def __init__(self, threshold_ms: float = 500.0):
        self._threshold_ms = threshold_ms
        self._records: deque[SlowQueryRecord] = deque(maxlen=500)
        self._alert_count: int = 0

    @property
    def threshold(self) -> float:
        return self._threshold_ms

    def set_threshold(self, threshold_ms: float) -> None:
        self._threshold_ms = threshold_ms
        logger.info("Slow query threshold updated", extra={"threshold_ms": threshold_ms})

    def record(
        self,
        query: str,
        duration_ms: float,
        database: str = "postgresql",
        caller: str = "",
        tenant_id: str = "",
        rows_affected: int = 0,
        plan: str = "",
    ) -> bool:
        if duration_ms >= self._threshold_ms:
            record = SlowQueryRecord(
                query=query,
                database=database,
                duration_ms=duration_ms,
                caller=caller,
                tenant_id=tenant_id,
                rows_affected=rows_affected,
                plan=plan,
            )
            self._records.append(record)
            self._alert_count += 1
            logger.warning(
                "Slow query detected",
                extra={
                    "duration_ms": round(duration_ms, 1),
                    "threshold": self._threshold_ms,
                    "caller": caller,
                },
            )
            return True
        return False

    def get_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        return [r.to_dict() for r in list(self._records)[-limit:]]

    def get_stats(self) -> dict[str, Any]:
        if not self._records:
            return {
                "count": 0,
                "avg_duration_ms": 0,
                "max_duration_ms": 0,
                "alerts": self._alert_count,
            }
        durations = [r.duration_ms for r in self._records]
        return {
            "count": len(self._records),
            "avg_duration_ms": round(sum(durations) / len(durations), 1),
            "max_duration_ms": round(max(durations), 1),
            "alerts": self._alert_count,
        }


class RuntimeObserver:
    def __init__(self, kernel: Kernel | None = None):
        self._kernel = kernel
        self._traces: deque[Span] = deque(maxlen=500)
        self._active_spans: dict[str, Span] = {}
        self._metrics_store: dict[str, list[float]] = defaultdict(lambda: deque(maxlen=1000))
        self._topology = TopologyCollector()
        self._slow_queries = SlowQueryDetector()
        self._log_buffer: deque[dict[str, Any]] = deque(maxlen=2000)
        self._started_at: float = time.time()

    @property
    def topology(self) -> TopologyCollector:
        return self._topology

    @property
    def slow_queries(self) -> SlowQueryDetector:
        return self._slow_queries

    def start_trace(
        self, name: str, service: str = "kernel", trace_id: str = "", parent_span_id: str = "",
    ) -> Span:
        span = Span(
            name=name,
            service=service,
            trace_id=trace_id or str(uuid.uuid4()),
            parent_span_id=parent_span_id,
        )
        self._active_spans[span.span_id] = span
        return span

    def end_trace(self, span_id: str, status: str = "ok") -> Span | None:
        span = self._active_spans.pop(span_id, None)
        if span:
            span.finish(status)
            self._traces.append(span)
        return span

    def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        self._metrics_store[name].append(value)

    def record_log(self, level: str, message: str, extra: dict[str, Any] | None = None) -> None:
        self._log_buffer.append(
            {
                "timestamp": time.time(),
                "level": level,
                "message": message,
                "extra": extra or {},
            },
        )

    def get_metrics_snapshot(self) -> dict[str, Any]:
        snapshot = {}
        for name, values in self._metrics_store.items():
            if values:
                snapshot[name] = {
                    "count": len(values),
                    "min": round(min(values), 2),
                    "max": round(max(values), 2),
                    "avg": round(sum(values) / len(values), 2),
                    "latest": round(values[-1], 2),
                }
        return snapshot

    def get_topology_snapshot(self) -> dict[str, Any]:
        return self._topology.get_graph()

    def get_slow_queries_snapshot(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._slow_queries.get_recent(limit)

    def get_full_snapshot(self) -> dict[str, Any]:
        return {
            "uptime_seconds": round(time.time() - self._started_at, 1),
            "metrics": self.get_metrics_snapshot(),
            "topology": self.get_topology_snapshot(),
            "slow_queries": self.get_slow_queries_snapshot(limit=20),
            "active_traces": len(self._active_spans),
            "traces_buffer": len(self._traces),
            "log_buffer": len(self._log_buffer),
        }
