from __future__ import annotations

from app.national.exceptions import NationalDomainError


class ObservabilityError(NationalDomainError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Observability error: {reason}")


class MetricQueryError(NationalDomainError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Metric query failed: {reason}")


class HealthCheckNotFoundError(NationalDomainError):
    def __init__(self, check_id: str) -> None:
        self.check_id = check_id
        super().__init__(f"Health check not found: {check_id}")


class AlertRuleNotFoundError(NationalDomainError):
    def __init__(self, rule_id: str) -> None:
        self.rule_id = rule_id
        super().__init__(f"Alert rule not found: {rule_id}")


class AlertEventNotFoundError(NationalDomainError):
    def __init__(self, event_id: str) -> None:
        self.event_id = event_id
        super().__init__(f"Alert event not found: {event_id}")


class DashboardNotFoundError(NationalDomainError):
    def __init__(self, dashboard_id: str) -> None:
        self.dashboard_id = dashboard_id
        super().__init__(f"Dashboard not found: {dashboard_id}")


class TraceSpanNotFoundError(NationalDomainError):
    def __init__(self, span_id: str) -> None:
        self.span_id = span_id
        super().__init__(f"Trace span not found: {span_id}")
