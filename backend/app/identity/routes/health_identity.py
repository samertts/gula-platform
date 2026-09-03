from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.clinical.appointments.routes import (
    _actor_rate_limit,
    _correlation_id,
    _handle_error,
    _require_idempotency_key,
)
from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync
from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.orm import Session

from ..schemas.health_identity import (
    ConsentGrantRequest,
    ConsentRevokeRequest,
    DeviceRegisterRequest,
    DeviceTrustRequest,
    HealthIdIssueRequest,
    RecoveryCompleteRequest,
    RecoveryRequest,
    VerificationCompleteRequest,
    VerificationRequest,
)
from ..services.health_identity_service import CanonicalHealthIdentityService

router = APIRouter(tags=["NIAM Health Identity"])


def _run(request: Request, actor: NiamActor, db: Session, operation: str, target_type: str, target_id: str | None, callback: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    _actor_rate_limit(request, actor)
    try:
        result = callback()
        db.commit()
        return result
    except Exception as exc:
        _handle_error(exc, db=db, actor=actor, request=request, operation=operation, target_type=target_type, target_id=target_id, workspace_id=None)
        raise AssertionError("unreachable") from exc


@router.get("/api/v1/identity/health/status")
def health_status(request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, "identity.health.status", "citizen_lifecycle", None, lambda: CanonicalHealthIdentityService(db).health_status(actor, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/identity/health/verifications", status_code=status.HTTP_201_CREATED)
def request_verification(body: VerificationRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "identity.verification.request", "health_identity_operation", None, lambda: CanonicalHealthIdentityService(db).request_verification(actor, method=body.method, purpose=body.purpose, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/identity/health/verifications/complete")
def complete_verification(body: VerificationCompleteRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "identity.verification.complete", "health_identity_operation", body.operation_id, lambda: CanonicalHealthIdentityService(db).complete_verification(actor, operation_id=body.operation_id, proof=body.proof, verified_attributes=body.verified_attributes, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/identity/health/issue")
def issue_health_id(body: HealthIdIssueRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "identity.health_id.issue", "citizen_lifecycle", None, lambda: CanonicalHealthIdentityService(db).issue_health_id(actor, verification_operation_id=body.verification_operation_id, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/identity/devices", status_code=status.HTTP_201_CREATED)
def register_device(body: DeviceRegisterRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "identity.device.register", "niam_device", None, lambda: CanonicalHealthIdentityService(db).register_device(actor, device_fingerprint=body.device_fingerprint, device_name=body.device_name, device_type=body.device_type, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/identity/devices/trust")
def trust_device(body: DeviceTrustRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "identity.device.trust", "niam_device", body.device_id, lambda: CanonicalHealthIdentityService(db).trust_device(actor, device_id=body.device_id, verification_operation_id=body.verification_operation_id, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/identity/consents", status_code=status.HTTP_201_CREATED)
def grant_consent(body: ConsentGrantRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "identity.consent.grant", "niam_consent", None, lambda: CanonicalHealthIdentityService(db).grant_consent(actor, grantee_account_id=body.grantee_account_id, purpose=body.purpose, resource_domain=body.resource_domain, scope=body.scope, expires_at=body.expires_at, reason=body.reason, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/identity/consents/revoke")
def revoke_consent(body: ConsentRevokeRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "identity.consent.revoke", "niam_consent", body.consent_id, lambda: CanonicalHealthIdentityService(db).revoke_consent(actor, consent_id=body.consent_id, reason=body.reason, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/identity/recovery", status_code=status.HTTP_201_CREATED)
def request_recovery(body: RecoveryRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "identity.recovery.request", "health_identity_operation", None, lambda: CanonicalHealthIdentityService(db).request_recovery(actor, purpose=body.purpose, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/identity/recovery/complete")
def complete_recovery(body: RecoveryCompleteRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "identity.recovery.complete", "health_identity_operation", body.operation_id, lambda: CanonicalHealthIdentityService(db).complete_recovery(actor, operation_id=body.operation_id, proof=body.proof, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))
