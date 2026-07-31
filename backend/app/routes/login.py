import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from ..config import IS_PRODUCTION, JWT_EXPIRE_MINUTES, NID_HMAC_KEY, REFRESH_TOKEN_EXPIRE_DAYS
from ..database import get_db
from ..models.lab_user import LabUser
from ..models.user import User
from ..security.auth import (
    blacklist_token,
    build_token_payload,
    create_refresh_token,
    create_token,
    decode_refresh_token,
    decode_token,
    verify_password,
)
from ..security.rate_limit import get_client_ip, rate_limit_auth
from ..security.session import bump_perm_version, warm_perm_version
from ..services.audit_service import log_action

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

    # ── Try lab staff / admin first ────────────────────────────────────────────
    lab_user = (
        db.query(LabUser)
        .filter(
            LabUser.email == email,
            LabUser.is_active,
        )
        .first()
    )

    # ── Fallback: citizen account ──────────────────────────────────────────────
    citizen = None
    if not lab_user:
        citizen = (
            db.query(User)
            .filter(
                User.email == email,
                User.is_active,
            )
            .first()
        )

    user = lab_user or citizen

    # Always call verify_password to prevent user-enumeration via timing.
    # When user is None we verify against a dummy hash (constant time).
    from ..security.auth import _DUMMY_HASH  # defined alongside pwd_context

    password_ok = verify_password(
        data.password,
        user.password_hash if user else _DUMMY_HASH,
    )
    if not user or not password_ok:
        log_action(
            db,
            action="login_failed",
            resource_type="auth",
            user_id=user.id if user else None,
            user_role=user.role if user else None,
            details=f"Failed login for email_hmac: {hmac.new(NID_HMAC_KEY.encode(), email.encode(), hashlib.sha256).hexdigest()[:16]}",
            ip_address=client_ip,
        )
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # ── Enforce MFA for privileged roles ─────────────────────────────────────
    privileged_roles = {"master_admin", "ministry_admin", "province_admin"}
    if user.role in privileged_roles:
        from ..security.mfa_service import MFAService

        mfa = MFAService(db)
        if not mfa.has_mfa_enabled(user.id):
            log_action(
                db,
                action="login_denied_mfa_required",
                resource_type="auth",
                user_id=user.id,
                user_role=user.role,
                details="Login denied: MFA required for privileged role",
                ip_address=client_ip,
            )
            db.commit()
            raise HTTPException(
                status_code=403,
                detail="MFA enrollment required for privileged accounts. Please set up MFA before logging in.",
            )

    # ── Lab-user: check lab is still active ───────────────────────────────────
    lab = None
    if lab_user:
        from ..models.lab import Lab

        lab = db.query(Lab).filter(Lab.id == lab_user.lab_id, Lab.is_active).first()
        if not lab and lab_user.role != "master_admin":
            log_action(
                db,
                action="login_denied",
                resource_type="auth",
                user_id=lab_user.id,
                user_role=lab_user.role,
                details="Login denied: laboratory deactivated",
                ip_address=client_ip,
            )
            db.commit()
            raise HTTPException(status_code=403, detail="Your laboratory account is deactivated")

        # Warm Redis perm_version cache (lab users only)
        warm_perm_version(lab_user)
        base_payload = build_token_payload(lab_user)
        user_name = lab_user.name
        lab_name = lab.name if lab else None
    else:
        # Citizen token payload (no perm_version needed)
        base_payload = {
            "user_id": citizen.id,
            "lab_id": None,
            "role": "citizen",
            "perm_ver": 1,
        }
        user_name = citizen.full_name
        lab_name = None

    token = create_token(base_payload)
    refresh_token = create_refresh_token(base_payload)

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

    cookie_kwargs = {
        "httponly": True,
        "samesite": "strict",
        "secure": IS_PRODUCTION,
    }
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=JWT_EXPIRE_MINUTES * 60,
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
            "name": user_name,
            "email": user.email,
            "role": user.role,
            "lab_id": user.lab_id,
            "lab_name": lab_name,
        },
    }


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """Logout with two-layer revocation:
    1. Redis JTI blacklist — fast, rejects this specific token within milliseconds
    2. DB perm_version bump — survives Redis restart; invalidates ALL sessions for this user
    """
    import time as _time

    user_id = None

    # Layer 1: blacklist access token JTI in Redis
    access_token = request.cookies.get("access_token")
    if access_token:
        payload = decode_token(access_token)
        if payload:
            user_id = payload.get("user_id")
            jti = payload.get("jti")
            if jti:
                remaining = int((payload["exp"] - _time.time()) + 1)
                if remaining > 0:
                    blacklist_token(jti, remaining)

    # Layer 1b: blacklist refresh token JTI in Redis
    refresh_cookie = request.cookies.get("refresh_token")
    if refresh_cookie:
        rp = decode_refresh_token(refresh_cookie)
        if rp and rp.get("jti"):
            remaining = int((rp["exp"] - _time.time()) + 1)
            if remaining > 0:
                blacklist_token(rp["jti"], min(remaining, REFRESH_TOKEN_EXPIRE_DAYS * 86400))
            if not user_id:
                user_id = rp.get("user_id")

    # Layer 2: bump perm_version in DB so ALL existing tokens become invalid
    # This is the safety net if Redis is wiped — get_current_user will reject
    # any token whose perm_ver no longer matches the DB value.
    if user_id:
        user = db.query(LabUser).filter(LabUser.id == user_id).first()
        if user:
            bump_perm_version(
                user,
                db,
                actor_id=user_id,
                actor_role=user.role,
                reason="logout",
            )
            db.commit()

    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"message": "Logged out successfully"}
