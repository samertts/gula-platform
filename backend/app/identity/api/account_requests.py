from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clinical_gateway.session_facade import SyncSessionAsyncFacade
from app.database import get_db
from app.identity.api.account_management import (
    get_governance_organization_id,
    require_governance_management,
)
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync
from app.identity.models.account_request import AccountCreationRequest, AccountRequestStatus
from app.identity.services.account_request_service import (
    AccountRequestConfigurationError,
    AccountRequestConflict,
    AccountRequestService,
    AccountRequestStateError,
    VerificationProviderUnavailable,
)
from app.security.rate_limit import rate_limit_auth

router = APIRouter(prefix="/account-requests", tags=["NIAM Account Requests"])


class AccountRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=30)
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    requested_account_type: str = Field(default="human", max_length=20)

    @field_validator("email", "phone", "display_name", mode="before")
    @classmethod
    def reject_control_characters(cls, value: Any) -> Any:
        if isinstance(value, str) and any(ord(char) < 32 for char in value if char not in "\t\n\r"):
            raise ValueError("control characters are not allowed")
        return value


class AccountRequestAccepted(BaseModel):
    accepted: bool
    status: str
    request_id: str | None
    message: str


@router.post(
    "/",
    response_model=AccountRequestAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_account_request(
    body: AccountRequestCreate,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=16, max_length=200),
    db: Session = Depends(get_db),
) -> AccountRequestAccepted:
    """Receive a review request only; this route never creates or activates an account."""
    rate_limit_auth(request, max_per_minute=5)
    try:
        result = await AccountRequestService(SyncSessionAsyncFacade(db)).submit(
            email=body.email,
            phone=body.phone,
            display_name=body.display_name,
            requested_account_type=body.requested_account_type,
            idempotency_key=idempotency_key,
            source_ip=request.client.host if request.client else None,
            request_id=str(getattr(request.state, "request_id", "")) or None,
            user_agent=request.headers.get("user-agent"),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except AccountRequestConfigurationError:
        # Fail closed without exposing key names or configuration details.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account request intake is temporarily unavailable.",
        ) from None
    return AccountRequestAccepted(**AccountRequestService.public_result(result))


class AccountRequestAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason_code: str = Field(default="manual_review", min_length=3, max_length=120)
    suspended_until: datetime | None = None

    @field_validator("suspended_until")
    @classmethod
    def validate_suspension_date(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("suspended_until must include timezone")
        return value


class AccountRequestVerificationConfirm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=6, max_length=6, pattern=r"^[0-9]{6}$")


class AccountActivationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=20, max_length=256)
    password: str = Field(min_length=12, max_length=128)


async def _load_request_or_404(request_uuid: str, db: Session):
    request = await AccountRequestService(SyncSessionAsyncFacade(db))._get_request(request_uuid)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account request not found")
    return request


@router.get("/")
async def list_account_requests(
    request_status: str | None = None,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
):
    """List sanitized requests for an authorized governance reviewer only."""
    await require_governance_management(
        actor,
        db,
        action="review",
        resource_type="account_request",
        resource_exists=True,
    )
    service = AccountRequestService(SyncSessionAsyncFacade(db))
    statement = select(AccountCreationRequest).order_by(AccountCreationRequest.created_at.desc()).limit(100)
    if request_status:
        if request_status not in {item.value for item in AccountRequestStatus}:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid request status")
        statement = statement.where(AccountCreationRequest.status == request_status)
    result = await service.session.execute(statement)
    return {"requests": [service.serialize_request(item) for item in result.scalars().all()]}


