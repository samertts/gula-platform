from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.national.observability.application.service import ObservabilityService
from app.national.observability.exceptions import (
    AlertEventNotFoundError,
    AlertRuleNotFoundError,
    DashboardNotFoundError,
    MetricQueryError,
)
from app.national.observability.infrastructure.repository import (
    SQLAlchemyAlertEventRepository,
    SQLAlchemyAlertRuleRepository,
    SQLAlchemyDashboardPanelRepository,
    SQLAlchemyDashboardRepository,
    SQLAlchemyHealthCheckRepository,
    SQLAlchemyMetricRepository,
    SQLAlchemyServiceGraphRepository,
    SQLAlchemyTraceSpanRepository,
)

router = APIRouter(prefix="/national/observability", tags=["National Observability"])


def _get_service(db: Session = Depends(get_db)) -> ObservabilityService:
    from app.kernel import Kernel
    from app.kernel.event_bus.bus import EventBus

    kernel = Kernel.get_instance()
    event_bus = kernel.event_bus if hasattr(kernel, "event_bus") else EventBus(kernel)
    return ObservabilityService(
        metric_repository=SQLAlchemyMetricRepository(db),
        trace_span_repository=SQLAlchemyTraceSpanRepository(db),
        health_check_repository=SQLAlchemyHealthCheckRepository(db),
        alert_rule_repository=SQLAlchemyAlertRuleRepository(db),
        alert_event_repository=SQLAlchemyAlertEventRepository(db),
        dashboard_repository=SQLAlchemyDashboardRepository(db),
        dashboard_panel_repository=SQLAlchemyDashboardPanelRepository(db),
        service_graph_repository=SQLAlchemyServiceGraphRepository(db),
        event_bus=event_bus,
    )


@router.post("/metrics", status_code=status.HTTP_201_CREATED)
async def record_metrics(
    body: dict[str, Any],
    service: ObservabilityService = Depends(_get_service),
) -> dict[str, Any]:
    metrics = body.get("metrics", [body])
    if not isinstance(metrics, list):
        metrics = [body]
    recorded = await service.record_metrics_batch(metrics)
    return {
        "recorded": len(recorded),
        "status": "ok",
    }


@router.get("/metrics/query")
async def query_metrics(
    name: str | None = Query(None),
    from_time: str | None = Query(None),
    to_time: str | None = Query(None),
    aggregate: str = Query("avg"),
    group_by: str | None = Query(None),
    limit: int = Query(100, ge=1, le=10000),
    service: ObservabilityService = Depends(_get_service),
) -> list[dict[str, Any]]:
    try:
        tags = None
        parsed_group_by = group_by.split(",") if group_by else None
        return await service.query_metrics(
            name=name,
            tags=tags,
            from_time=from_time,
            to_time=to_time,
            aggregate=aggregate,
            group_by=parsed_group_by,
            limit=limit,
        )
    except MetricQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Validation error",
        ) from e


@router.post("/traces", status_code=status.HTTP_201_CREATED)
async def record_traces(
    body: dict[str, Any],
    service: ObservabilityService = Depends(_get_service),
) -> dict[str, Any]:
    spans = body.get("spans", [body])
    saved = []
    for span_data in spans:
        span = await service.start_span(
            trace_id=span_data.get("trace_id", ""),
            name=span_data.get("name", ""),
            service=span_data.get("service", ""),
            operation=span_data.get("operation", ""),
            parent_span_id=span_data.get("parent_span_id", ""),
            attributes=span_data.get("attributes"),
        )
        ended = await service.end_span(
            span=span,
            status=span_data.get("status", "ok"),
            attributes=span_data.get("attributes"),
        )
        saved.append(ended)
    return {"recorded": len(saved), "status": "ok"}


@router.get("/traces/{trace_id}")
async def get_trace(
    trace_id: str,
    service: ObservabilityService = Depends(_get_service),
) -> list[dict[str, Any]]:
    spans = await service.query_traces(trace_id=trace_id)
    return [_span_to_dict(s) for s in spans]


@router.get("/traces/search")
async def search_traces(
    service: str | None = Query(None),
    operation: str | None = Query(None),
    min_duration: float | None = Query(None),
    max_duration: float | None = Query(None),
    from_time: str | None = Query(None),
    to_time: str | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    svc: ObservabilityService = Depends(_get_service),
) -> list[dict[str, Any]]:
    spans = await svc.query_traces(
        service=service,
        operation=operation,
        min_duration=min_duration,
        max_duration=max_duration,
        from_time=from_time,
        to_time=to_time,
        status=status,
        skip=skip,
        limit=limit,
    )
    return [_span_to_dict(s) for s in spans]


@router.post("/health/checks/{name}")
async def run_health_check(
    name: str,
    body: dict[str, Any],
    service: ObservabilityService = Depends(_get_service),
) -> dict[str, Any]:
    check = await service.run_health_check(
        name=name,
        is_healthy=body.get("is_healthy", True),
        details=body.get("details"),
    )
    return _health_check_to_dict(check)


