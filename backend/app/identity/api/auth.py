from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import REFRESH_TOKEN_EXPIRE_DAYS, USE_SECURE_COOKIES
from app.database_async import get_async_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.services.authentication_service import AuthenticationService
from app.security.csrf import clear_csrf_cookie, issue_csrf_cookie
from app.security.rate_limit import get_client_ip, rate_limit_auth

router = APIRouter(prefix="/auth", tags=["NIAM Auth"])


class LoginRequest(BaseModel):
    login: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    session_uuid: str
    account_uuid: str
    refresh_family_id: str | None = None
    account: dict[str, object] | None = None


def _cookie_kwargs() -> dict[str, object]:
    return {
        "httponly": True,
        "secure": USE_SECURE_COOKIES,
        "samesite": "strict",
        "path": "/",
    }


def _set_auth_cookies(response: Response, result: dict) -> None:
    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        max_age=int(result["expires_in"]),
        **_cookie_kwargs(),
    )
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        **_cookie_kwargs(),
    )
    issue_csrf_cookie(response)


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    clear_csrf_cookie(response)


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db),
):
    rate_limit_auth(request, identifier=body.login)
    service = AuthenticationService(db)
    result = await service.login(
        login=body.login,
        password=body.password,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    _set_auth_cookies(response, result)
    return result


@router.post("/refresh", response_model=LoginResponse)
async def refresh(
    request: Request,
    response: Response,
    body: RefreshRequest | None = None,
    refresh_token: str | None = None,
    db: AsyncSession = Depends(get_async_db),
):
    rate_limit_auth(request, max_per_minute=20)
    raw_refresh = (body.refresh_token if body else None) or refresh_token or request.cookies.get("refresh_token")
    if not raw_refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token required")

    result = await AuthenticationService(db).refresh_session(raw_refresh)
    if not result:
        _clear_auth_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    _set_auth_cookies(response, result)
    return result


@router.post("/logout")
async def logout(
    response: Response,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_async_db),
):
    service = AuthenticationService(db)
    terminated = await service.logout(actor.session.uuid, account_id=str(actor.account.id))
    if not terminated:
        _clear_auth_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session is no longer active")
    await db.commit()
    _clear_auth_cookies(response)
    return {"success": True, "scope": "current_session"}


@router.post("/logout-all")
async def logout_all(
    response: Response,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_async_db),
):
    count = await AuthenticationService(db).logout_all_sessions(str(actor.account.id))
    await db.commit()
    _clear_auth_cookies(response)
    return {"success": True, "scope": "all_sessions", "terminated": count}