@router.post("/{request_uuid}/review")
async def review_account_request(
    request_uuid: str,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
):
    await require_governance_management(
        actor,
        db,
        action="review",
        resource_type="account_request",
        resource_id=request_uuid,
    )
    try:
        request = await AccountRequestService(SyncSessionAsyncFacade(db)).start_review(
            request_uuid,
            actor.account.id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account request not found") from exc
    except AccountRequestStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return AccountRequestService.serialize_request(request)


@router.post("/{request_uuid}/verification/start", status_code=status.HTTP_202_ACCEPTED)
async def start_account_request_verification(
    request_uuid: str,
    request: Request,
    db: Session = Depends(get_db),
):
    rate_limit_auth(request)
    service = AccountRequestService(SyncSessionAsyncFacade(db))
    try:
        account_request = await service.start_verification(
            request_uuid,
            request_id=str(getattr(request.state, "request_id", "")) or None,
        )
    except (LookupError, AccountRequestStateError, VerificationProviderUnavailable):
        # Do not disclose whether a request UUID exists or which provider/contact
        # is configured. The caller must rely on the generic response.
        return {"accepted": True, "status": "verification_pending", "message": "If the request is eligible, verification remains pending."}
    return {"accepted": True, "status": account_request.status, "message": "Verification is pending delivery."}


@router.post("/{request_uuid}/verification/confirm")
async def confirm_account_request_verification(
    request_uuid: str,
    body: AccountRequestVerificationConfirm,
    request: Request,
    db: Session = Depends(get_db),
):
    rate_limit_auth(request)
    try:
        account_request = await AccountRequestService(SyncSessionAsyncFacade(db)).confirm_verification(
            request_uuid,
            body.code,
            request_id=str(getattr(request.state, "request_id", "")) or None,
        )
    except (LookupError, AccountRequestStateError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification is invalid or expired") from exc
    return {"status": account_request.status, "message": "Verification completed."}


@router.post("/{request_uuid}/approve")
async def approve_account_request(
    request_uuid: str,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
):
    await require_governance_management(
        actor,
        db,
        action="approve",
        resource_type="account_request",
        resource_id=request_uuid,
    )
    try:
        account_request, account = await AccountRequestService(SyncSessionAsyncFacade(db)).approve(
            request_uuid,
            actor.account.id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account request not found") from exc
    except AccountRequestConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AccountRequestStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return {
        "request": AccountRequestService.serialize_request(account_request),
        "account": AccountRequestService.serialize_account(account),
    }


@router.post("/{request_uuid}/activation-token", status_code=status.HTTP_202_ACCEPTED)
async def issue_account_activation_token(
    request_uuid: str,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
):
    await require_governance_management(
        actor,
        db,
        action="activate",
        resource_type="account_request",
        resource_id=request_uuid,
    )
    try:
        await AccountRequestService(SyncSessionAsyncFacade(db)).issue_activation_token(
            request_uuid,
            actor.account.id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account request not found") from exc
    except (AccountRequestStateError, VerificationProviderUnavailable) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return {"accepted": True, "message": "Activation instructions were sent through the approved channel."}


@router.post("/{request_uuid}/activate")
async def activate_account_request(
    request_uuid: str,
    body: AccountActivationRequest,
    db: Session = Depends(get_db),
):
    try:
        account = await AccountRequestService(SyncSessionAsyncFacade(db)).activate(
            request_uuid,
            body.token,
            body.password,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found") from exc
    except AccountRequestStateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return AccountRequestService.serialize_account(account)


@router.post("/{request_uuid}/reject")
async def reject_account_request(
    request_uuid: str,
    body: AccountRequestAction,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
):
    await require_governance_management(
        actor,
        db,
        action="reject",
        resource_type="account_request",
        resource_id=request_uuid,
    )
    service = AccountRequestService(SyncSessionAsyncFacade(db))
    request = await _load_request_or_404(request_uuid, db)
    try:
        request.rejection_reason_encrypted = service._encrypt_optional_reason(body.reason_code)
        await service._transition_request(
            request,
            AccountRequestStatus.rejected,
            actor_id=actor.account.id,
            reason_code=body.reason_code,
        )
        await service.session.commit()
    except AccountRequestStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return service.serialize_request(request)


@router.post("/{request_uuid}/expire")
async def expire_account_request(
    request_uuid: str,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
):
    await require_governance_management(
        actor,
        db,
        action="expire",
        resource_type="account_request",
        resource_id=request_uuid,
    )
    try:
        request = await AccountRequestService(SyncSessionAsyncFacade(db)).expire(
            request_uuid,
            actor.account.id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account request not found") from exc
    except AccountRequestStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return AccountRequestService.serialize_request(request)


@router.post("/accounts/{account_uuid}/{action}")
async def mutate_account_lifecycle(
    account_uuid: str,
    action: str,
    body: AccountRequestAction,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
):
    allowed_actions = {"suspend", "lock", "reactivate", "deactivate"}
    if action not in allowed_actions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unsupported account action")
    await require_governance_management(
        actor,
        db,
        action=action,
        resource_type="account",
        resource_id=account_uuid,
    )
    try:
        account = await AccountRequestService(SyncSessionAsyncFacade(db)).mutate_account(
            account_uuid,
            actor_id=actor.account.id,
            action=action,
            reason_code=body.reason_code,
            governance_organization_id=get_governance_organization_id(),
            suspended_until=body.suspended_until,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found") from exc
    except AccountRequestStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return AccountRequestService.serialize_account(account)
