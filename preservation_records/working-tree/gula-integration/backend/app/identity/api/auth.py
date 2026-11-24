
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import load_niam_step_up_freshness_seconds
from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.services.authentication_service import AuthenticationService
from app.identity.services.step_up_service import (
    StepUpConfigurationError,
    StepUpDenied,
    StepUpService,
)
from app.security.rate_limit import rate_limit_auth

router = APIRouter(prefix="/auth", tags=["NIAM Auth"])


class LoginRequest(BaseModel):
    login: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    session_uuid: str
    account_uuid: str


@router.post("/login")
async def login(
    body: LoginRequest,
    request: Request,
    ip_address: str | None = None,
    user_agent: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    rate_limit_auth(request, identifier=body.login)
    service = AuthenticationService(db)
    result = await service.login(
        login=body.login,
        password=body.password,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return result


@router.post("/refresh")
async def refresh(
    refresh_token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    rate_limit_auth(request, max_per_minute=20)
    service = AuthenticationService(db)
    result = await service.refresh_session(refresh_token)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    return result


@router.post("/logout")
async def logout(
    session_uuid: str,
    db: AsyncSession = Depends(get_db),
):
    service = AuthenticationService(db)
    await service.logout(session_uuid)
    return {"success": True}


class StepUpVerifyRequest(BaseModel):
    """Only the factor code is accepted — no account, session or timestamp."""

    code: str
    method: str = "totp"


class StepUpVerifyResponse(BaseModel):
    verified: bool
    event_id: str
    mfa_method: str
    verified_at: str
    freshness_seconds: int


@router.post("/step-up/verify")
async def verify_step_up(
    body: StepUpVerifyRequest,
    request: Request,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    """Stage a fresh step-up signal using the caller's OWN NIAM MFA factor.

    The authenticated principal is resolved server-side; the request body
    carries no account identifier, so cross-account MFA completion is
    structurally impossible on this endpoint.
    """
    rate_limit_auth(request, identifier=f"niam-stepup:{actor.account.id}")
    try:
        event = await StepUpService(db).verify(actor, body.code, body.method)
        freshness = load_niam_step_up_freshness_seconds()
    except StepUpConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Step-up authentication unavailable") from exc
    except StepUpDenied as exc:
        raise HTTPException(status_code=401, detail=f"Step-up verification failed: {exc}") from exc
    return StepUpVerifyResponse(
        verified=True,
        event_id=event.event_id,
        mfa_method=event.mfa_method,
        verified_at=event.verified_at.isoformat(),
        freshness_seconds=freshness,
    )
