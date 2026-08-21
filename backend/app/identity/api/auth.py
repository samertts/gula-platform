
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.clinical_gateway.session_facade import SyncSessionAsyncFacade
from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync
from app.identity.services.authentication_service import AuthenticationService
from app.security.rate_limit import get_client_ip, rate_limit_auth

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
    db: Session = Depends(get_db),
):
    rate_limit_auth(request, identifier=body.login)
    # Keep legacy optional query parameters for API compatibility, but never
    # trust caller-supplied session metadata. Persist only request-derived data.
    server_ip_address = get_client_ip(request)
    server_user_agent = request.headers.get("user-agent")
    service = AuthenticationService(SyncSessionAsyncFacade(db))
    result = await service.login(
        login=body.login,
        password=body.password,
        ip_address=server_ip_address,
        user_agent=server_user_agent,
    )
    if not result:
        # AccountService flushes failed-attempt/lockout state before returning
        # None; commit it before raising so the request dependency cannot roll
        # the security control back.
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    db.commit()
    return result


@router.post("/refresh")
async def refresh(
    refresh_token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    rate_limit_auth(request, max_per_minute=20)
    service = AuthenticationService(SyncSessionAsyncFacade(db))
    result = await service.refresh_session(refresh_token)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    db.commit()
    return result


@router.post("/logout")
async def logout(
    session_uuid: str,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
):
    service = AuthenticationService(SyncSessionAsyncFacade(db))
    terminated = await service.logout(session_uuid, account_id=str(actor.account.id))
    if not terminated:
        raise HTTPException(status_code=403, detail="Session does not belong to the authenticated account")
    db.commit()
    return {"success": True}
