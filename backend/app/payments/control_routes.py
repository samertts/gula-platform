from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.exceptions import NotFoundError
from app.security.dependencies import require_permission

from .control_schemas import (
    FinancialControlListResponse,
    FinancialControlReject,
    FinancialControlSummaryResponse,
    FinancialControlRequestCreate,
    FinancialControlResponse,
)
from .control_service import FinancialControlService
from .models import FinancialControlRequest
from .service import PaymentService

router = APIRouter(prefix="/payments/controls", tags=["GULA Financial Controls"])
DbSession = Annotated[Session, Depends(get_db)]


def _commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _request_or_404(db: Session, request_id: str) -> FinancialControlRequest:
    request = db.query(FinancialControlRequest).filter(FinancialControlRequest.id == request_id).first()
    if request is None:
        raise NotFoundError("Financial control request not found")
    return request


def _response(request: FinancialControlRequest) -> FinancialControlResponse:
    metadata = request.safe_metadata or {}
    return FinancialControlResponse(
        id=request.id,
        institution_id=request.institution_id,
        control_type=request.control_type,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        requested_action=request.requested_action,
        status=request.status,
        idempotency_key=request.idempotency_key,
        reason=request.reason,
        rejection_reason=request.rejection_reason,
        requested_by=request.requested_by,
        approved_by=request.approved_by,
        applied_by=request.applied_by,
        request_id=request.request_id,
        evidence_hash=request.evidence_hash,
        external_operation=bool(metadata.get("external_operation", False)),
        requested_at=request.requested_at,
        approved_at=request.approved_at,
        applied_at=request.applied_at,
        expires_at=request.expires_at,
    )


def _assert_access(db: Session, current_user, institution_id: int) -> None:
    PaymentService(db).assert_institution_access(current_user, institution_id)


@router.post("/requests", response_model=FinancialControlResponse, status_code=status.HTTP_201_CREATED)
def create_control_request(
    payload: FinancialControlRequestCreate,
    db: DbSession,
    response: Response,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    request_id: Annotated[str | None, Header(alias="X-Request-ID")] = None,
    current_user=Depends(require_permission("payments:control:request")),
):
    _assert_access(db, current_user, payload.institution_id)
    request = FinancialControlService(db).create_request(
        institution_id=payload.institution_id,
        control_type=payload.control_type,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        requested_action=payload.requested_action,
        idempotency_key=idempotency_key or "",
        reason=payload.reason,
        requested_by=current_user.id,
        request_id=request_id,
        expires_at=payload.expires_at,
    )
    _commit(db)
    response.headers["Idempotency-Key"] = idempotency_key or ""
    return _response(request)


@router.get("/summary", response_model=FinancialControlSummaryResponse)
def financial_control_summary(
    db: DbSession,
    institution_id: int,
    current_user=Depends(require_permission("payments:control:read")),
):
    _assert_access(db, current_user, institution_id)
    return FinancialControlSummaryResponse(**FinancialControlService(db).summary(institution_id=institution_id))


@router.get("/requests", response_model=FinancialControlListResponse)
def list_control_requests(
    db: DbSession,
    institution_id: int,
    status_filter: str | None = None,
    current_user=Depends(require_permission("payments:control:read")),
):
    _assert_access(db, current_user, institution_id)
    items = FinancialControlService(db).list_requests(institution_id=institution_id, status=status_filter)
    return FinancialControlListResponse(items=[_response(item) for item in items], count=len(items))


@router.post("/requests/{request_id}/approve", response_model=FinancialControlResponse)
def approve_control_request(
    request_id: str,
    db: DbSession,
    current_user=Depends(require_permission("payments:control:approve")),
):
    request = _request_or_404(db, request_id)
    _assert_access(db, current_user, request.institution_id)
    request = FinancialControlService(db).approve(
        request_id=request_id,
        institution_id=request.institution_id,
        actor_user_id=current_user.id,
    )
    _commit(db)
    return _response(request)


@router.post("/requests/{request_id}/reject", response_model=FinancialControlResponse)
def reject_control_request(
    request_id: str,
    payload: FinancialControlReject,
    db: DbSession,
    current_user=Depends(require_permission("payments:control:approve")),
):
    request = _request_or_404(db, request_id)
    _assert_access(db, current_user, request.institution_id)
    request = FinancialControlService(db).reject(
        request_id=request_id,
        institution_id=request.institution_id,
        actor_user_id=current_user.id,
        rejection_reason=payload.rejection_reason,
    )
    _commit(db)
    return _response(request)


@router.post("/requests/{request_id}/apply", response_model=FinancialControlResponse)
def apply_control_request(
    request_id: str,
    db: DbSession,
    current_user=Depends(require_permission("payments:control:apply")),
):
    request = _request_or_404(db, request_id)
    _assert_access(db, current_user, request.institution_id)
    request = FinancialControlService(db).apply(
        request_id=request_id,
        institution_id=request.institution_id,
        actor_user_id=current_user.id,
    )
    _commit(db)
    return _response(request)
