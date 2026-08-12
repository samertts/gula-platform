from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.models.citizen_relationship import CitizenRelationship
from app.identity.services.citizen_relationship_service import (
    REVOCATION_REASON_CODES,
    CitizenRelationshipConflict,
    CitizenRelationshipNotFound,
    CitizenRelationshipUnsupported,
    CitizenRelationshipWorkflow,
    _serialize,
)
from app.models.lab_user import LabUser
from app.security.dependencies import require_permission

router = APIRouter(prefix="/admin/citizen-relationships", tags=["citizen-relationships-admin"])

_ALLOWED_ACTOR_ROLES = frozenset({"master_admin", "ministry_admin"})


class CreateCitizenRelationshipRequest(BaseModel):
    source_kind: Literal["legacy_user"] = "legacy_user"
    legacy_user_id: int = Field(gt=0)
    citizen_id: str = Field(min_length=16, max_length=26)
    patient_id: str | None = Field(default=None, min_length=16, max_length=26)
    relationship_type: Literal["self"] = "self"
    purpose: Literal["citizen_workspace"] = "citizen_workspace"
    scope: dict[str, list[str]]


class ActivateCitizenRelationshipRequest(BaseModel):
    verification_reference: str = Field(min_length=8, max_length=255)


class RevokeCitizenRelationshipRequest(BaseModel):
    reason: Literal[
        "user_request",
        "verification_failed",
        "policy_change",
        "duplicate",
        "security_event",
        "administrative_correction",
    ]


def _relationship_admin(actor: LabUser = Depends(require_permission("platform:manage_users"))) -> LabUser:
    if actor.role not in _ALLOWED_ACTOR_ROLES:
        raise HTTPException(status_code=403, detail="Citizen relationship administration requires ministry authorization")
    return actor


def _workflow_error(exc: Exception) -> HTTPException:
    if isinstance(exc, CitizenRelationshipNotFound):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, CitizenRelationshipUnsupported):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, CitizenRelationshipConflict):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=500, detail="Citizen relationship workflow failed")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_pending_relationship(
    body: CreateCitizenRelationshipRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    actor: LabUser = Depends(_relationship_admin),
    db: Session = Depends(get_db),
):
    try:
        relationship = CitizenRelationshipWorkflow(
            db, actor, request_ip=request.client.host if request.client else None,
        ).create_pending(
            source_kind=body.source_kind,
            legacy_user_id=body.legacy_user_id,
            citizen_id=body.citizen_id,
            patient_id=body.patient_id,
            relationship_type=body.relationship_type,
            purpose=body.purpose,
            scope=body.scope,
            idempotency_key=idempotency_key,
        )
        return {"relationship": _serialize(relationship)}
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Relationship request conflicts with an existing record") from exc
    except Exception as exc:
        db.rollback()
        raise _workflow_error(exc) from exc


@router.get("")
def list_relationships(
    status_filter: str | None = Query(default=None, alias="status"),
    legacy_user_id: int | None = Query(default=None, gt=0),
    citizen_id: str | None = Query(default=None, min_length=16, max_length=26),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    actor: LabUser = Depends(_relationship_admin),
    db: Session = Depends(get_db),
):
    query = db.query(CitizenRelationship)
    if status_filter:
        query = query.filter(CitizenRelationship.status == status_filter)
    if legacy_user_id is not None:
        query = query.filter(CitizenRelationship.legacy_user_id == legacy_user_id)
    if citizen_id is not None:
        query = query.filter(CitizenRelationship.citizen_id == citizen_id)
    relationships = (
        query.order_by(CitizenRelationship.created_at.desc()).offset(skip).limit(limit).all()
    )
    return {"relationships": [_serialize(item) for item in relationships], "count": len(relationships)}


@router.post("/{relationship_id}/activate")
def activate_relationship(
    relationship_id: str,
    body: ActivateCitizenRelationshipRequest,
    request: Request,
    actor: LabUser = Depends(_relationship_admin),
    db: Session = Depends(get_db),
):
    try:
        relationship = CitizenRelationshipWorkflow(
            db, actor, request_ip=request.client.host if request.client else None,
        ).activate(relationship_id, verification_reference=body.verification_reference)
        return {"relationship": _serialize(relationship)}
    except Exception as exc:
        db.rollback()
        raise _workflow_error(exc) from exc


@router.post("/{relationship_id}/revoke")
def revoke_relationship(
    relationship_id: str,
    body: RevokeCitizenRelationshipRequest,
    request: Request,
    actor: LabUser = Depends(_relationship_admin),
    db: Session = Depends(get_db),
):
    try:
        relationship = CitizenRelationshipWorkflow(
            db, actor, request_ip=request.client.host if request.client else None,
        ).revoke(relationship_id, reason=body.reason)
        return {"relationship": _serialize(relationship), "reason_codes": sorted(REVOCATION_REASON_CODES)}
    except Exception as exc:
        db.rollback()
        raise _workflow_error(exc) from exc
