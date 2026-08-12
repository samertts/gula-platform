from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from backend.app.integration.connectors import ConnectorRegistry

logger = logging.getLogger("gula.integration.monitoring")


@dataclass
class DashboardEntry:
    name: str = ""
    status: str = "unknown"
    latency_ms: float = 0.0
    error_count: int = 0
    request_count: int = 0
    last_checked: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


class APIDashboard:
    def __init__(self) -> None:
        self._entries: dict[str, DashboardEntry] = {}

    def record(self, name: str, latency_ms: float, success: bool) -> None:
        entry = self._entries.setdefault(name, DashboardEntry(name=name))
        entry.request_count += 1
        entry.latency_ms = latency_ms
        entry.last_checked = time.time()
        if not success:
            entry.error_count += 1
        entry.status = "degraded" if entry.error_count > entry.request_count * 0.1 else "healthy"

    def get_all(self) -> list[DashboardEntry]:
        return list(self._entries.values())

    def summary(self) -> dict[str, Any]:
        entries = self.get_all()
        total = len(entries)
        healthy = sum(1 for e in entries if e.status == "healthy")
        degraded = sum(1 for e in entries if e.status == "degraded")
        return {
            "total_endpoints": total,
            "healthy": healthy,
            "degraded": degraded,
            "entries": [self._entry_to_dict(e) for e in entries],
        }

    @staticmethod
    def _entry_to_dict(e: DashboardEntry) -> dict[str, Any]:
        return {
            "name": e.name,
            "status": e.status,
            "latency_ms": e.latency_ms,
            "error_count": e.error_count,
            "request_count": e.request_count,
            "last_checked": e.last_checked,
            "details": e.details,
        }


class ConnectorDashboard:
    def __init__(self) -> None:
        self._connectors: dict[str, dict[str, Any]] = {}

    def refresh(self) -> dict[str, Any]:
        statuses = ConnectorRegistry.get_status_all()
        for s in statuses:
            cid = s.get("name", s.get("connector_class", "unknown"))
            self._connectors[cid] = s
        return self.summary()

    def summary(self) -> dict[str, Any]:
        return {
            "total": len(self._connectors),
            "connectors": self._connectors,
        }


class FHIRDashboard:
    def __init__(self) -> None:
        self._operations: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def record_operation(self, resource_type: str, operation: str, latency_ms: float, success: bool) -> None:
        self._operations[resource_type].append({
            "operation": operation,
            "latency_ms": latency_ms,
            "success": success,
            "timestamp": time.time(),
        })

    def summary(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for resource_type, ops in self._operations.items():
            total = len(ops)
            successes = sum(1 for o in ops if o["success"])
            avg_latency = sum(o["latency_ms"] for o in ops) / total if total else 0
            result[resource_type] = {
                "total_operations": total,
                "success_rate": round(successes / total * 100, 2) if total else 0.0,
                "avg_latency_ms": round(avg_latency, 2),
                "last_operation": ops[-1] if ops else None,
            }
        return result


class ErrorDashboard:
    def __init__(self, max_entries: int = 1000) -> None:
        self._errors: list[dict[str, Any]] = []
        self._max_entries = max_entries

    def record_error(self, source: str, error: str, severity: str = "error") -> None:
        entry = {
            "source": source,
            "error": error,
            "severity": severity,
            "timestamp": time.time(),
        }
        self._errors.append(entry)
        if len(self._errors) > self._max_entries:
            self._errors.pop(0)

    def summary(self) -> dict[str, Any]:
        total = len(self._errors)
        by_severity: dict[str, int] = defaultdict(int)
        by_source: dict[str, int] = defaultdict(int)
        for e in self._errors:
            by_severity[e["severity"]] += 1
            by_source[e["source"]] += 1
        return {
            "total_errors": total,
            "by_severity": dict(by_severity),
            "by_source": dict(by_source),
            "recent": self._errors[-10:] if self._errors else [],
        }

    def get_recent(self, count: int = 10) -> list[dict[str, Any]]:
        return self._errors[-count:] if self._errors else []


class LatencyDashboard:
    def __init__(self) -> None:
        self._latencies: dict[str, list[float]] = defaultdict(list)
        self._max_samples = 1000

    def record(self, component: str, latency_ms: float) -> None:
        samples = self._latencies[component]
        samples.append(latency_ms)
        if len(samples) > self._max_samples:
            self._latencies[component] = samples[-self._max_samples:]

    def summary(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for component, samples in self._latencies.items():
            if not samples:
                continue
            result[component] = {
                "avg_ms": round(sum(samples) / len(samples), 2),
                "min_ms": round(min(samples), 2),
                "max_ms": round(max(samples), 2),
                "p50_ms": round(sorted(samples)[len(samples) // 2], 2),
                "p95_ms": round(sorted(samples)[int(len(samples) * 0.95)], 2),
                "p99_ms": round(sorted(samples)[int(len(samples) * 0.99)], 2),
                "sample_count": len(samples),
            }
        return result


class IntegrationMonitor:
    def __init__(self) -> None:
        self.api = APIDashboard()
        self.connectors = ConnectorDashboard()
        self.fhir = FHIRDashboard()
        self.errors = ErrorDashboard()
        self.latency = LatencyDashboard()

    def get_health_dashboard(self) -> dict[str, Any]:
        return {
            "api": self.api.summary(),
            "connectors": self.connectors.summary(),
            "fhir": self.fhir.summary(),
            "errors": self.errors.summary(),
            "latency": self.latency.summary(),
            "timestamp": time.time(),
        }

    def get_api_dashboard(self) -> dict[str, Any]:
        return self.api.summary()

    def get_connector_dashboard(self) -> dict[str, Any]:
        return self.connectors.refresh()

    def get_fhir_dashboard(self) -> dict[str, Any]:
        return self.fhir.summary()

    def get_error_dashboard(self) -> dict[str, Any]:
        return self.errors.summary()

    def get_latency_dashboard(self) -> dict[str, Any]:
        return self.latency.summary()

    def record_api_call(self, name: str, latency_ms: float, success: bool) -> None:
        self.api.record(name, latency_ms, success)
        self.latency.record(f"api_{name}", latency_ms)

    def record_connector_health(self, name: str, latency_ms: float, success: bool) -> None:
        self.latency.record(f"connector_{name}", latency_ms)

    def record_fhir_operation(self, resource_type: str, operation: str, latency_ms: float, success: bool) -> None:
        self.fhir.record_operation(resource_type, operation, latency_ms, success)
        self.latency.record(f"fhir_{resource_type}_{operation}", latency_ms)

    def record_error(self, source: str, error: str, severity: str = "error") -> None:
        self.errors.record_error(source, error, severity)
