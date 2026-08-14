
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.services.authentication_service import AuthenticationService
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
    rate_limit_auth(request)
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
