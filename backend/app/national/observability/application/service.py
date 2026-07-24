from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from app._compat import UTC
from app.kernel.event_bus.bus import EventBus
from app.kernel.event_bus.events import Event
from app.national.observability.domain.entities import (
    AlertEvent,
    AlertRule,
    Dashboard,
    DashboardPanel,
    HealthCheck,
    MetricPoint,
    PlatformOverview,
    ServiceDependency,
    ServiceGraph,
    TraceSpan,
)
from app.national.observability.domain.enums import (
    AlertSeverity,
    AlertStatus,
    HealthStatus,
    MetricType,
    SpanStatus,
)
from app.national.observability.domain.events import (
    AlertFired,
    AlertResolved,
    HealthStatusChanged,
    MetricRecorded,
    SpanCompleted,
)
from app.national.observability.domain.repository import (
    AlertEventRepository,
    AlertRuleRepository,
    DashboardPanelRepository,
    DashboardRepository,
    HealthCheckRepository,
    MetricRepository,
    ServiceGraphRepository,
    TraceSpanRepository,
)
from app.national.observability.exceptions import (
    AlertEventNotFoundError,
    AlertRuleNotFoundError,
    DashboardNotFoundError,
    MetricQueryError,
)

logger = logging.getLogger("gula.national.observability")


