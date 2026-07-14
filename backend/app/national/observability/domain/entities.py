from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.national.observability.domain.enums import (
    AlertSeverity,
    AlertStatus,
    HealthStatus,
    MetricType,
    SpanStatus,
)


@dataclass
class MetricPoint:
    id: str
    name: str
    type: MetricType = MetricType.GAUGE
    value: float = 0.0
    tags: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    resource_attributes: dict[str, str] = field(default_factory=dict)


@dataclass
class TraceSpan:
    id: str
    trace_id: str
    parent_span_id: str = ""
    name: str = ""
    service: str = ""
    operation: str = ""
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_ms: float = 0.0
    status: SpanStatus = SpanStatus.UNSET
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class HealthCheck:
    id: str
    name: str
    component: str = ""
    status: HealthStatus = HealthStatus.UNKNOWN
    last_checked_at: datetime | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    failure_count: int = 0
    success_count: int = 0
    details: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


@dataclass
class AlertRule:
    id: str
    name: str
    metric_name: str = ""
    condition: str = "gt"
    threshold: float = 0.0
    duration_seconds: int = 60
    severity: AlertSeverity = AlertSeverity.WARNING
    channels: list[str] = field(default_factory=lambda: ["email"])
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AlertEvent:
    id: str
    rule_id: str
    metric_value: float = 0.0
    severity: AlertSeverity = AlertSeverity.WARNING
    status: AlertStatus = AlertStatus.FIRING
    fired_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None
    acknowledged_by: str = ""
    acknowledged_at: datetime | None = None
    message: str = ""


@dataclass
class Dashboard:
    id: str
    name: str
    description: str = ""
    panels: list[DashboardPanel] = field(default_factory=list)
    refresh_interval: int = 60
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DashboardPanel:
    id: str
    dashboard_id: str
    title: str = ""
    metric_names: list[str] = field(default_factory=list)
    chart_type: str = "line"
    width: int = 6
    height: int = 4
    position: int = 0


@dataclass
class ServiceGraph:
    id: str
    service_name: str
    dependencies: list[ServiceDependency] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    health: HealthStatus = HealthStatus.UNKNOWN


@dataclass
class ServiceDependency:
    source: str
    target: str
    type: str = "http"
    latency_p50: float = 0.0
    latency_p99: float = 0.0
    error_rate: float = 0.0


@dataclass
class PlatformOverview:
    overall_health: HealthStatus = HealthStatus.UNKNOWN
    total_services: int = 0
    healthy_services: int = 0
    degraded_services: int = 0
    unhealthy_services: int = 0
    active_alerts: int = 0
    critical_alerts: int = 0
    metrics_count: int = 0
    traces_count: int = 0
    checks: list[dict[str, Any]] = field(default_factory=list)
    recent_alerts: list[dict[str, Any]] = field(default_factory=list)
