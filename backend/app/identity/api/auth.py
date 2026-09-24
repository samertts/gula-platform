from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

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
def login(
    body: LoginRequest,
    request: Request,
    ip_address: str | None = None,
    user_agent: str | None = None,
    db: Session = Depends(get_db),
):
    rate_limit_auth(request, identifier=body.login)
    service = AuthenticationService(db)
    result = service.login(
        login=body.login,
        password=body.password,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return result


@router.post("/refresh")
def refresh(
    refresh_token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    rate_limit_auth(request, max_per_minute=20)
    service = AuthenticationService(db)
    result = service.refresh_session(refresh_token)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    return result


@router.post("/logout")
def logout(
    session_uuid: str,
    db: Session = Depends(get_db),
):
    service = AuthenticationService(db)
    service.logout(session_uuid)
    return {"success": True}
