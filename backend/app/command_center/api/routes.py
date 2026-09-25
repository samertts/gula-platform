from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.command_center.application.service import CommandCenterService
from app.command_center.domain.entities import (
    AfterActionReport,
    EmergencyDeclaration,
    ResourceRequest,
    SituationReport,
)
from app.command_center.exceptions import (
    EmergencyAlreadyResolvedError,
    EmergencyNotFoundError,
    ResourceRequestAlreadyClosedError,
    ResourceRequestNotFoundError,
)
from app.database import get_db
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user, require_permission

router = APIRouter(
    prefix="/command-center",
    tags=["National Health Command Center"],
    dependencies=[Depends(require_permission("system:admin"))],
)


def _get_service(db: Session = Depends(get_db)) -> CommandCenterService:
    try:
        from app.kernel import Kernel
        kernel = Kernel.get_instance()
        event_bus = kernel.event_bus if hasattr(kernel, "event_bus") else None
    except Exception:
        event_bus = None
    return CommandCenterService(db=db, event_bus=event_bus)


# ── Emergency Declarations ──

@router.post("/emergencies", status_code=status.HTTP_201_CREATED)
async def declare_emergency(
    body: dict[str, Any],
    service: CommandCenterService = Depends(_get_service),
) -> dict[str, Any]:
    return _emergency_to_dict(service.declare_emergency(body))


@router.get("/emergencies")
async def list_emergencies(
    status: str | None = Query(None),
    emergency_type: str | None = Query(None),
    region: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: CommandCenterService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_emergency_to_dict(e) for e in service.list_emergencies(status, emergency_type, region, skip, limit)]


@router.get("/emergencies/{emergency_id}")
async def get_emergency(
    emergency_id: str,
    service: CommandCenterService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _emergency_to_dict(service.get_emergency(emergency_id))
    except EmergencyNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e


@router.post("/emergencies/{emergency_id}/resolve")
async def resolve_emergency(
    emergency_id: str,
    body: dict[str, Any],
    service: CommandCenterService = Depends(_get_service),
    current_user: LabUser = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        return _emergency_to_dict(service.resolve_emergency(
            emergency_id, body.get("resolved_by", ""), body.get("notes", ""),
            actor_lab_id=current_user.lab_id))
    except EmergencyNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e
    except EmergencyAlreadyResolvedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


# ── Resource Requests ──

@router.post("/resource-requests", status_code=status.HTTP_201_CREATED)
async def request_resource(
    body: dict[str, Any],
    service: CommandCenterService = Depends(_get_service),
) -> dict[str, Any]:
    return _resource_to_dict(service.request_resource(body))


@router.get("/resource-requests")
async def list_resource_requests(
    emergency_id: str | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: CommandCenterService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_resource_to_dict(r) for r in service.list_resource_requests(emergency_id, status, skip, limit)]


@router.post("/resource-requests/{request_id}/fulfill")
async def fulfill_resource(
    request_id: str,
    body: dict[str, Any],
    service: CommandCenterService = Depends(_get_service),
    current_user: LabUser = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        return _resource_to_dict(service.fulfill_resource(
            request_id, body, actor_lab_id=current_user.lab_id))
    except ResourceRequestNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e
    except ResourceRequestAlreadyClosedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


# ── Situation Reports ──

@router.post("/situation-reports", status_code=status.HTTP_201_CREATED)
async def publish_situation_report(
    body: dict[str, Any],
    service: CommandCenterService = Depends(_get_service),
) -> dict[str, Any]:
    return _situation_to_dict(service.publish_situation_report(body))


@router.get("/situation-reports")
async def list_situation_reports(
    emergency_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: CommandCenterService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_situation_to_dict(s) for s in service.list_situation_reports(emergency_id, skip, limit)]


# ── After-Action Reports ──

@router.post("/after-action-reports", status_code=status.HTTP_201_CREATED)
async def complete_after_action(
    body: dict[str, Any],
    service: CommandCenterService = Depends(_get_service),
) -> dict[str, Any]:
    return _after_action_to_dict(service.complete_after_action(body))


@router.get("/after-action-reports")
async def list_after_action_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: CommandCenterService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_after_action_to_dict(r) for r in service.list_after_action_reports(skip, limit)]


# ── Unified Dashboard ──

@router.get("/dashboard")
async def get_unified_dashboard(
    service: CommandCenterService = Depends(_get_service),
) -> dict[str, Any]:
    return service.get_unified_command_dashboard()


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "module": "national_health_command_center", "version": "1.0.0"}


# ── Serializers ──

def _emergency_to_dict(e: EmergencyDeclaration) -> dict[str, Any]:
    return {
        "id": e.id, "emergency_type": e.emergency_type, "level": e.level,
        "status": e.status, "region": e.region, "description": e.description,
        "declared_by": e.declared_by, "declared_at": e.declared_at,
        "resolved_at": e.resolved_at,
    }


def _resource_to_dict(r: ResourceRequest) -> dict[str, Any]:
    return {
        "id": r.id, "emergency_id": r.emergency_id, "resource_type": r.resource_type,
        "quantity": r.quantity, "priority": r.priority, "status": r.status,
        "requested_by": r.requested_by, "requested_at": r.requested_at,
    }


def _situation_to_dict(s: SituationReport) -> dict[str, Any]:
    return {
        "id": s.id, "emergency_id": s.emergency_id, "report_number": s.report_number,
        "summary": s.summary, "published_by": s.published_by, "published_at": s.published_at,
    }


def _after_action_to_dict(a: AfterActionReport) -> dict[str, Any]:
    return {
        "id": a.id, "emergency_id": a.emergency_id, "emergency_type": a.emergency_type,
        "region": a.region, "overall_rating": a.overall_rating, "completed_by": a.completed_by,
    }