@router.get("/health/checks")
async def list_health_checks(
    service: ObservabilityService = Depends(_get_service),
) -> list[dict[str, Any]]:
    checks = await service.get_all_health_checks()
    return [_health_check_to_dict(c) for c in checks]


@router.get("/health/status")
async def health_status(
    service: ObservabilityService = Depends(_get_service),
) -> dict[str, Any]:
    return await service.get_health_status()


@router.get("/health")
async def health(
    service: ObservabilityService = Depends(_get_service),
) -> dict[str, Any]:
    status = await service.get_health_status()
    return {
        "status": "ok" if status.get("unhealthy", 0) == 0 else "degraded",
        "module": "national_observability",
        "version": "1.0.0",
        "checks": status,
    }


@router.post("/alerts/rules", status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    body: dict[str, Any],
    service: ObservabilityService = Depends(_get_service),
) -> dict[str, Any]:
    rule = await service.create_alert_rule(
        name=body.get("name", ""),
        metric_name=body.get("metric_name", ""),
        condition=body.get("condition", "gt"),
        threshold=body.get("threshold", 0.0),
        duration_seconds=body.get("duration_seconds", 60),
        severity=body.get("severity", "warning"),
        channels=body.get("channels"),
    )
    return _alert_rule_to_dict(rule)


@router.get("/alerts/rules")
async def list_alert_rules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ObservabilityService = Depends(_get_service),
) -> list[dict[str, Any]]:
    rules = await service.list_alert_rules(skip=skip, limit=limit)
    return [_alert_rule_to_dict(r) for r in rules]


