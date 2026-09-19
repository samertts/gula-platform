import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, field_validator
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..config import (
    DEMO_MODE,
    JWT_EXPIRE_MINUTES,
    NID_HMAC_KEY,
    REFRESH_TOKEN_EXPIRE_DAYS,
    USE_SECURE_COOKIES,
)
from ..database import get_db
from ..identity.services.legacy_session_bridge import (
    establish_canonical_session,
    resolve_canonical_account,
    session_expiry,
    terminate_canonical_session,
)
from ..models.lab_user import LabUser
from ..models.user import User
from ..security.auth import (
    ACCOUNT_KIND_LAB,
    ACCOUNT_KIND_USER,
    blacklist_token,
    build_token_payload,
    create_refresh_token,
    create_token,
    decode_refresh_token,
    decode_token,
    verify_password,
)
from ..security.dependencies import get_current_user, resolve_token_subject
from ..security.login_protection import is_locked, register_failed_login, register_successful_login
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
    client_ip = get_client_ip(request)
    identifier = data.email
    rate_limit_auth(request, identifier=identifier)

    # ── Try lab staff / admin first ────────────────────────────────────────────
    # The UI accepts email or phone; both are normalized before lookup.
    lab_user = (
        db.query(LabUser)
        .filter(
            LabUser.email == identifier,
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
                or_(User.email == identifier, User.phone == identifier),
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
    if user and is_locked(user):
        log_action(
            db,
            action="login_denied_lockout",
            resource_type="auth",
            user_id=user.id,
            user_role=user.role,
            details="Login denied while account lockout window is active",
            ip_address=client_ip,
        )
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user or not password_ok:
        if user:
            locked_now = register_failed_login(user)
            action = "login_lockout_started" if locked_now else "login_failed"
        else:
            action = "login_failed"
        log_action(
            db,
            action=action,
            resource_type="auth",
            user_id=user.id if user else None,
            user_role=user.role if user else None,
            details=f"Failed login for identifier_hmac: {hmac.new(NID_HMAC_KEY.encode(), identifier.encode(), hashlib.sha256).hexdigest()[:16]}",
            ip_address=client_ip,
        )
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")

    register_successful_login(user)

    # Citizen and provider accounts must complete the free verification flow
    # before any authenticated session is issued. Lab accounts remain gated by
    # lab approval and privileged-role MFA below.
    if not isinstance(user, LabUser) and not user.is_verified:
        log_action(
            db,
            action="login_denied_verification",
            resource_type="auth",
            user_id=user.id,
            user_role=user.role,
            details="Login denied: account verification required",
            ip_address=client_ip,
        )
        db.commit()
        raise HTTPException(
            status_code=403,
            detail="Account verification required before login.",
        )

    # ── Enforce MFA for privileged roles ─────────────────────────────────────
    PRIVILEGED_ROLES = {"master_admin", "ministry_admin", "province_admin"}
    if user.role in PRIVILEGED_ROLES:
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
        base_payload = build_token_payload(lab_user, account_kind=ACCOUNT_KIND_LAB)
        user_name = lab_user.name
        lab_name = lab.name if lab else None
    else:
        # Citizen token payload (no perm_version needed)
        base_payload = {
            "user_id": citizen.id,
            "lab_id": None,
            "role": "citizen",
            "perm_ver": 1,
            # NR-035: a citizen is a `users` row. Without this the claim is
            # indistinguishable from a lab_users id of the same number.
            "act": ACCOUNT_KIND_USER,
        }
        user_name = citizen.full_name
        lab_name = None

    # ── NR-135: bind this login to its canonical NIAM session ────────────────
    # NIAM is the canonical identity authority. The account is resolved from
    # the ALREADY-AUTHENTICATED legacy row, never from the request: the client
    # supplies a credential and cannot name an account_uuid, identity_id,
    # lab_id or role and have it become a security fact.
    #
    # account_uuid has to be in the payload BEFORE minting, and the jti only
    # exists AFTER minting (create_token generates its own), so the token is
    # minted once and then read back to bind the session to that exact jti.
    # One login, one jti, one session row.
    #
    # When no canonical account is linked, or it is not active, this is a
    # no-op: the legacy token is minted exactly as before and the
    # NIAM-protected surface keeps refusing it with 401. Nothing is widened by
    # the absence of a link.
    canonical_account = resolve_canonical_account(
        db,
        legacy_account_id=base_payload["user_id"],
        account_kind=base_payload["act"],
    )
    if canonical_account is not None:
        base_payload = {**base_payload, "account_uuid": canonical_account.uuid}

    token = create_token(base_payload)
    refresh_token = create_refresh_token(base_payload)

    if canonical_account is not None:
        access_claims = decode_token(token) or {}
        refresh_claims = decode_refresh_token(refresh_token) or {}
        establish_canonical_session(
            db,
            account=canonical_account,
            access_jti=access_claims["jti"],
            refresh_jti=refresh_claims.get("jti"),
            expires_at=session_expiry(REFRESH_TOKEN_EXPIRE_DAYS),
            ip_address=client_ip,
            user_agent=request.headers.get("user-agent"),
        )

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
        "secure": USE_SECURE_COOKIES,
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
        # `access_token` is the canonical native-client field; `token` remains
        # temporarily for older clients while they migrate to secure storage.
        "access_token": token,
        "token": token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": JWT_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "name": user_name,
            "email": user.email,
            "role": user.role,
            "lab_id": user.lab_id,
            "lab_name": lab_name,
            "is_verified": bool(getattr(user, "is_verified", True)),
        },
    }


