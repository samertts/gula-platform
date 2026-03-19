from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.lab_user import LabUser
from ..models.lab import Lab
from .auth import decode_token
from .rbac import get_permissions_for_role

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
) -> LabUser:
    raw_token = _extract_token(credentials, request)
    if raw_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    payload = decode_token(raw_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    user = db.query(LabUser).filter(LabUser.id == user_id, LabUser.is_active == True).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # perm_version check — if admin changed user's role, old tokens are rejected
    token_perm_ver = payload.get("perm_ver", 1)
    db_perm_ver = user.perm_version if user.perm_version is not None else 1
    if token_perm_ver != db_perm_ver:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Permissions updated — please log in again",
        )

    # Check if lab is still active (skip for master_admin)
    if user.role != "master_admin":
        lab = db.query(Lab).filter(Lab.id == user.lab_id, Lab.is_active == True).first()
        if lab is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your laboratory account is deactivated",
            )

    return user


def require_permission(permission: str):
    """FastAPI dependency factory: require a specific permission.

    Usage:
        @router.get("/patients")
        def list_patients(user=Depends(require_permission("patients:read"))):
            ...
    """
    def checker(
        current_user: LabUser = Depends(get_current_user),
    ) -> LabUser:
        perms = get_permissions_for_role(current_user.role)
        if permission not in perms:
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
    lab = db.query(Lab).filter(Lab.id == current_user.lab_id, Lab.is_active == True).first()
    if lab is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lab not found or inactive",
        )
    return lab
