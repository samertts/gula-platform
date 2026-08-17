from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.clinical_gateway.context import ClinicalGatewayBlocked, ClinicalGatewayContextResolver
from app.clinical_gateway.contracts import (
    ClinicalGatewayError,
    ClinicalGatewayErrorCode,
    ClinicalGatewayErrorEnvelope,
    ClinicalPageRequest,
    ClinicalReadEnvelope,
    OrderRead,
    PatientRead,
    ResultRead,
)
from app.clinical_gateway.rollout import ClinicalGatewayRollout
from app.clinical_gateway.service import ClinicalGatewayAuditFailure, ClinicalGatewayService
from app.clinical_gateway.session_facade import SyncSessionAsyncFacade
from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync
from app.identity.services.canonical_audit import AuditEventInput, CanonicalAuditService

router = APIRouter(prefix="/api/v1/clinical", tags=["Canonical Clinical Read Gateway"])


def _request_id(request: Request) -> UUID:
    value = getattr(request.state, "request_id", None)
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return uuid4()


def _correlation_id(request: Request, request_id: UUID) -> UUID:
    value = getattr(request.state, "correlation_id", None)
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return request_id


def _error_envelope(code: ClinicalGatewayErrorCode, message: str, request_id: UUID, correlation_id: UUID) -> ClinicalGatewayErrorEnvelope:
    return ClinicalGatewayErrorEnvelope(
        error=ClinicalGatewayError(
            code=code,
            message=message,
            request_id=request_id,
            correlation_id=correlation_id,
        ),
    )


def _status_for_block(reason_code: str) -> int:
    if reason_code == "invalid_cursor":
        return status.HTTP_422_UNPROCESSABLE_ENTITY
    if reason_code in {"service_unavailable", "rollout_off"}:
        return status.HTTP_503_SERVICE_UNAVAILABLE
    return status.HTTP_403_FORBIDDEN


def _audit_block(
    *,
    db: Session,
    actor: NiamActor,
    resource: str,
    request_id: UUID,
    correlation_id: UUID,
    reason_code: str,
) -> None:
    audit = CanonicalAuditService(SyncSessionAsyncFacade(db))
    import asyncio

    asyncio.run(
        audit.record(
            AuditEventInput(
                event_type="clinical_gateway_access",
                category="clinical_access",
                action=f"{resource}.read",
                actor_id=actor.account.id,
                actor_identity_id=actor.account.identity_id,
                target_type=f"clinical_{resource[:-1] if resource.endswith('s') else resource}",
                decision="deny",
                reason_code=reason_code,
                request_id=str(request_id),
                correlation_id=str(correlation_id),
                session_id=actor.session.id,
                source="clinical_gateway",
                data_classification="CLINICAL_SENSITIVE",
                outcome="denied",
            ),
        ),
    )


def _raise_safe(
    *,
    db: Session,
    actor: NiamActor,
    resource: str,
    request_id: UUID,
    correlation_id: UUID,
    reason_code: str,
    http_status: int | None = None,
) -> None:
    try:
        _audit_block(
            db=db,
            actor=actor,
            resource=resource,
            request_id=request_id,
            correlation_id=correlation_id,
            reason_code=reason_code,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_error_envelope(
                ClinicalGatewayErrorCode.unavailable,
                "Clinical read gateway is unavailable.",
                request_id,
                correlation_id,
            ).model_dump(mode="json"),
        ) from None
    raise HTTPException(
        status_code=http_status or _status_for_block(reason_code),
        detail=_error_envelope(
            ClinicalGatewayErrorCode.unauthorized if (http_status or _status_for_block(reason_code)) == 403 else ClinicalGatewayErrorCode.invalid_request,
            "Clinical read is not available for this context.",
            request_id,
            correlation_id,
        ).model_dump(mode="json"),
    )


