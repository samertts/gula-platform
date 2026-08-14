from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.clinical_gateway.session_facade import SyncSessionAsyncFacade
from app.database import get_db
from app.identity.services.account_request_service import (
    AccountRequestConfigurationError,
    AccountRequestService,
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
