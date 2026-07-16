from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC


@dataclass
class InfrastructureTwin:
    nodes: int = 0
    containers: int = 0
    edge_devices: int = 0
    services: list[dict[str, Any]] = field(default_factory=list)
    resources: dict[str, Any] = field(default_factory=dict)
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class ServiceTwin:
    name: str = ""
    version: str = ""
    status: str = "unknown"
    dependencies: list[str] = field(default_factory=list)
    instances: int = 0
    latency_ms: float = 0.0
    health: str = "unknown"
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class ApplicationTwin:
    name: str = ""
    version: str = ""
    components: list[dict[str, Any]] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    status: str = "unknown"
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class HospitalTwin:
    hospital_id: str = ""
    name: str = ""
    departments: list[dict[str, Any]] = field(default_factory=list)
    equipment: list[dict[str, Any]] = field(default_factory=list)
    status: str = "unknown"
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class LaboratoryTwin:
    lab_id: str = ""
    name: str = ""
    instruments: list[dict[str, Any]] = field(default_factory=list)
    tests_processed: int = 0
    status: str = "unknown"
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class SecurityStateTwin:
    active_threats: int = 0
    incidents: int = 0
    vulnerabilities: int = 0
    compliance_score: float = 0.0
    last_scan: str | None = None
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class OperationsStateTwin:
    health_grade: str = "GREEN"
    active_alerts: int = 0
    degraded_components: int = 0
    queue_backlog: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage: float = 0.0
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
