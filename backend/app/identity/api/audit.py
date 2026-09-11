from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecisionService,
    AuthorizationRequest,
)
from app.identity.services.canonical_audit import AuditEventInput, CanonicalAuditService

router = APIRouter(prefix="/audit", tags=["NIAM Audit"])


def _serialize(entry: Any, *, sensitive: bool = False) -> dict[str, Any]:
    data = {
        "id": entry.id,
        "event_type": entry.event_type,
        "event_version": entry.event_version,
        "category": entry.category,
        "actor_id": entry.actor_id,
        "actor_type": entry.actor_type,
        "organization_id": entry.organization_id,
        "facility_id": entry.facility_id,
        "department_id": entry.department_id,
        "workspace_id": entry.workspace_id,
        "target_type": entry.target_type,
        "target_id": entry.target_id,
        "action": entry.action,
        "decision": entry.decision,
        "reason_code": entry.reason_code,
        "request_id": entry.request_id,
        "correlation_id": entry.correlation_id,
        "source": entry.source,
        "data_classification": entry.data_classification,
        "occurred_at": entry.occurred_at.isoformat(),
        "outcome": entry.outcome,
        "event_hash": entry.entry_hash,
        "previous_hash": entry.previous_hash,
    }
    if sensitive:
        data["changes"] = entry.changes
        data["metadata"] = entry.extra_data
        data["context"] = entry.context
    return data


def _require_audit_permission(
    actor: NiamActor,
    db: Session,
    *,
    organization_id: str,
    permission_key: str,
) -> None:
    decision = AuthorizationDecisionService(db).authorize(
        AuthorizationActor(account=actor.account, session=actor.session),
        AuthorizationRequest(
            subject_account_id=actor.account.id,
            action="read" if permission_key == "audit.read" else "verify",
            resource_type="audit",
            permission_key=permission_key,
            organization_id=organization_id,
            sensitivity="critical",
            resource_context={"exists": True, "organization_id": organization_id},
        ),
    )
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Audit authorization denied")


@router.get("")
def search_audit_events(
    organization_id: str = Query(min_length=1, max_length=26),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    actor_id: str | None = Query(default=None, max_length=26),
    event_type: str | None = Query(default=None, max_length=120),
    resource_type: str | None = Query(default=None, max_length=50),
    decision: str | None = Query(default=None, max_length=20),
    facility_id: str | None = Query(default=None, max_length=26),
    workspace_id: str | None = Query(default=None, max_length=26),
    occurred_from: datetime | None = None,
    occurred_to: datetime | None = None,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    _require_audit_permission(actor, db, organization_id=organization_id, permission_key="audit.read")
    entries = CanonicalAuditService(db).search(
        organization_id=organization_id,
        limit=limit,
        offset=offset,
        actor_id=actor_id,
        event_type=event_type,
        resource_type=resource_type,
        decision=decision,
        facility_id=facility_id,
        workspace_id=workspace_id,
        occurred_from=occurred_from,
        occurred_to=occurred_to,
    )
    return {"events": [_serialize(entry) for entry in entries], "limit": limit, "offset": offset}


@router.get("/export")
def export_audit_events(
    request: Request,
    organization_id: str = Query(min_length=1, max_length=26),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    event_type: str | None = Query(default=None, max_length=120),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    _require_audit_permission(actor, db, organization_id=organization_id, permission_key="audit.export")
    entries = CanonicalAuditService(db).search(
        organization_id=organization_id,
        limit=limit,
        offset=offset,
        event_type=event_type,
    )
    CanonicalAuditService(db).record(
        AuditEventInput(
            event_type="DATA_EXPORT_REQUESTED",
            category="DATA_EXPORT",
            action="audit.export",
            actor_id=actor.account.id,
            actor_identity_id=actor.account.identity_id,
            actor_type="human",
            organization_id=organization_id,
            target_type="audit_export",
            decision="ALLOW",
            reason_code="EXPLICIT_EXPORT_PERMISSION",
            request_id=getattr(request.state, "request_id", None),
            session_id=actor.session.uuid,
            source="api",
            data_classification="SENSITIVE",
            metadata={"limit": limit, "offset": offset, "event_type": event_type},
        ),
    )
    return {"events": [_serialize(entry) for entry in entries], "expires_at": None, "permanent_url": False}


@router.get("/integrity")
def verify_audit_integrity(
    organization_id: str = Query(min_length=1, max_length=26),
    occurred_from: datetime | None = None,
    occurred_to: datetime | None = None,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    _require_audit_permission(actor, db, organization_id=organization_id, permission_key="audit.verify_integrity")
    return CanonicalAuditService(db).verify(
        organization_id=organization_id,
        occurred_from=occurred_from,
        occurred_to=occurred_to,
    )
