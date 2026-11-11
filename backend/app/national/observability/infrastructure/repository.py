from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC
from app.national.observability.domain.entities import (
    AlertEvent,
    AlertRule,
    Dashboard,
    DashboardPanel,
    HealthCheck,
    MetricPoint,
    ServiceGraph,
    TraceSpan,
)
from app.national.observability.domain.enums import AlertSeverity, AlertStatus, HealthStatus
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
from app.national.observability.infrastructure.models import (
    NationalAlertEvent,
    NationalAlertRule,
    NationalDashboard,
    NationalDashboardPanel,
    NationalHealthCheck,
    NationalMetricPoint,
    NationalServiceGraph,
    NationalTraceSpan,
)


class SQLAlchemyMetricRepository(MetricRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, metric: MetricPoint) -> MetricPoint:
        model = NationalMetricPoint(
            id=metric.id,
            name=metric.name,
            type=metric.type,
            value=metric.value,
            tags=metric.tags,
            timestamp=metric.timestamp,
            resource_attributes=metric.resource_attributes,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def save_many(self, metrics: list[MetricPoint]) -> list[MetricPoint]:
        models = []
        for m in metrics:
            model = NationalMetricPoint(
                id=m.id,
                name=m.name,
                type=m.type,
                value=m.value,
                tags=m.tags,
                timestamp=m.timestamp,
                resource_attributes=m.resource_attributes,
            )
            self.db.add(model)
            models.append(model)
        self.db.commit()
        return [m.to_domain() for m in models]

    async def query(
        self,
        name: str | None = None,
        tags: dict[str, str] | None = None,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        aggregate: str = "avg",
        group_by: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = self.db.query(NationalMetricPoint)
        if name:
            query = query.filter(NationalMetricPoint.name == name)
        if from_time:
            query = query.filter(NationalMetricPoint.timestamp >= from_time)
        if to_time:
            query = query.filter(NationalMetricPoint.timestamp <= to_time)
        rows = query.order_by(NationalMetricPoint.timestamp.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "name": r.name,
                "type": r.type.value,
                "value": r.value,
                "tags": r.tags,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in rows
        ]

    async def get_stats(self) -> dict[str, Any]:
        total = self.db.query(func.count(NationalMetricPoint.id)).scalar() or 0
        by_name = self.db.query(
            NationalMetricPoint.name,
            func.count(NationalMetricPoint.id).label("count"),
        ).group_by(NationalMetricPoint.name).all()
        return {
            "total": total,
            "by_metric": {row.name: row.count for row in by_name},
        }

    async def get_metric_names(self) -> list[str]:
        rows = self.db.query(NationalMetricPoint.name).distinct().all()
        return [r.name for r in rows]


class SQLAlchemyTraceSpanRepository(TraceSpanRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, span: TraceSpan) -> TraceSpan:
        model = self.db.query(NationalTraceSpan).filter(NationalTraceSpan.id == span.id).first()
        if model:
            model.trace_id = span.trace_id
            model.parent_span_id = span.parent_span_id
            model.name = span.name
            model.service = span.service
            model.operation = span.operation
            model.start_time = span.start_time
            model.end_time = span.end_time
            model.duration_ms = span.duration_ms
            model.status = span.status
            model.attributes = span.attributes
            model.events = span.events
        else:
            model = NationalTraceSpan(
                id=span.id,
                trace_id=span.trace_id,
                parent_span_id=span.parent_span_id or None,
                name=span.name,
                service=span.service,
                operation=span.operation,
                start_time=span.start_time,
                end_time=span.end_time,
                duration_ms=span.duration_ms,
                status=span.status,
                attributes=span.attributes,
                events=span.events,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, span_id: str) -> TraceSpan | None:
        model = self.db.query(NationalTraceSpan).filter(NationalTraceSpan.id == span_id).first()
        if not model:
            return None
        return model.to_domain()

    async def find_by_trace(self, trace_id: str) -> list[TraceSpan]:
        models = self.db.query(NationalTraceSpan).filter(
            NationalTraceSpan.trace_id == trace_id,
        ).order_by(NationalTraceSpan.start_time.asc()).all()
        return [m.to_domain() for m in models]

    async def search(
        self,
        service: str | None = None,
        operation: str | None = None,
        min_duration: float | None = None,
        max_duration: float | None = None,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[TraceSpan]:
        query = self.db.query(NationalTraceSpan)
        if service:
            query = query.filter(NationalTraceSpan.service == service)
        if operation:
            query = query.filter(NationalTraceSpan.operation == operation)
        if min_duration is not None:
            query = query.filter(NationalTraceSpan.duration_ms >= min_duration)
        if max_duration is not None:
            query = query.filter(NationalTraceSpan.duration_ms <= max_duration)
        if from_time:
            query = query.filter(NationalTraceSpan.start_time >= from_time)
        if to_time:
            query = query.filter(NationalTraceSpan.start_time <= to_time)
        if status:
            from app.national.observability.domain.enums import SpanStatus
            query = query.filter(NationalTraceSpan.status == SpanStatus(status))
        models = query.order_by(NationalTraceSpan.start_time.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def get_stats(self) -> dict[str, Any]:
        total = self.db.query(func.count(NationalTraceSpan.id)).scalar() or 0
        by_service = self.db.query(
            NationalTraceSpan.service,
            func.count(NationalTraceSpan.id).label("count"),
        ).group_by(NationalTraceSpan.service).all()
        avg_duration = self.db.query(
            func.avg(NationalTraceSpan.duration_ms),
        ).scalar() or 0.0
        return {
            "total": total,
            "by_service": {row.service: row.count for row in by_service if row.service},
            "avg_duration_ms": round(float(avg_duration), 2),
        }


class SQLAlchemyHealthCheckRepository(HealthCheckRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, check: HealthCheck) -> HealthCheck:
        model = self.db.query(NationalHealthCheck).filter(NationalHealthCheck.id == check.id).first()
        if model:
            model.name = check.name
            model.component = check.component
            model.status = check.status
            model.last_checked_at = check.last_checked_at
            model.last_success_at = check.last_success_at
            model.last_failure_at = check.last_failure_at
            model.failure_count = check.failure_count
            model.success_count = check.success_count
            model.details = check.details
            model.tags = check.tags
        else:
            model = NationalHealthCheck(
                id=check.id,
                name=check.name,
                component=check.component,
                status=check.status,
                last_checked_at=check.last_checked_at,
                last_success_at=check.last_success_at,
                last_failure_at=check.last_failure_at,
                failure_count=check.failure_count,
                success_count=check.success_count,
                details=check.details,
                tags=check.tags,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, check_id: str) -> HealthCheck | None:
        model = self.db.query(NationalHealthCheck).filter(
            NationalHealthCheck.id == check_id,
            ~NationalHealthCheck.is_deleted,
        ).first()
        if not model:
            return None
        return model.to_domain()

    async def list(self) -> list[HealthCheck]:
        models = self.db.query(NationalHealthCheck).filter(
            ~NationalHealthCheck.is_deleted,
        ).order_by(NationalHealthCheck.name.asc()).all()
        return [m.to_domain() for m in models]

    async def find_by_name(self, name: str) -> HealthCheck | None:
        model = self.db.query(NationalHealthCheck).filter(
            NationalHealthCheck.name == name,
            ~NationalHealthCheck.is_deleted,
        ).first()
        if not model:
            return None
        return model.to_domain()

    async def get_overall_status(self) -> dict[str, Any]:
        checks = await self.list()
        by_status: dict[str, int] = {}
        for c in checks:
            key = c.status.value
            by_status[key] = by_status.get(key, 0) + 1
        return {
            "total": len(checks),
            "by_status": by_status,
            "healthy": sum(1 for c in checks if c.status == HealthStatus.HEALTHY),
            "degraded": sum(1 for c in checks if c.status == HealthStatus.DEGRADED),
            "unhealthy": sum(1 for c in checks if c.status == HealthStatus.UNHEALTHY),
            "unknown": sum(1 for c in checks if c.status == HealthStatus.UNKNOWN),
        }


class SQLAlchemyAlertRuleRepository(AlertRuleRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, rule: AlertRule) -> AlertRule:
        model = self.db.query(NationalAlertRule).filter(NationalAlertRule.id == rule.id).first()
        if model:
            model.name = rule.name
            model.metric_name = rule.metric_name
            model.condition = rule.condition
            model.threshold = rule.threshold
            model.duration_seconds = rule.duration_seconds
            model.severity = rule.severity
            model.channels = rule.channels
            model.enabled = rule.enabled
        else:
            model = NationalAlertRule(
                id=rule.id,
                name=rule.name,
                metric_name=rule.metric_name,
                condition=rule.condition,
                threshold=rule.threshold,
                duration_seconds=rule.duration_seconds,
                severity=rule.severity,
                channels=rule.channels,
                enabled=rule.enabled,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, rule_id: str) -> AlertRule | None:
        model = self.db.query(NationalAlertRule).filter(
            NationalAlertRule.id == rule_id,
            ~NationalAlertRule.is_deleted,
        ).first()
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AlertRule]:
        models = self.db.query(NationalAlertRule).filter(
            ~NationalAlertRule.is_deleted,
        ).order_by(NationalAlertRule.created_at.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def delete(self, rule_id: str) -> None:
        model = self.db.query(NationalAlertRule).filter(
            NationalAlertRule.id == rule_id,
            ~NationalAlertRule.is_deleted,
        ).first()
        if model:
            model.is_deleted = True
            model.deleted_at = datetime.now(UTC)
            self.db.commit()

    async def find_enabled(self) -> list[AlertRule]:
        models = self.db.query(NationalAlertRule).filter(
            NationalAlertRule.enabled,
            ~NationalAlertRule.is_deleted,
        ).all()
        return [m.to_domain() for m in models]


class SQLAlchemyAlertEventRepository(AlertEventRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, event: AlertEvent) -> AlertEvent:
        model = self.db.query(NationalAlertEvent).filter(NationalAlertEvent.id == event.id).first()
        if model:
            model.rule_id = event.rule_id
            model.metric_value = event.metric_value
            model.severity = event.severity
            model.status = event.status
            model.fired_at = event.fired_at
            model.resolved_at = event.resolved_at
            model.acknowledged_by = event.acknowledged_by
            model.acknowledged_at = event.acknowledged_at
            model.message = event.message
        else:
            model = NationalAlertEvent(
                id=event.id,
                rule_id=event.rule_id,
                metric_value=event.metric_value,
                severity=event.severity,
                status=event.status,
                fired_at=event.fired_at,
                resolved_at=event.resolved_at,
                acknowledged_by=event.acknowledged_by,
                acknowledged_at=event.acknowledged_at,
                message=event.message,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, event_id: str) -> AlertEvent | None:
        model = self.db.query(NationalAlertEvent).filter(NationalAlertEvent.id == event_id).first()
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        status: AlertStatus | None = None,
        severity: AlertSeverity | None = None,
        rule_id: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AlertEvent]:
        query = self.db.query(NationalAlertEvent)
        if status:
            query = query.filter(NationalAlertEvent.status == status)
        if severity:
            query = query.filter(NationalAlertEvent.severity == severity)
        if rule_id:
            query = query.filter(NationalAlertEvent.rule_id == rule_id)
        models = query.order_by(NationalAlertEvent.fired_at.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def find_firing(self) -> list[AlertEvent]:
        models = self.db.query(NationalAlertEvent).filter(
            NationalAlertEvent.status == AlertStatus.FIRING,
        ).all()
        return [m.to_domain() for m in models]

    async def get_active_count_by_severity(self) -> dict[str, int]:
        rows = self.db.query(
            NationalAlertEvent.severity,
            func.count(NationalAlertEvent.id).label("count"),
        ).filter(
            NationalAlertEvent.status == AlertStatus.FIRING,
        ).group_by(NationalAlertEvent.severity).all()
        return {row.severity.value: row.count for row in rows}


class SQLAlchemyDashboardRepository(DashboardRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, dashboard: Dashboard) -> Dashboard:
        model = self.db.query(NationalDashboard).filter(NationalDashboard.id == dashboard.id).first()
        if model:
            model.name = dashboard.name
            model.description = dashboard.description
            model.refresh_interval = dashboard.refresh_interval
            model.created_by = dashboard.created_by
        else:
            model = NationalDashboard(
                id=dashboard.id,
                name=dashboard.name,
                description=dashboard.description,
                refresh_interval=dashboard.refresh_interval,
                created_by=dashboard.created_by,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, dashboard_id: str) -> Dashboard | None:
        model = self.db.query(NationalDashboard).filter(
            NationalDashboard.id == dashboard_id,
            ~NationalDashboard.is_deleted,
        ).first()
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Dashboard]:
        models = self.db.query(NationalDashboard).filter(
            ~NationalDashboard.is_deleted,
        ).order_by(NationalDashboard.created_at.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def delete(self, dashboard_id: str) -> None:
        model = self.db.query(NationalDashboard).filter(
            NationalDashboard.id == dashboard_id,
            ~NationalDashboard.is_deleted,
        ).first()
        if model:
            model.is_deleted = True
            model.deleted_at = datetime.now(UTC)
            self.db.commit()


class SQLAlchemyDashboardPanelRepository(DashboardPanelRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, panel: DashboardPanel) -> DashboardPanel:
        model = self.db.query(NationalDashboardPanel).filter(NationalDashboardPanel.id == panel.id).first()
        if model:
            model.dashboard_id = panel.dashboard_id
            model.title = panel.title
            model.metric_names = panel.metric_names
            model.chart_type = panel.chart_type
            model.width = panel.width
            model.height = panel.height
            model.position = panel.position
        else:
            model = NationalDashboardPanel(
                id=panel.id,
                dashboard_id=panel.dashboard_id,
                title=panel.title,
                metric_names=panel.metric_names,
                chart_type=panel.chart_type,
                width=panel.width,
                height=panel.height,
                position=panel.position,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def save_many(self, panels: list[DashboardPanel]) -> list[DashboardPanel]:
        saved = []
        for p in panels:
            saved.append(await self.save(p))
        return saved

    async def find_by_dashboard(self, dashboard_id: str) -> list[DashboardPanel]:
        models = self.db.query(NationalDashboardPanel).filter(
            NationalDashboardPanel.dashboard_id == dashboard_id,
        ).order_by(NationalDashboardPanel.position.asc()).all()
        return [m.to_domain() for m in models]

    async def delete_by_dashboard(self, dashboard_id: str) -> None:
        models = self.db.query(NationalDashboardPanel).filter(
            NationalDashboardPanel.dashboard_id == dashboard_id,
        ).all()
        for m in models:
            self.db.delete(m)
        self.db.commit()


class SQLAlchemyServiceGraphRepository(ServiceGraphRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, graph: ServiceGraph) -> ServiceGraph:
        model = self.db.query(NationalServiceGraph).filter(
            NationalServiceGraph.service_name == graph.service_name,
        ).first()
        if model:
            model.dependencies = [
                {
                    "source": d.source,
                    "target": d.target,
                    "type": d.type,
                    "latency_p50": d.latency_p50,
                    "latency_p99": d.latency_p99,
                    "error_rate": d.error_rate,
                }
                for d in graph.dependencies
            ]
            model.metrics = graph.metrics
            model.health = graph.health
        else:
            model = NationalServiceGraph(
                id=graph.id,
                service_name=graph.service_name,
                dependencies=[
                    {
                        "source": d.source,
                        "target": d.target,
                        "type": d.type,
                        "latency_p50": d.latency_p50,
                        "latency_p99": d.latency_p99,
                        "error_rate": d.error_rate,
                    }
                    for d in graph.dependencies
                ],
                metrics=graph.metrics,
                health=graph.health,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, service_name: str) -> ServiceGraph | None:
        model = self.db.query(NationalServiceGraph).filter(
            NationalServiceGraph.service_name == service_name,
            ~NationalServiceGraph.is_deleted,
        ).first()
        if not model:
            return None
        return model.to_domain()

    async def list(self) -> list[ServiceGraph]:
        models = self.db.query(NationalServiceGraph).filter(
            ~NationalServiceGraph.is_deleted,
        ).all()
        return [m.to_domain() for m in models]

    async def delete(self, service_name: str) -> None:
        model = self.db.query(NationalServiceGraph).filter(
            NationalServiceGraph.service_name == service_name,
            ~NationalServiceGraph.is_deleted,
        ).first()
        if model:
            model.is_deleted = True
            model.deleted_at = datetime.now(UTC)
            self.db.commit()