@router.get("/alerts/rules/{rule_id}")
async def get_alert_rule(
    rule_id: str,
    service: ObservabilityService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        rule = await service.get_alert_rule(rule_id)
        return _alert_rule_to_dict(rule)
    except AlertRuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.put("/alerts/rules/{rule_id}")
async def update_alert_rule(
    rule_id: str,
    body: dict[str, Any],
    service: ObservabilityService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        rule = await service.update_alert_rule(rule_id, body)
        return _alert_rule_to_dict(rule)
    except AlertRuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.delete("/alerts/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    rule_id: str,
    service: ObservabilityService = Depends(_get_service),
) -> None:
    try:
        await service.delete_alert_rule(rule_id)
    except AlertRuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.post("/alerts/rules/{rule_id}/evaluate")
async def evaluate_alert_rule(
    rule_id: str,
    service: ObservabilityService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        event = await service.evaluate_alert(rule_id)
        if event:
            return _alert_event_to_dict(event)
        return {"status": "ok", "message": "No alert triggered"}
    except AlertRuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.get("/alerts/events")
async def list_alert_events(
    status: str | None = Query(None),
    severity: str | None = Query(None),
    rule_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ObservabilityService = Depends(_get_service),
) -> list[dict[str, Any]]:
    events = await service.list_alert_events(
        status=status,
        severity=severity,
        rule_id=rule_id,
        skip=skip,
        limit=limit,
    )
    return [_alert_event_to_dict(e) for e in events]


@router.post("/alerts/events/{event_id}/acknowledge")
async def acknowledge_alert(
    event_id: str,
    body: dict[str, Any] | None = None,
    service: ObservabilityService = Depends(_get_service),
) -> dict[str, Any]:
    if body is None:
        body = {}
    try:
        event = await service.acknowledge_alert(
            event_id=event_id,
            acknowledged_by=body.get("acknowledged_by", ""),
        )
        return _alert_event_to_dict(event)
    except AlertEventNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.post("/alerts/events/{event_id}/silence")
async def silence_alert(
    event_id: str,
    service: ObservabilityService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        event = await service.silence_alert(event_id)
        return _alert_event_to_dict(event)
    except AlertEventNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.post("/dashboards", status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    body: dict[str, Any],
    service: ObservabilityService = Depends(_get_service),
) -> dict[str, Any]:
    dashboard = await service.create_dashboard(
        name=body.get("name", ""),
        description=body.get("description", ""),
        panels=body.get("panels"),
        refresh_interval=body.get("refresh_interval", 60),
        created_by=body.get("created_by", ""),
    )
    return _dashboard_to_dict(dashboard)


@router.get("/dashboards")
async def list_dashboards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ObservabilityService = Depends(_get_service),
) -> list[dict[str, Any]]:
    dashboards = await service.list_dashboards(skip=skip, limit=limit)
    return [_dashboard_to_dict(d) for d in dashboards]


@router.get("/dashboards/{dashboard_id}")
async def get_dashboard(
    dashboard_id: str,
    service: ObservabilityService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        dashboard = await service.get_dashboard(dashboard_id)
        return _dashboard_to_dict(dashboard)
    except DashboardNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.put("/dashboards/{dashboard_id}")
async def update_dashboard(
    dashboard_id: str,
    body: dict[str, Any],
    service: ObservabilityService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        dashboard = await service.update_dashboard(
            dashboard_id=dashboard_id,
            updates={k: v for k, v in body.items() if k != "panels"},
            panels=body.get("panels"),
        )
        return _dashboard_to_dict(dashboard)
    except DashboardNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.delete("/dashboards/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: str,
    service: ObservabilityService = Depends(_get_service),
) -> None:
    try:
        await service.delete_dashboard(dashboard_id)
    except DashboardNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.get("/overview")
async def get_platform_overview(
    service: ObservabilityService = Depends(_get_service),
) -> dict[str, Any]:
    overview = await service.get_platform_overview()
    return {
        "overall_health": overview.overall_health.value,
        "total_services": overview.total_services,
        "healthy_services": overview.healthy_services,
        "degraded_services": overview.degraded_services,
        "unhealthy_services": overview.unhealthy_services,
        "active_alerts": overview.active_alerts,
        "critical_alerts": overview.critical_alerts,
        "checks": overview.checks,
        "recent_alerts": overview.recent_alerts,
    }


@router.get("/service-graph")
async def get_service_graph(
    service_name: str | None = Query(None),
    service: ObservabilityService = Depends(_get_service),
) -> list[dict[str, Any]]:
    graphs = await service.get_service_graph(service_name=service_name)
    return [_service_graph_to_dict(g) for g in graphs]


@router.post("/service-graph", status_code=status.HTTP_201_CREATED)
async def record_service_graph(
    body: dict[str, Any],
    service: ObservabilityService = Depends(_get_service),
) -> dict[str, Any]:
    graph = await service.record_service_graph(
        service_name=body.get("service_name", ""),
        dependencies=body.get("dependencies", []),
        metrics=body.get("metrics"),
        health=body.get("health", "unknown"),
    )
    return _service_graph_to_dict(graph)


def _span_to_dict(s: Any) -> dict[str, Any]:
    return {
        "id": s.id,
        "trace_id": s.trace_id,
        "parent_span_id": s.parent_span_id,
        "name": s.name,
        "service": s.service,
        "operation": s.operation,
        "start_time": s.start_time.isoformat() if s.start_time else None,
        "end_time": s.end_time.isoformat() if s.end_time else None,
        "duration_ms": s.duration_ms,
        "status": s.status.value,
        "attributes": s.attributes,
        "events": s.events,
    }


def _health_check_to_dict(c: Any) -> dict[str, Any]:
    return {
        "id": c.id,
        "name": c.name,
        "component": c.component,
        "status": c.status.value,
        "last_checked_at": c.last_checked_at.isoformat() if c.last_checked_at else None,
        "last_success_at": c.last_success_at.isoformat() if c.last_success_at else None,
        "last_failure_at": c.last_failure_at.isoformat() if c.last_failure_at else None,
        "failure_count": c.failure_count,
        "success_count": c.success_count,
        "details": c.details,
        "tags": c.tags,
    }


def _alert_rule_to_dict(r: Any) -> dict[str, Any]:
    return {
        "id": r.id,
        "name": r.name,
        "metric_name": r.metric_name,
        "condition": r.condition,
        "threshold": r.threshold,
        "duration_seconds": r.duration_seconds,
        "severity": r.severity.value,
        "channels": r.channels,
        "enabled": r.enabled,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _alert_event_to_dict(e: Any) -> dict[str, Any]:
    return {
        "id": e.id,
        "rule_id": e.rule_id,
        "metric_value": e.metric_value,
        "severity": e.severity.value,
        "status": e.status.value,
        "fired_at": e.fired_at.isoformat() if e.fired_at else None,
        "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
        "acknowledged_by": e.acknowledged_by,
        "acknowledged_at": e.acknowledged_at.isoformat() if e.acknowledged_at else None,
        "message": e.message,
    }


def _dashboard_to_dict(d: Any) -> dict[str, Any]:
    return {
        "id": d.id,
        "name": d.name,
        "description": d.description,
        "panels": [
            {
                "id": p.id,
                "dashboard_id": p.dashboard_id,
                "title": p.title,
                "metric_names": p.metric_names,
                "chart_type": p.chart_type,
                "width": p.width,
                "height": p.height,
                "position": p.position,
            }
            for p in d.panels
        ],
        "refresh_interval": d.refresh_interval,
        "created_by": d.created_by,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }


def _service_graph_to_dict(g: Any) -> dict[str, Any]:
    return {
        "id": g.id,
        "service_name": g.service_name,
        "dependencies": [
            {
                "source": d.source,
                "target": d.target,
                "type": d.type,
                "latency_p50": d.latency_p50,
                "latency_p99": d.latency_p99,
                "error_rate": d.error_rate,
            }
            for d in g.dependencies
        ],
        "metrics": g.metrics,
        "health": g.health.value,
    }
