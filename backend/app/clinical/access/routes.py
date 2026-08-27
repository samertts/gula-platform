from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.orm import Session

from app.clinical.appointments.routes import (
    _actor_rate_limit,
    _correlation_id,
    _handle_error,
    _require_idempotency_key,
    _require_if_match,
)
from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync
from app.identity.services.canonical_audit import AuditEventInput, SyncCanonicalAuditService

from .schemas import GrantAccessRequest, RevokeAccessRequest
from .service import AccessExpiredError, AccessNotGrantedError, AccessRevokedError, AccessService

router = APIRouter(tags=["Clinical Access"])


def _run(request: Request, actor: NiamActor, db: Session, operation: str, target_type: str, target_id: str | None, workspace_id: str, callback):
    _actor_rate_limit(request, actor)
    try:
        result = callback()
        db.commit()
        return result
    except Exception as exc:
        if isinstance(exc, (AccessNotGrantedError, AccessExpiredError, AccessRevokedError)):
            db.rollback()
            scope = AccessService(db).authz.resolve_scope(actor, workspace_id)
            SyncCanonicalAuditService(db).record(AuditEventInput(event_type="ACCESS_DENIED", category="clinical_access", action=operation, actor_id=actor.account.id, actor_identity_id=actor.account.identity_id, actor_type="account", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, target_type=target_type, target_id=target_id, decision="deny", reason_code=getattr(exc, "code", "ACCESS_DENIED"), request_id=getattr(request.state, "request_id", None), correlation_id=_correlation_id(request), session_id=actor.session.uuid, source="api", data_classification="INTERNAL", outcome="denied"))
            db.commit()
        _handle_error(exc, db=db, actor=actor, request=request, operation=operation, target_type=target_type, target_id=target_id, workspace_id=workspace_id)


@router.post("/api/v1/clinical/access/grants", status_code=201)
def grant_access(body: GrantAccessRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "access.grant", "access_grant", None, body.workspace_id, lambda: AccessService(db).grant(actor, workspace_id=body.workspace_id, resource_type=body.resource_type, resource_id=body.resource_id, grantee_account_id=body.grantee_account_id, purpose=body.purpose, scope_payload=body.scope, duration_hours=body.duration_hours, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/clinical/access/grants/{grant_id}/revoke")
def revoke_access(grant_id: str, body: RevokeAccessRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "access.revoke", "access_grant", grant_id, body.workspace_id, lambda: AccessService(db).revoke(actor, grant_id=grant_id, workspace_id=body.workspace_id, expected_version=expected, reason=body.reason, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.get("/api/v1/clinical/access/results/{result_id}")
def read_shared_result(result_id: str, request: Request, workspace_id: str = Query(..., min_length=1, max_length=26), actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, "access.read", "lab_result", result_id, workspace_id, lambda: AccessService(db).read_result(actor, result_id=result_id, workspace_id=workspace_id, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.get("/api/v1/clinical/access/grants")
def list_grants(request: Request, workspace_id: str = Query(..., min_length=1, max_length=26), limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0, le=1_000_000), actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, "access.grants.list", "access_grant", None, workspace_id, lambda: AccessService(db).list_grants(actor, workspace_id=workspace_id, limit=limit, offset=offset, correlation_id=_correlation_id(request)))


@router.get("/api/v1/clinical/access/history")
def access_history(request: Request, workspace_id: str = Query(..., min_length=1, max_length=26), provider_account_id: str | None = Query(default=None, max_length=26), resource_type: str | None = Query(default=None, max_length=40), purpose: str | None = Query(default=None, max_length=40), action: str | None = Query(default=None, max_length=48), limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0, le=1_000_000), actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, "access.history", "access_history", None, workspace_id, lambda: AccessService(db).history(actor, workspace_id=workspace_id, provider_account_id=provider_account_id, resource_type=resource_type, purpose=purpose, action=action, limit=limit, offset=offset, correlation_id=_correlation_id(request)))
