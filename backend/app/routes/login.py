import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.lab_user import LabUser
from ..security.auth import verify_password, create_token, create_refresh_token, build_token_payload, blacklist_token
from ..security.auth import decode_token, decode_refresh_token
from ..security.rate_limit import rate_limit_auth, get_client_ip
from ..security.session import warm_perm_version
from ..services.audit_service import log_action
from ..config import IS_PRODUCTION, JWT_EXPIRE_HOURS, REFRESH_TOKEN_EXPIRE_DAYS

logger = logging.getLogger("gula.auth")

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v):
        return v.strip().lower()


@router.post("/login")
def login(data: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    rate_limit_auth(request)

    client_ip = get_client_ip(request)
    email = data.email

    # Lookup user (always verify password even if not found, to prevent timing attacks)
    user = db.query(LabUser).filter(
        LabUser.email == email,
        LabUser.is_active == True,
    ).first()

    if not user or not verify_password(data.password, user.password_hash):
        # Log failed login attempt for security monitoring
        log_action(
            db,
            action="login_failed",
            resource_type="auth",
            user_id=user.id if user else None,
            user_role=user.role if user else None,
            details=f"Failed login attempt for email: {email}",
            ip_address=client_ip,
        )
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Check if lab is active
    from ..models.lab import Lab
    lab = db.query(Lab).filter(Lab.id == user.lab_id, Lab.is_active == True).first()
    if not lab and user.role != "master_admin":
        log_action(
            db,
            action="login_denied",
            resource_type="auth",
            user_id=user.id,
            user_role=user.role,
            details="Login denied: laboratory deactivated",
            ip_address=client_ip,
        )
        db.commit()
        raise HTTPException(status_code=403, detail="Your laboratory account is deactivated")

    # Warm Redis so the fast perm_version path is always a cache hit after login
    warm_perm_version(user)

    base_payload = build_token_payload(user)
    token = create_token(base_payload)
    refresh_token = create_refresh_token(base_payload)

    # Audit log (don't log password in details)
    log_action(
        db,
        action="login",
        resource_type="auth",
        user_id=user.id,
        user_role=user.role,
        details="User logged in successfully",
        ip_address=client_ip,
    )
    db.commit()

    # Set httpOnly cookies for web browser clients (prevents XSS token theft)
    cookie_kwargs = {
        "httponly": True,
        "samesite": "strict",
        "secure": IS_PRODUCTION,
    }
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=JWT_EXPIRE_HOURS * 3600,
        path="/",
        **cookie_kwargs,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
        **cookie_kwargs,
    )

    return {
        "token": token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "lab_id": user.lab_id,
            "lab_name": lab.name if lab else None,
        },
    }


@router.post("/logout")
def logout(request: Request, response: Response):
    """Clear authentication cookies and blacklist current tokens."""
    # Blacklist access token JTI so it cannot be replayed (even if cookie is stolen)
    access_token = request.cookies.get("access_token")
    if access_token:
        payload = decode_token(access_token)
        if payload and payload.get("jti"):
            remaining = int((payload["exp"] - __import__("time").time()) + 1)
            if remaining > 0:
                blacklist_token(payload["jti"], remaining)

    # Blacklist refresh token JTI as well
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        payload = decode_refresh_token(refresh_token)
        if payload and payload.get("jti"):
            remaining = int((payload["exp"] - __import__("time").time()) + 1)
            if remaining > 0:
                from ..config import REFRESH_TOKEN_EXPIRE_DAYS
                blacklist_token(payload["jti"], min(remaining, REFRESH_TOKEN_EXPIRE_DAYS * 86400))

    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"message": "Logged out successfully"}
