from __future__ import annotations

from dataclasses import dataclass

from app.national.events.base import NationalDomainEvent


@dataclass
class MetricRecorded(NationalDomainEvent):
    event_type: str = "national.observability.metric.recorded"
    aggregate_type: str = "MetricPoint"
    metric_name: str = ""
    metric_value: float = 0.0
    metric_type: str = ""


@dataclass
class SpanCompleted(NationalDomainEvent):
    event_type: str = "national.observability.span.completed"
    aggregate_type: str = "TraceSpan"
    trace_id: str = ""
    span_id: str = ""
    duration_ms: float = 0.0


@dataclass
class AlertFired(NationalDomainEvent):
    event_type: str = "national.observability.alert.fired"
    aggregate_type: str = "AlertEvent"
    alert_event_id: str = ""
    rule_id: str = ""
    metric_value: float = 0.0
    severity: str = ""


@dataclass
class AlertResolved(NationalDomainEvent):
    event_type: str = "national.observability.alert.resolved"
    aggregate_type: str = "AlertEvent"
    alert_event_id: str = ""
    rule_id: str = ""


@dataclass
class HealthStatusChanged(NationalDomainEvent):
    event_type: str = "national.observability.health_status.changed"
    aggregate_type: str = "HealthCheck"
    check_name: str = ""
    previous_status: str = ""
    new_status: str = ""
