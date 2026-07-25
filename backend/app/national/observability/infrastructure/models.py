from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SAEnum

from app.national.base import BaseEntity, _ulid
from app.national.observability.domain.enums import (
    AlertSeverity,
    AlertStatus,
    HealthStatus,
    MetricType,
    SpanStatus,
)


class NationalMetricPoint(BaseEntity):
    __tablename__ = "national_observability_metrics"

    id = Column(String(26), primary_key=True, default=_ulid)
    name = Column(String(255), nullable=False, index=True)
    type = Column(SAEnum(MetricType), nullable=False, default=MetricType.GAUGE)
    value = Column(Float, nullable=False, default=0.0)
    tags = Column(JSON, nullable=True, default=dict)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    resource_attributes = Column(JSON, nullable=True, default=dict)

    __table_args__ = (
        Index("ix_nat_obs_metric_name_time", "name", "timestamp"),
        Index("ix_nat_obs_metric_time", "timestamp"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.observability.domain.entities import MetricPoint

        return MetricPoint(
            id=self.id,
            name=self.name,
            type=self.type or MetricType.GAUGE,
            value=self.value,
            tags=self.tags or {},
            timestamp=self.timestamp,
            resource_attributes=self.resource_attributes or {},
        )


class NationalTraceSpan(BaseEntity):
    __tablename__ = "national_observability_trace_spans"

    id = Column(String(26), primary_key=True, default=_ulid)
    trace_id = Column(String(26), nullable=False, index=True)
    parent_span_id = Column(String(26), nullable=True)
    name = Column(String(255), nullable=False)
    service = Column(String(100), nullable=True, index=True)
    operation = Column(String(255), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Float, nullable=False, default=0.0)
    status = Column(SAEnum(SpanStatus), nullable=False, default=SpanStatus.UNSET)
    attributes = Column(JSON, nullable=True, default=dict)
    events = Column(JSON, nullable=True, default=list)

    __table_args__ = (
        Index("ix_nat_obs_trace_trace_id", "trace_id"),
        Index("ix_nat_obs_trace_service", "service", "start_time"),
        Index("ix_nat_obs_trace_duration", "duration_ms"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.observability.domain.entities import TraceSpan

        return TraceSpan(
            id=self.id,
            trace_id=self.trace_id,
            parent_span_id=self.parent_span_id or "",
            name=self.name,
            service=self.service or "",
            operation=self.operation or "",
            start_time=self.start_time,
            end_time=self.end_time,
            duration_ms=self.duration_ms,
            status=self.status or SpanStatus.UNSET,
            attributes=self.attributes or {},
            events=self.events or [],
        )


class NationalHealthCheck(BaseEntity):
    __tablename__ = "national_observability_health_checks"

    id = Column(String(26), primary_key=True, default=_ulid)
    name = Column(String(255), nullable=False, unique=True, index=True)
    component = Column(String(255), nullable=True, default="")
    status = Column(SAEnum(HealthStatus), nullable=False, default=HealthStatus.UNKNOWN, index=True)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    last_failure_at = Column(DateTime(timezone=True), nullable=True)
    failure_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    details = Column(JSON, nullable=True, default=dict)
    tags = Column(JSON, nullable=True, default=list)

    __table_args__ = (
        Index("ix_nat_obs_health_status", "status"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.observability.domain.entities import HealthCheck

        return HealthCheck(
            id=self.id,
            name=self.name,
            component=self.component or "",
            status=self.status or HealthStatus.UNKNOWN,
            last_checked_at=self.last_checked_at,
            last_success_at=self.last_success_at,
            last_failure_at=self.last_failure_at,
            failure_count=self.failure_count,
            success_count=self.success_count,
            details=self.details or {},
            tags=self.tags or [],
        )


class NationalAlertRule(BaseEntity):
    __tablename__ = "national_observability_alert_rules"

    id = Column(String(26), primary_key=True, default=_ulid)
    name = Column(String(255), nullable=False)
    metric_name = Column(String(255), nullable=False, index=True)
    condition = Column(String(20), nullable=False, default="gt")
    threshold = Column(Float, nullable=False, default=0.0)
    duration_seconds = Column(Integer, nullable=False, default=60)
    severity = Column(SAEnum(AlertSeverity), nullable=False, default=AlertSeverity.WARNING)
    channels = Column(JSON, nullable=True, default=lambda: ["email"])
    enabled = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("ix_nat_obs_alert_rule_metric", "metric_name", "enabled"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.observability.domain.entities import AlertRule

        return AlertRule(
            id=self.id,
            name=self.name,
            metric_name=self.metric_name,
            condition=self.condition,
            threshold=self.threshold,
            duration_seconds=self.duration_seconds,
            severity=self.severity or AlertSeverity.WARNING,
            channels=self.channels or ["email"],
            enabled=self.enabled if self.enabled is not None else True,
            created_at=self.created_at,
        )


class NationalAlertEvent(BaseEntity):
    __tablename__ = "national_observability_alert_events"

    id = Column(String(26), primary_key=True, default=_ulid)
    rule_id = Column(
        String(26),
        ForeignKey("national_observability_alert_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_value = Column(Float, nullable=False, default=0.0)
    severity = Column(SAEnum(AlertSeverity), nullable=False, default=AlertSeverity.WARNING)
    status = Column(SAEnum(AlertStatus), nullable=False, default=AlertStatus.FIRING, index=True)
    fired_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(100), nullable=True, default="")
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    message = Column(Text, nullable=True, default="")

    __table_args__ = (
        Index("ix_nat_obs_alert_event_rule_status", "rule_id", "status"),
        Index("ix_nat_obs_alert_event_severity_status", "severity", "status"),
        Index("ix_nat_obs_alert_event_fired", "fired_at"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.observability.domain.entities import AlertEvent

        return AlertEvent(
            id=self.id,
            rule_id=self.rule_id,
            metric_value=self.metric_value,
            severity=self.severity or AlertSeverity.WARNING,
            status=self.status or AlertStatus.FIRING,
            fired_at=self.fired_at,
            resolved_at=self.resolved_at,
            acknowledged_by=self.acknowledged_by or "",
            acknowledged_at=self.acknowledged_at,
            message=self.message or "",
        )


class NationalDashboard(BaseEntity):
    __tablename__ = "national_observability_dashboards"

    id = Column(String(26), primary_key=True, default=_ulid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True, default="")
    refresh_interval = Column(Integer, nullable=False, default=60)
    created_by = Column(String(100), nullable=True)

    __table_args__ = {"extend_existing": True}

    def to_domain(self):
        from app.national.observability.domain.entities import Dashboard

        return Dashboard(
            id=self.id,
            name=self.name,
            description=self.description or "",
            refresh_interval=self.refresh_interval,
            created_by=self.created_by or "",
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class NationalDashboardPanel(BaseEntity):
    __tablename__ = "national_observability_dashboard_panels"

    id = Column(String(26), primary_key=True, default=_ulid)
    dashboard_id = Column(
        String(26),
        ForeignKey("national_observability_dashboards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=True, default="")
    metric_names = Column(JSON, nullable=True, default=list)
    chart_type = Column(String(50), nullable=False, default="line")
    width = Column(Integer, nullable=False, default=6)
    height = Column(Integer, nullable=False, default=4)
    position = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("ix_nat_obs_panel_dashboard", "dashboard_id", "position"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.observability.domain.entities import DashboardPanel

        return DashboardPanel(
            id=self.id,
            dashboard_id=self.dashboard_id,
            title=self.title or "",
            metric_names=self.metric_names or [],
            chart_type=self.chart_type,
            width=self.width,
            height=self.height,
            position=self.position,
        )


class NationalServiceGraph(BaseEntity):
    __tablename__ = "national_observability_service_graphs"

    id = Column(String(26), primary_key=True, default=_ulid)
    service_name = Column(String(255), nullable=False, unique=True, index=True)
    dependencies = Column(JSON, nullable=True, default=list)
    metrics = Column(JSON, nullable=True, default=dict)
    health = Column(SAEnum(HealthStatus), nullable=False, default=HealthStatus.UNKNOWN)

    __table_args__ = {"extend_existing": True}

    def to_domain(self):
        from app.national.observability.domain.entities import ServiceDependency, ServiceGraph

        deps = []
        for d in self.dependencies or []:
            deps.append(
                ServiceDependency(
                    source=d.get("source", ""),
                    target=d.get("target", ""),
                    type=d.get("type", "http"),
                    latency_p50=d.get("latency_p50", 0.0),
                    latency_p99=d.get("latency_p99", 0.0),
                    error_rate=d.get("error_rate", 0.0),
                ),
            )
        return ServiceGraph(
            id=self.id,
            service_name=self.service_name,
            dependencies=deps,
            metrics=self.metrics or {},
            health=self.health or HealthStatus.UNKNOWN,
        )
