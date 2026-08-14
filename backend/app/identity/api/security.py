from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.models.security import SecurityIncident
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecisionService,
    AuthorizationRequest,
)
from app.identity.services.incident_service import IncidentError, IncidentService

router = APIRouter(prefix="/security", tags=["NIAM Security"])


class IncidentCreateRequest(BaseModel):
    organization_id: str = Field(min_length=1, max_length=26)
    severity: str = Field(min_length=2, max_length=4)
    category: str = Field(min_length=1, max_length=80)
    affected_scope: dict[str, Any] = Field(default_factory=dict, max_length=20)


class IncidentTransitionRequest(BaseModel):
    status: str = Field(min_length=3, max_length=20)
    expected_version: int = Field(ge=1)
    resolution: str | None = Field(default=None, max_length=4000)
    containment_status: str | None = Field(default=None, max_length=120)


async def _require_security_permission(
    actor: NiamActor,
    db: AsyncSession,
    *,
    organization_id: str,
    permission_key: str,
) -> None:
    decision = await AuthorizationDecisionService(db).authorize(
        AuthorizationActor(account=actor.account, session=actor.session),
        AuthorizationRequest(
            subject_account_id=actor.account.id,
            action="read" if permission_key.endswith("read") else "manage",
            resource_type="security_incident",
            permission_key=permission_key,
            organization_id=organization_id,
            sensitivity="critical",
            resource_context={"exists": True, "organization_id": organization_id},
        ),
    )
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Security authorization denied")


def _serialize(incident: SecurityIncident) -> dict[str, Any]:
    return {
        "id": incident.id,
        "incident_key": incident.incident_key,
        "severity": incident.severity,
        "category": incident.category,
        "organization_id": incident.organization_id,
        "status": incident.status,
        "detected_at": incident.detected_at.isoformat(),
        "reported_at": incident.reported_at.isoformat() if incident.reported_at else None,
        "assigned_to": incident.assigned_to,
        "affected_scope": incident.affected_scope,
        "containment_status": incident.containment_status,
        "resolution": incident.resolution,
        "closed_at": incident.closed_at.isoformat() if incident.closed_at else None,
        "version": incident.version,
    }


@router.get("/incidents")
async def list_incidents(
    organization_id: str = Query(min_length=1, max_length=26),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    await _require_security_permission(actor, db, organization_id=organization_id, permission_key="security.incident.read")
    incidents = await IncidentService(db).list(organization_id=organization_id, limit=limit, offset=offset)
    return {"incidents": [_serialize(incident) for incident in incidents], "limit": limit, "offset": offset}


@router.post("/incidents", status_code=status.HTTP_201_CREATED)
async def create_incident(
    body: IncidentCreateRequest,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    await _require_security_permission(actor, db, organization_id=body.organization_id, permission_key="security.incident.manage")
    try:
        incident = await IncidentService(db).create(
            actor_id=actor.account.id,
            severity=body.severity,
            category=body.category,
            organization_id=body.organization_id,
            affected_scope=body.affected_scope,
        )
    except IncidentError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return _serialize(incident)


@router.patch("/incidents/{incident_id}")
async def transition_incident(
    incident_id: str,
    body: IncidentTransitionRequest,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    incident = await db.get(SecurityIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    if incident.organization_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incident scope unavailable")
    await _require_security_permission(actor, db, organization_id=incident.organization_id, permission_key="security.incident.manage")
    try:
        updated = await IncidentService(db).transition(
            actor_id=actor.account.id,
            incident_id=incident_id,
            target_status=body.status,
            expected_version=body.expected_version,
            resolution=body.resolution,
            containment_status=body.containment_status,
        )
    except IncidentError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _serialize(updated)


@router.get("/dashboard")
async def security_dashboard(
    organization_id: str = Query(min_length=1, max_length=26),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    await _require_security_permission(actor, db, organization_id=organization_id, permission_key="security.incident.read")
    result = await db.execute(
        select(SecurityIncident.status, SecurityIncident.severity, func.count(SecurityIncident.id))
        .where(SecurityIncident.organization_id == organization_id)
        .group_by(SecurityIncident.status, SecurityIncident.severity),
    )
    counts = [
        {"status": status_value, "severity": severity, "count": count}
        for status_value, severity, count in result.all()
    ]
    return {"organization_id": organization_id, "incident_counts": counts}