def _prepare(
    *,
    db: Session,
    actor: NiamActor,
    resource: str,
    request: Request,
) -> tuple[ClinicalGatewayService, object, UUID, UUID]:
    request_id = _request_id(request)
    correlation_id = _correlation_id(request, request_id)
    rollout = ClinicalGatewayRollout()
    if rollout.mode.value == "OFF":
        _raise_safe(
            db=db,
            actor=actor,
            resource=resource,
            request_id=request_id,
            correlation_id=correlation_id,
            reason_code="rollout_off",
        )
    try:
        context = ClinicalGatewayContextResolver(db).resolve(actor)
    except ClinicalGatewayBlocked as exc:
        _raise_safe(
            db=db,
            actor=actor,
            resource=resource,
            request_id=request_id,
            correlation_id=correlation_id,
            reason_code=exc.reason_code,
        )
    if not rollout.allows(
        account_id=context.actor.account.id,
        organization_id=context.scope.niam_organization_id,
    ):
        _raise_safe(
            db=db,
            actor=actor,
            resource=resource,
            request_id=request_id,
            correlation_id=correlation_id,
            reason_code="rollout_not_selected",
        )
    return ClinicalGatewayService(db), context, request_id, correlation_id


@router.get(
    "/patients",
    response_model=ClinicalReadEnvelope[PatientRead],
    responses={401: {"model": ClinicalGatewayErrorEnvelope}, 403: {"model": ClinicalGatewayErrorEnvelope}, 422: {"model": ClinicalGatewayErrorEnvelope}, 503: {"model": ClinicalGatewayErrorEnvelope}},
)
def list_clinical_patients(
    request: Request,
    params: ClinicalPageRequest = Depends(),
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
):
    service, context, request_id, correlation_id = _prepare(db=db, actor=actor, resource="patients", request=request)
    try:
        response = service.list_patients(
            context=context,
            request_id=request_id,
            correlation_id=correlation_id,
            params=params,
        )
        db.commit()
        return response
    except ClinicalGatewayAuditFailure:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_error_envelope(ClinicalGatewayErrorCode.unavailable, "Clinical read gateway is unavailable.", request_id, correlation_id).model_dump(mode="json"),
        ) from None
    except ClinicalGatewayBlocked as exc:
        _raise_safe(db=db, actor=actor, resource="patients", request_id=request_id, correlation_id=correlation_id, reason_code=exc.reason_code)


@router.get(
    "/orders/{order_id}/results",
    response_model=ClinicalReadEnvelope[ResultRead],
    responses={401: {"model": ClinicalGatewayErrorEnvelope}, 403: {"model": ClinicalGatewayErrorEnvelope}, 404: {"model": ClinicalGatewayErrorEnvelope}, 503: {"model": ClinicalGatewayErrorEnvelope}},
)
def list_clinical_results(
    order_id: int,
    request: Request,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
):
    service, context, request_id, correlation_id = _prepare(db=db, actor=actor, resource="results", request=request)
    try:
        response = service.list_results(
            context=context,
            request_id=request_id,
            correlation_id=correlation_id,
            order_id=order_id,
        )
        db.commit()
        return response
    except ClinicalGatewayAuditFailure:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_error_envelope(ClinicalGatewayErrorCode.unavailable, "Clinical read gateway is unavailable.", request_id, correlation_id).model_dump(mode="json"),
        ) from None
    except ClinicalGatewayBlocked as exc:
        _raise_safe(db=db, actor=actor, resource="results", request_id=request_id, correlation_id=correlation_id, reason_code=exc.reason_code, http_status=status.HTTP_404_NOT_FOUND if exc.reason_code == "not_found" else None)


@router.get(
    "/orders",
    response_model=ClinicalReadEnvelope[OrderRead],
    responses={401: {"model": ClinicalGatewayErrorEnvelope}, 403: {"model": ClinicalGatewayErrorEnvelope}, 422: {"model": ClinicalGatewayErrorEnvelope}, 503: {"model": ClinicalGatewayErrorEnvelope}},
)
def list_clinical_orders(
    request: Request,
    params: ClinicalPageRequest = Depends(),
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
):
    service, context, request_id, correlation_id = _prepare(db=db, actor=actor, resource="orders", request=request)
    try:
        response = service.list_orders(
            context=context,
            request_id=request_id,
            correlation_id=correlation_id,
            params=params,
        )
        db.commit()
        return response
    except ClinicalGatewayAuditFailure:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_error_envelope(ClinicalGatewayErrorCode.unavailable, "Clinical read gateway is unavailable.", request_id, correlation_id).model_dump(mode="json"),
        ) from None
    except ClinicalGatewayBlocked as exc:
        _raise_safe(db=db, actor=actor, resource="orders", request_id=request_id, correlation_id=correlation_id, reason_code=exc.reason_code)
