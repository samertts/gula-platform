from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab import Lab
from ..models.lab_user import LabUser
from ..models.user import User
from .auth import decode_token, is_token_blacklisted
from .rbac import get_permissions_for_role
from .session import get_perm_version

if TYPE_CHECKING:
    from ..models.service_account import ServiceAccount

logger = logging.getLogger("gula.security.auth")

security = HTTPBearer(auto_error=False)


def _extract_token(
    credentials: HTTPAuthorizationCredentials | None,
    request: Request,
) -> str | None:
    """Extract JWT from Bearer header (mobile) or httpOnly cookie (web)."""
    if credentials is not None:
        return credentials.credentials
    return request.cookies.get("access_token")


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> LabUser | User:
    raw_token = _extract_token(credentials, request)
    if raw_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_token(raw_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token",
        )

    # Reject revoked tokens (logout, forced expiry)
    jti = payload.get("jti")
    if jti and is_token_blacklisted(jti):
        logger.warning("Token revoked jti=%s user_id=%s", jti, payload.get("user_id"))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked",
        )

    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload",
        )

    user = db.query(LabUser).filter(LabUser.id == user_id, LabUser.is_active).first()
    if user is None:
        user = (
            db.query(User)
            .filter(User.id == user_id, User.is_active, User.is_verified)
            .first()
        )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found, inactive, or unverified",
        )

    # ── perm_version check ────────────────────────────────────────────────────
    # Fast path: compare against Redis (O(1)).  Falls back to DB value if Redis
    # has no entry for this user yet (e.g. first request after server restart).
    token_perm_ver = int(payload.get("perm_ver", 1))
    authoritative_ver = get_perm_version(
        user.id,
        user.perm_version or 1,
        account_kind="user" if isinstance(user, User) else "lab",
    )
    if token_perm_ver != authoritative_ver:
        logger.warning(
            "Permission version mismatch user=%s token_perm_ver=%s authoritative=%s",
            user.id, token_perm_ver, authoritative_ver,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Permissions updated — please log in again",
        )

    # ── Lab active check (skip for master_admin) ──────────────────────────────
    if isinstance(user, LabUser) and user.role != "master_admin":
        lab = db.query(Lab).filter(Lab.id == user.lab_id, Lab.is_active).first()
        if lab is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your laboratory account is deactivated",
            )

    # ── Correlation context — propagate user/lab for DB error logging ─────────
    from ..database import _lab_id_var, _user_id_var

    _user_id_var.set(user.id)
    _lab_id_var.set(user.lab_id)

    return user


def require_institutional_user(
    current_user: LabUser | User = Depends(get_current_user),
) -> LabUser:
    """Allow only active institutional accounts backed by ``LabUser``.

    Citizen/individual ``User`` accounts must never reach device-integration
    endpoints, even if a role or a stale client-side permission suggests access.
    """
    if not isinstance(current_user, LabUser) or current_user.lab_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device integration is available to institutional accounts only",
        )
    return current_user


def require_institutional_permission(permission: str):
    """Require an institutional account and a specific lab permission."""

    def checker(
        current_user: LabUser = Depends(require_institutional_user),
    ) -> LabUser:
        if permission not in get_permissions_for_role(current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}",
            )
        return current_user

    return checker


def require_permission(permission: str):
    """FastAPI dependency factory: require a specific permission.

    Permissions are derived from the user's role at request time — no extra
    DB query needed (O(1) dict lookup in rbac.ROLE_PERMISSIONS).

    Usage:
        @router.get("/patients")
        def list_patients(user=Depends(require_permission("patients:read"))):
            ...
    """

    def checker(current_user: LabUser = Depends(get_current_user)) -> LabUser:
        if permission not in get_permissions_for_role(current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}",
            )
        return current_user

    return checker


def get_current_lab(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Lab:
    lab = db.query(Lab).filter(Lab.id == current_user.lab_id, Lab.is_active).first()
    if lab is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lab not found or inactive",
        )
    return lab


def require_service_account(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> LabUser | ServiceAccount:
    raw_token = _extract_token(credentials, request)
    if raw_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    if raw_token.startswith("gula_"):
        from .service_accounts import validate_api_key

        account = validate_api_key(db, raw_token)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired API key",
            )
        return account

    return get_current_user(request, credentials, db)