class ObservabilityService:

    def __init__(
        self,
        metric_repository: MetricRepository,
        trace_span_repository: TraceSpanRepository,
        health_check_repository: HealthCheckRepository,
        alert_rule_repository: AlertRuleRepository,
        alert_event_repository: AlertEventRepository,
        dashboard_repository: DashboardRepository,
        dashboard_panel_repository: DashboardPanelRepository,
        service_graph_repository: ServiceGraphRepository,
        event_bus: EventBus,
    ) -> None:
        self.metric_repository = metric_repository
        self.trace_span_repository = trace_span_repository
        self.health_check_repository = health_check_repository
        self.alert_rule_repository = alert_rule_repository
        self.alert_event_repository = alert_event_repository
        self.dashboard_repository = dashboard_repository
        self.dashboard_panel_repository = dashboard_panel_repository
        self.service_graph_repository = service_graph_repository
        self.event_bus = event_bus

    async def record_metric(
        self,
        name: str,
        value: float,
        type: str = "gauge",
        tags: dict[str, str] | None = None,
        timestamp: str | None = None,
        resource_attributes: dict[str, str] | None = None,
    ) -> MetricPoint:
        metric = MetricPoint(
            id=str(uuid.uuid4()),
            name=name,
            type=MetricType(type),
            value=value,
            tags=tags or {},
            timestamp=datetime.fromisoformat(timestamp) if timestamp else datetime.now(UTC),
            resource_attributes=resource_attributes or {},
        )
        saved = await self.metric_repository.save(metric)

        self._publish_event(MetricRecorded(
            metric_name=name,
            metric_value=value,
            metric_type=type,
            aggregate_id=name,
            payload={"name": name, "value": value, "type": type},
        ))

        return saved

    async def record_metrics_batch(
        self,
        metrics: list[dict[str, Any]],
    ) -> list[MetricPoint]:
        points = []
        for m in metrics:
            points.append(MetricPoint(
                id=str(uuid.uuid4()),
                name=m.get("name", ""),
                type=MetricType(m.get("type", "gauge")),
                value=m.get("value", 0.0),
                tags=m.get("tags", {}),
                timestamp=datetime.fromisoformat(m["timestamp"]) if m.get("timestamp") else datetime.now(UTC),
                resource_attributes=m.get("resource_attributes", {}),
            ))
        return await self.metric_repository.save_many(points)

    async def query_metrics(
        self,
        name: str | None = None,
        tags: dict[str, str] | None = None,
        from_time: str | None = None,
        to_time: str | None = None,
        aggregate: str = "avg",
        group_by: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        try:
            parsed_from = datetime.fromisoformat(from_time) if from_time else None
            parsed_to = datetime.fromisoformat(to_time) if to_time else None
            return await self.metric_repository.query(
                name=name,
                tags=tags,
                from_time=parsed_from,
                to_time=parsed_to,
                aggregate=aggregate,
                group_by=group_by,
                limit=limit,
            )
        except Exception as exc:
            raise MetricQueryError(str(exc)) from exc

    async def start_span(
        self,
        trace_id: str,
        name: str,
        service: str = "",
        operation: str = "",
        parent_span_id: str = "",
        attributes: dict[str, Any] | None = None,
    ) -> TraceSpan:
        return TraceSpan(
            id=str(uuid.uuid4()),
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            name=name,
            service=service,
            operation=operation,
            start_time=datetime.now(UTC),
            status=SpanStatus.OK,
            attributes=attributes or {},
        )

    async def end_span(
        self,
        span: TraceSpan,
        status: str = "ok",
        attributes: dict[str, Any] | None = None,
    ) -> TraceSpan:
        span.end_time = datetime.now(UTC)
        span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000 if span.start_time else 0
        span.status = SpanStatus(status)
        if attributes:
            span.attributes.update(attributes)

        saved = await self.trace_span_repository.save(span)

        self._publish_event(SpanCompleted(
            trace_id=span.trace_id,
            span_id=span.id,
            duration_ms=span.duration_ms,
            aggregate_id=span.trace_id,
            payload={"span_id": span.id, "duration_ms": span.duration_ms},
        ))

        return saved

    async def query_traces(
        self,
        trace_id: str | None = None,
        service: str | None = None,
        operation: str | None = None,
        min_duration: float | None = None,
        max_duration: float | None = None,
        from_time: str | None = None,
        to_time: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[TraceSpan]:
        parsed_from = datetime.fromisoformat(from_time) if from_time else None
        parsed_to = datetime.fromisoformat(to_time) if to_time else None

        if trace_id:
            return await self.trace_span_repository.find_by_trace(trace_id)
        return await self.trace_span_repository.search(
            service=service,
            operation=operation,
            min_duration=min_duration,
            max_duration=max_duration,
            from_time=parsed_from,
            to_time=parsed_to,
            status=status,
            skip=skip,
            limit=limit,
        )

    async def register_health_check(
        self,
        name: str,
        component: str = "",
        tags: list[str] | None = None,
    ) -> HealthCheck:
        existing = await self.health_check_repository.find_by_name(name)
        if existing:
            return existing
        check = HealthCheck(
            id=str(uuid.uuid4()),
            name=name,
            component=component,
            status=HealthStatus.UNKNOWN,
            tags=tags or [],
        )
        return await self.health_check_repository.save(check)

    async def run_health_check(
        self,
        name: str,
        is_healthy: bool,
        details: dict[str, Any] | None = None,
    ) -> HealthCheck:
        check = await self.health_check_repository.find_by_name(name)
        if not check:
            check = HealthCheck(
                id=str(uuid.uuid4()),
                name=name,
                component="",
                status=HealthStatus.UNKNOWN,
                tags=[],
            )

        previous_status = check.status
        check.last_checked_at = datetime.now(UTC)

        if is_healthy:
            check.status = HealthStatus.HEALTHY
            check.last_success_at = datetime.now(UTC)
            check.success_count += 1
        else:
            check.status = HealthStatus.UNHEALTHY
            check.last_failure_at = datetime.now(UTC)
            check.failure_count += 1

        check.details = details or {}
        saved = await self.health_check_repository.save(check)

        if previous_status != saved.status:
            self._publish_event(HealthStatusChanged(
                check_name=name,
                previous_status=previous_status.value,
                new_status=saved.status.value,
                aggregate_id=name,
                payload={"check": name, "previous": previous_status.value, "new": saved.status.value},
            ))

        return saved

    async def get_health_status(self) -> dict[str, Any]:
        return await self.health_check_repository.get_overall_status()

    async def get_all_health_checks(self) -> list[HealthCheck]:
        return await self.health_check_repository.list()

    async def create_alert_rule(
        self,
        name: str,
        metric_name: str,
        condition: str = "gt",
        threshold: float = 0.0,
        duration_seconds: int = 60,
        severity: str = "warning",
        channels: list[str] | None = None,
    ) -> AlertRule:
        rule = AlertRule(
            id=str(uuid.uuid4()),
            name=name,
            metric_name=metric_name,
            condition=condition,
            threshold=threshold,
            duration_seconds=duration_seconds,
            severity=AlertSeverity(severity),
            channels=channels or ["email"],
        )
        return await self.alert_rule_repository.save(rule)

    async def get_alert_rule(self, rule_id: str) -> AlertRule:
        rule = await self.alert_rule_repository.get(rule_id)
        if not rule:
            raise AlertRuleNotFoundError(rule_id)
        return rule

    async def list_alert_rules(self, skip: int = 0, limit: int = 100) -> list[AlertRule]:
        return await self.alert_rule_repository.list(skip=skip, limit=limit)

    async def update_alert_rule(self, rule_id: str, updates: dict[str, Any]) -> AlertRule:
        rule = await self.alert_rule_repository.get(rule_id)
        if not rule:
            raise AlertRuleNotFoundError(rule_id)
        for key, value in updates.items():
            if hasattr(rule, key) and key not in ("id", "created_at"):
                if key == "severity" and isinstance(value, str):
                    value = AlertSeverity(value)
                setattr(rule, key, value)
        return await self.alert_rule_repository.save(rule)

    async def delete_alert_rule(self, rule_id: str) -> None:
        rule = await self.alert_rule_repository.get(rule_id)
        if not rule:
            raise AlertRuleNotFoundError(rule_id)
        await self.alert_rule_repository.delete(rule_id)

    async def evaluate_alert(self, rule_id: str) -> AlertEvent | None:
        rule = await self.alert_rule_repository.get(rule_id)
        if not rule or not rule.enabled:
            return None

        recent = await self.metric_repository.query(
            name=rule.metric_name,
            from_time=datetime.now(UTC) - timedelta(seconds=rule.duration_seconds),
            to_time=datetime.now(UTC),
            aggregate="avg",
            limit=1,
        )

        if not recent:
            firing_events = await self.alert_event_repository.list(
                rule_id=rule_id,
                status=AlertStatus.FIRING,
            )
            for fe in firing_events:
                fe.status = AlertStatus.RESOLVED
                fe.resolved_at = datetime.now(UTC)
                await self.alert_event_repository.save(fe)
                self._publish_event(AlertResolved(
                    alert_event_id=fe.id,
                    rule_id=rule_id,
                    aggregate_id=rule_id,
                    payload={"rule_name": rule.name},
                ))
            return None

        current_value = recent[0].get("value", 0.0)
        triggered = False

        if (rule.condition == "gt" and current_value > rule.threshold) or (rule.condition == "gte" and current_value >= rule.threshold) or (rule.condition == "lt" and current_value < rule.threshold) or (rule.condition == "lte" and current_value <= rule.threshold) or (rule.condition == "eq" and current_value == rule.threshold):
            triggered = True

        if triggered:
            firing = await self.alert_event_repository.find_firing()
            already_firing = any(e.rule_id == rule_id for e in firing)
            if not already_firing:
                event = AlertEvent(
                    id=str(uuid.uuid4()),
                    rule_id=rule_id,
                    metric_value=current_value,
                    severity=rule.severity,
                    message=f"Alert {rule.name}: {rule.metric_name} is {current_value} (threshold: {rule.threshold})",
                )
                saved = await self.alert_event_repository.save(event)
                self._publish_event(AlertFired(
                    alert_event_id=saved.id,
                    rule_id=rule_id,
                    metric_value=current_value,
                    severity=rule.severity.value,
                    aggregate_id=rule_id,
                    payload={"rule_name": rule.name, "value": current_value, "threshold": rule.threshold},
                ))
                return saved
        else:
            firing_events = await self.alert_event_repository.list(
                rule_id=rule_id,
                status=AlertStatus.FIRING,
            )
            for fe in firing_events:
                fe.status = AlertStatus.RESOLVED
                fe.resolved_at = datetime.now(UTC)
                await self.alert_event_repository.save(fe)
                self._publish_event(AlertResolved(
                    alert_event_id=fe.id,
                    rule_id=rule_id,
                    aggregate_id=rule_id,
                    payload={"rule_name": rule.name},
                ))

        return None

    async def list_alert_events(
        self,
        status: str | None = None,
        severity: str | None = None,
        rule_id: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AlertEvent]:
        return await self.alert_event_repository.list(
            status=AlertStatus(status) if status else None,
            severity=AlertSeverity(severity) if severity else None,
            rule_id=rule_id,
            skip=skip,
            limit=limit,
        )

    async def acknowledge_alert(self, event_id: str, acknowledged_by: str = "") -> AlertEvent:
        event = await self.alert_event_repository.get(event_id)
        if not event:
            raise AlertEventNotFoundError(event_id)
        event.status = AlertStatus.ACKNOWLEDGED
        event.acknowledged_by = acknowledged_by
        event.acknowledged_at = datetime.now(UTC)
        return await self.alert_event_repository.save(event)

    async def silence_alert(self, event_id: str) -> AlertEvent:
        event = await self.alert_event_repository.get(event_id)
        if not event:
            raise AlertEventNotFoundError(event_id)
        event.status = AlertStatus.SILENCED
        return await self.alert_event_repository.save(event)

    async def create_dashboard(
        self,
        name: str,
        description: str = "",
        panels: list[dict[str, Any]] | None = None,
        refresh_interval: int = 60,
        created_by: str = "",
    ) -> Dashboard:
        dashboard = Dashboard(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            refresh_interval=refresh_interval,
            created_by=created_by,
        )
        saved = await self.dashboard_repository.save(dashboard)

        if panels:
            for i, p in enumerate(panels):
                panel = DashboardPanel(
                    id=str(uuid.uuid4()),
                    dashboard_id=saved.id,
                    title=p.get("title", ""),
                    metric_names=p.get("metric_names", []),
                    chart_type=p.get("chart_type", "line"),
                    width=p.get("width", 6),
                    height=p.get("height", 4),
                    position=p.get("position", i),
                )
                await self.dashboard_panel_repository.save(panel)

        return await self.get_dashboard(saved.id)

    async def get_dashboard(self, dashboard_id: str) -> Dashboard:
        dashboard = await self.dashboard_repository.get(dashboard_id)
        if not dashboard:
            raise DashboardNotFoundError(dashboard_id)
        dashboard.panels = await self.dashboard_panel_repository.find_by_dashboard(dashboard_id)
        return dashboard

    async def list_dashboards(self, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        dashboards = await self.dashboard_repository.list(skip=skip, limit=limit)
        result = []
        for d in dashboards:
            panels = await self.dashboard_panel_repository.find_by_dashboard(d.id)
            d.panels = panels
            result.append(d)
        return result

    async def update_dashboard(
        self,
        dashboard_id: str,
        updates: dict[str, Any],
        panels: list[dict[str, Any]] | None = None,
    ) -> Dashboard:
        dashboard = await self.dashboard_repository.get(dashboard_id)
        if not dashboard:
            raise DashboardNotFoundError(dashboard_id)

        for key, value in updates.items():
            if hasattr(dashboard, key) and key not in ("id", "created_at"):
                setattr(dashboard, key, value)

        dashboard.updated_at = datetime.now(UTC)
        await self.dashboard_repository.save(dashboard)

        if panels is not None:
            await self.dashboard_panel_repository.delete_by_dashboard(dashboard_id)
            for i, p in enumerate(panels):
                panel = DashboardPanel(
                    id=str(uuid.uuid4()),
                    dashboard_id=dashboard_id,
                    title=p.get("title", ""),
                    metric_names=p.get("metric_names", []),
                    chart_type=p.get("chart_type", "line"),
                    width=p.get("width", 6),
                    height=p.get("height", 4),
                    position=p.get("position", i),
                )
                await self.dashboard_panel_repository.save(panel)

        return await self.get_dashboard(dashboard_id)

    async def delete_dashboard(self, dashboard_id: str) -> None:
        dashboard = await self.dashboard_repository.get(dashboard_id)
        if not dashboard:
            raise DashboardNotFoundError(dashboard_id)
        await self.dashboard_panel_repository.delete_by_dashboard(dashboard_id)
        await self.dashboard_repository.delete(dashboard_id)

    async def record_service_graph(
        self,
        service_name: str,
        dependencies: list[dict[str, Any]],
        metrics: dict[str, float] | None = None,
        health: str = "unknown",
    ) -> ServiceGraph:
        parsed_deps = [
            ServiceDependency(
                source=d.get("source", service_name),
                target=d.get("target", ""),
                type=d.get("type", "http"),
                latency_p50=d.get("latency_p50", 0.0),
                latency_p99=d.get("latency_p99", 0.0),
                error_rate=d.get("error_rate", 0.0),
            )
            for d in dependencies
        ]
        graph = ServiceGraph(
            id=str(uuid.uuid4()),
            service_name=service_name,
            dependencies=parsed_deps,
            metrics=metrics or {},
            health=HealthStatus(health),
        )
        return await self.service_graph_repository.save(graph)

    async def get_service_graph(self, service_name: str | None = None) -> list[ServiceGraph]:
        if service_name:
            graph = await self.service_graph_repository.get(service_name)
            return [graph] if graph else []
        return await self.service_graph_repository.list()

    async def get_platform_overview(self) -> PlatformOverview:
        checks = await self.health_check_repository.list()
        firing = await self.alert_event_repository.find_firing()
        firing_count = len(firing)
        critical_count = sum(1 for e in firing if e.severity == AlertSeverity.CRITICAL or e.severity == AlertSeverity.EMERGENCY)

        checks_data = []
        for c in checks:
            checks_data.append({
                "id": c.id,
                "name": c.name,
                "component": c.component,
                "status": c.status.value,
                "last_checked_at": c.last_checked_at.isoformat() if c.last_checked_at else None,
                "failure_count": c.failure_count,
                "success_count": c.success_count,
            })

        recent_alerts = await self.alert_event_repository.list(limit=10)

        overview = PlatformOverview(
            total_services=len(checks),
            healthy_services=sum(1 for c in checks if c.status == HealthStatus.HEALTHY),
            degraded_services=sum(1 for c in checks if c.status == HealthStatus.DEGRADED),
            unhealthy_services=sum(1 for c in checks if c.status == HealthStatus.UNHEALTHY),
            active_alerts=firing_count,
            critical_alerts=critical_count,
            checks=checks_data,
            recent_alerts=[
                {
                    "id": e.id,
                    "rule_id": e.rule_id,
                    "severity": e.severity.value,
                    "status": e.status.value,
                    "message": e.message,
                    "fired_at": e.fired_at.isoformat() if e.fired_at else None,
                }
                for e in recent_alerts
            ],
        )

        if critical_count > 0 or overview.unhealthy_services > 0:
            overview.overall_health = HealthStatus.UNHEALTHY
        elif overview.degraded_services > 0:
            overview.overall_health = HealthStatus.DEGRADED
        elif overview.total_services == 0:
            overview.overall_health = HealthStatus.UNKNOWN
        else:
            overview.overall_health = HealthStatus.HEALTHY

        return overview

    async def export_otel(self, metric: MetricPoint) -> dict[str, Any]:
        return {
            "resourceMetrics": [
                {
                    "resource": {
                        "attributes": [
                            {"key": k, "value": {"stringValue": v}}
                            for k, v in metric.resource_attributes.items()
                        ],
                    },
                    "scopeMetrics": [
                        {
                            "scope": {"name": "gula.national.observability"},
                            "metrics": [
                                {
                                    "name": metric.name,
                                    "unit": "1",
                                    "gauge": {
                                        "dataPoints": [
                                            {
                                                "asDouble": metric.value,
                                                "timeUnixNano": int(metric.timestamp.timestamp() * 1_000_000_000),
                                                "attributes": [
                                                    {"key": k, "value": {"stringValue": v}}
                                                    for k, v in metric.tags.items()
                                                ],
                                            },
                                        ],
                                    },
                                },
                            ],
                        },
                    ],
                },
            ],
        }

    def _publish_event(self, domain_event: Any) -> None:
        try:
            event = Event(
                name=domain_event.event_type,
                data=domain_event.payload if hasattr(domain_event, "payload") else {},
                correlation_id=getattr(domain_event, "correlation_id", ""),
                tenant_id=getattr(domain_event, "tenant_id", ""),
            )
            self.event_bus.publish(event)
        except Exception as exc:
            logger.error(
                "Failed to publish event %s: %s",
                getattr(domain_event, "event_type", "unknown"),
                exc,
            )