def _bearer(request: Request) -> str | None:
    """The access token an API client actually sent, if it used the header."""
    header = request.headers.get("Authorization") or ""
    scheme, _, value = header.partition(" ")
    if scheme.lower() == "bearer" and value.strip():
        return value.strip()
    return None


def _body_refresh_token(request: Request) -> str | None:
    """A refresh token supplied out of band, so it can be revoked too."""
    return request.headers.get("X-Refresh-Token") or None


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """Logout with two-layer revocation:
    1. Redis JTI blacklist — fast, rejects this specific token within milliseconds
    2. DB perm_version bump — survives Redis restart; invalidates ALL sessions for this user
    """
    import time as _time

    user_id = None
    account_kind = None

    # Layer 1: blacklist access token JTI in Redis.
    #
    # The cookie alone is not the session. Every non-browser client -- the
    # mobile app, the device bridge, anything using the documented
    # `Authorization: Bearer` contract -- sends no cookie, so this read
    # returned None, nothing was blacklisted, user_id stayed None, and the
    # perm_version bump below never ran either. MEASURED on a live server:
    # POST /logout returned 200 and GET /session with the same bearer token
    # still returned 200 afterwards. Logout was a no-op for API clients.
    access_token = request.cookies.get("access_token") or _bearer(request)
    if access_token:
        payload = decode_token(access_token)
        if payload:
            user_id = payload.get("user_id")
            account_kind = payload.get("act")
            jti = payload.get("jti")
            if jti:
                remaining = int((payload["exp"] - _time.time()) + 1)
                if remaining > 0:
                    blacklist_token(jti, remaining)
                # NR-135. Revocation has to reach the canonical session too.
                # The Redis blacklist stops the legacy path; the NIAM-protected
                # surface authenticates against the niam_sessions row, so a
                # session left is_active=True would keep opening it after
                # logout for as long as the row lived.
                terminate_canonical_session(db, access_jti=jti, reason="logout")

    # Layer 1b: blacklist refresh token JTI in Redis
    refresh_cookie = request.cookies.get("refresh_token") or _body_refresh_token(request)
    if refresh_cookie:
        rp = decode_refresh_token(refresh_cookie)
        if rp and rp.get("jti"):
            remaining = int((rp["exp"] - _time.time()) + 1)
            if remaining > 0:
                blacklist_token(rp["jti"], min(remaining, REFRESH_TOKEN_EXPIRE_DAYS * 86400))
            if not user_id:
                user_id = rp.get("user_id")
                account_kind = rp.get("act")

    # Layer 2: bump perm_version in DB so ALL existing tokens become invalid
    # This is the safety net if Redis is wiped — get_current_user will reject
    # any token whose perm_ver no longer matches the DB value.
    if user_id:
        # NR-035: resolve through the shared discriminator-aware resolver so a
        # logout cannot bump the permission version of the wrong identity.
        user = resolve_token_subject(db, {"user_id": user_id, "act": account_kind})
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


@router.get("/session", summary="Return the authenticated session identity")
def get_session(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = current_user
    lab_name = None
    if isinstance(user, LabUser) and user.lab_id:
        from ..models.lab import Lab

        lab = db.query(Lab).filter(Lab.id == user.lab_id).first()
        lab_name = lab.name if lab else None
    return {
        "user": {
            "id": user.id,
            "name": getattr(user, "name", getattr(user, "full_name", "")),
            "email": user.email,
            "role": user.role,
            "lab_id": getattr(user, "lab_id", None),
            "lab_name": lab_name,
            "is_verified": bool(getattr(user, "is_verified", True)),
        },
        "demo_mode": DEMO_MODE,
    }
