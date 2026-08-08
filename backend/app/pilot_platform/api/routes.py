from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.pilot_platform.application.service import PilotPlatformService
from app.pilot_platform.domain.entities import (
    DeploymentRecord,
    GoNoGoGate,
    PilotFacility,
    PilotProgram,
    ReadinessChecklist,
)
from app.pilot_platform.exceptions import (
    PilotNotFoundError,
    ReadinessAssessmentNotFoundError,
)
from app.security.dependencies import get_current_user

router = APIRouter(
    prefix="/pilot-platform",
    tags=["National Pilot Deployment & Readiness"],
    dependencies=[Depends(get_current_user)],
)


def _get_service(db: Session = Depends(get_db)) -> PilotPlatformService:
    try:
        from app.kernel import Kernel

        kernel = Kernel.get_instance()
        event_bus = kernel.event_bus if hasattr(kernel, "event_bus") else None
    except Exception:
        event_bus = None
    return PilotPlatformService(db=db, event_bus=event_bus)


# ── Pilot Programs ──


@router.post("/pilots", status_code=status.HTTP_201_CREATED)
async def create_pilot(
    body: dict[str, Any],
    service: PilotPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    return _program_to_dict(service.create_pilot(body))


@router.get("/pilots")
async def list_pilots(
    status: str | None = Query(None),
    module_name: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: PilotPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_program_to_dict(p) for p in service.list_pilots(status, module_name, skip, limit)]


@router.get("/pilots/{pilot_id}")
async def get_pilot(
    pilot_id: str,
    service: PilotPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _program_to_dict(service.get_pilot(pilot_id))
    except PilotNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        ) from e


@router.put("/pilots/{pilot_id}/phase")
async def advance_phase(
    pilot_id: str,
    body: dict[str, Any],
    service: PilotPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _program_to_dict(service.advance_phase(pilot_id, body.get("phase", "")))
    except PilotNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        ) from e


# ── Pilot Facilities ──


@router.post("/facilities", status_code=status.HTTP_201_CREATED)
async def enroll_facility(
    body: dict[str, Any],
    service: PilotPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    return _facility_to_dict(service.enroll_facility(body))


@router.get("/pilots/{pilot_id}/facilities")
async def list_pilot_facilities(
    pilot_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: PilotPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_facility_to_dict(f) for f in service.list_pilot_facilities(pilot_id, skip, limit)]


# ── Readiness Assessments ──


@router.post("/readiness", status_code=status.HTTP_201_CREATED)
async def assess_readiness(
    body: dict[str, Any],
    service: PilotPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    return _readiness_to_dict(service.assess_readiness(body))


@router.get("/facilities/{facility_id}/readiness")
async def get_facility_readiness(
    facility_id: str,
    pilot_id: str = Query(...),
    service: PilotPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _readiness_to_dict(service.get_facility_readiness(facility_id, pilot_id))
    except ReadinessAssessmentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        ) from e


# ── Go/No-Go Gates ──


@router.post("/gates", status_code=status.HTTP_201_CREATED)
async def decide_gate(
    body: dict[str, Any],
    service: PilotPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    return _gate_to_dict(service.decide_gate(body))


@router.get("/pilots/{pilot_id}/gates")
async def list_gates(
    pilot_id: str,
    facility_id: str | None = Query(None),
    service: PilotPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_gate_to_dict(g) for g in service.list_gates(pilot_id, facility_id)]


# ── Deployment Records ──


@router.post("/deployments", status_code=status.HTTP_201_CREATED)
async def record_deployment(
    body: dict[str, Any],
    service: PilotPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    return _deployment_to_dict(service.record_deployment(body))


@router.get("/deployments")
async def list_deployments(
    pilot_id: str | None = Query(None),
    facility_id: str | None = Query(None),
    service: PilotPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_deployment_to_dict(d) for d in service.list_deployments(pilot_id, facility_id)]


# ── Certification Integration ──


@router.get("/certify/{module_path:path}")
async def evaluate_certification(
    module_path: str,
    pilot_id: str = Query(...),
    service: PilotPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    return service.evaluate_with_certification(module_path, pilot_id)


# ── Dashboard ──


@router.get("/dashboard")
async def get_dashboard(
    service: PilotPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    return service.get_dashboard()


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "module": "national_pilot_platform", "version": "1.0.0"}


# ── Serializers ──


def _program_to_dict(p: PilotProgram) -> dict[str, Any]:
    return {
        "id": p.id,
        "module_name": p.module_name,
        "version": p.version,
        "current_phase": p.current_phase,
        "status": p.status,
        "strategy": p.strategy,
        "pilot_lead": p.pilot_lead,
        "description": p.description,
    }


def _facility_to_dict(f: PilotFacility) -> dict[str, Any]:
    return {
        "id": f.id,
        "pilot_id": f.pilot_id,
        "facility_id": f.facility_id,
        "facility_name": f.facility_name,
        "readiness_level": f.readiness_level,
        "readiness_score": f.readiness_score,
    }


def _readiness_to_dict(r: ReadinessChecklist) -> dict[str, Any]:
    return {
        "id": r.id,
        "pilot_id": r.pilot_id,
        "facility_id": r.facility_id,
        "overall_score": r.overall_score,
        "level": r.level,
        "assessed_by": r.assessed_by,
    }


def _gate_to_dict(g: GoNoGoGate) -> dict[str, Any]:
    return {
        "id": g.id,
        "pilot_id": g.pilot_id,
        "facility_id": g.facility_id,
        "gate_name": g.gate_name,
        "result": g.result,
        "approver": g.approver,
        "comments": g.comments,
    }


def _deployment_to_dict(d: DeploymentRecord) -> dict[str, Any]:
    return {
        "id": d.id,
        "pilot_id": d.pilot_id,
        "module": d.module,
        "version": d.version,
        "facility_id": d.facility_id,
        "strategy": d.strategy,
        "status": d.status,
        "health_check_passed": d.health_check_passed,
    }
