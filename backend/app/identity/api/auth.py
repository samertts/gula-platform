from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.models.audit import AuditAction
from app.identity.services.audit_service import AuditService
from app.identity.services.authentication_service import AuthenticationService
from app.security.rate_limit import rate_limit_auth

from .ownership import record_authorization_denial
from .workspaces import NiamActor, get_current_niam_actor

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
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    service = AuthenticationService(db)
    session = await service.session_repo.get_by_uuid(session_uuid)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.account_id != actor.account.id:
        await record_authorization_denial(
            db,
            actor,
            target_type="session",
            target_id=session_uuid,
            reason="logout_session_scope_mismatch",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this session is not permitted",
        )

    terminated = await service.logout(
        session_uuid,
        actor_account_id=actor.account.id,
    )
    if not terminated:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session could not be terminated")
    await AuditService(db).record(
        AuditAction.logout,
        actor_id=actor.account.id,
        actor_type="account",
        target_type="session",
        target_id=session.uuid,
        session_id=actor.session.uuid,
    )
    return {"success": True}
