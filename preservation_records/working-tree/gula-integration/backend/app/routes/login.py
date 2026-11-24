import hashlib
import hmac
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, field_validator
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..config import (
    DEMO_MODE,
    JWT_EXPIRE_MINUTES,
    NID_HMAC_KEY,
    REFRESH_TOKEN_EXPIRE_DAYS,
    cookie_security_options,
)
from ..database import get_db
from ..models.lab_user import LabUser
from ..models.user import User
from ..security.auth import (
    ACCOUNT_KIND_LAB,
    ACCOUNT_KIND_USER,
    MFA_PENDING_TTL_MINUTES,
    blacklist_token,
    build_token_payload,
    create_mfa_pending_token,
    create_refresh_token,
    create_token,
    decode_mfa_pending_token,
    decode_refresh_token,
    decode_token,
    is_token_blacklisted,
    verify_password,
)
from ..security.dependencies import _extract_token, get_current_user, security
from ..security.login_protection import is_locked, register_failed_login, register_successful_login
from ..security.rate_limit import get_client_ip, rate_limit_auth
from ..security.session import bump_perm_version, warm_perm_version
from ..services.audit_service import log_action

logger = logging.getLogger("gula.auth")

router = APIRouter(tags=["auth"])

# Roles whose password-only login is never sufficient (AUD-SEC-003).
PRIVILEGED_ROLES = frozenset({"master_admin", "ministry_admin", "province_admin"})


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v):
        return v.strip().lower()


class MFAVerifyRequest(BaseModel):
    """Stage-2 of privileged login: the scoped pending token plus one factor."""

    mfa_pending_token: str
    method: str = "totp"  # "totp" (incl. backup codes) or "webauthn"
    code: str | None = None  # TOTP / backup code
    credential: dict | None = None  # WebAuthn assertion


class MFAPendingBeginRequest(BaseModel):
    mfa_pending_token: str


def _pending_ttl_seconds(payload: dict) -> int:
    exp = payload.get("exp")
    if exp is None:
        return MFA_PENDING_TTL_MINUTES * 60
    return max(1, int(exp - datetime.now(UTC).timestamp()))


def _decode_valid_pending(token: str) -> dict | None:
    """Decode a pending token that is well-formed, lab-scoped and not consumed."""
    payload = decode_mfa_pending_token(token)
    if payload is None:
        return None
    jti = payload.get("jti")
    if not jti or payload.get("account_kind") != ACCOUNT_KIND_LAB or not payload.get("user_id"):
        return None
    try:
        if is_token_blacklisted(jti):
            return None
    except Exception:
        # Fail closed: cannot prove the single-use challenge is unconsumed.
        return None
    return payload


def _complete_login(db, response, user, base_payload, user_name, lab_name, client_ip):
    """Issue full tokens, set cookies, audit and render the login response."""
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

    cookie_kwargs = cookie_security_options()
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

    # ── Stage privileged login behind a real MFA challenge (AUD-SEC-003) ────
    # Previously, merely *having* an MFA device enrolled was treated as MFA.
    # Password-only access issued full tokens. We now stop after credentials
    # and return a short-lived, single-purpose token; full tokens require a
    # verified second factor at POST /login/mfa/verify.
    if user.role in PRIVILEGED_ROLES:
        from ..security.mfa_service import MFAService

        if not isinstance(user, LabUser):
            # Privileged roles are institutional accounts; MFA devices are
            # bound to lab_users. Fail closed for any other account family.
            log_action(
                db,
                action="login_denied_mfa_required",
                resource_type="auth",
                user_id=user.id,
                user_role=user.role,
                details="Login denied: privileged role is not an institutional account",
                ip_address=client_ip,
            )
            db.commit()
            raise HTTPException(status_code=403, detail="MFA enrollment required for privileged accounts.")

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

        enrolled = mfa.get_user_devices(user.id)
        methods = []
        if any(d.get("device_type") == "totp" for d in enrolled):
            methods.append("totp")
        if any(d.get("device_type") in ("webauthn", "fido2", "passkey") for d in enrolled):
            methods.append("webauthn")

        pending_token = create_mfa_pending_token(
            {
                "user_id": user.id,
                "lab_id": user.lab_id,
                "role": user.role,
                "account_kind": ACCOUNT_KIND_LAB,
            }
        )
        log_action(
            db,
            action="login_mfa_challenge_issued",
            resource_type="auth",
            user_id=user.id,
            user_role=user.role,
            details="Privileged credential check passed; MFA challenge pending",
            ip_address=client_ip,
        )
        db.commit()
        return {
            "mfa_required": True,
            "mfa_pending_token": pending_token,
            "mfa_methods": methods,
            "expires_in": MFA_PENDING_TTL_MINUTES * 60,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
            },
        }

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
        # Citizen token payload (no perm_version needed). account_kind binds
        # this token to the User table so it can never resolve to a LabUser
        # with a colliding primary key (AUD-SEC-002).
        base_payload = {
            "user_id": citizen.id,
            "lab_id": None,
            "role": "citizen",
            "perm_ver": 1,
            "account_kind": ACCOUNT_KIND_USER,
        }
        user_name = citizen.full_name
        lab_name = None

    return _complete_login(db, response, user, base_payload, user_name, lab_name, client_ip)


@router.post("/login/mfa/webauthn/begin")
def privileged_webauthn_begin(
    data: MFAPendingBeginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Produce a WebAuthn assertion challenge for a pending privileged login."""
    payload = _decode_valid_pending(data.mfa_pending_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid, expired or consumed MFA challenge")
    rate_limit_auth(request, identifier=f"mfa-begin:{payload['user_id']}")
    from ..security.mfa_service import MFAService

    return MFAService(db).begin_webauthn_authentication(int(payload["user_id"]))


@router.post("/login/mfa/verify")
def privileged_mfa_verify(
    data: MFAVerifyRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Stage 2 of privileged login: verify a real factor, then issue full tokens.

    The pending token is single-use — it is blacklisted on first use (success
    or failure-independent replay defence) so a password-only caller, or an
    attacker replaying the challenge, can never mint full privileged tokens.
    """
    client_ip = get_client_ip(request)
    payload = _decode_valid_pending(data.mfa_pending_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid, expired or consumed MFA challenge")

    jti = payload["jti"]
    user_id = int(payload["user_id"])
    rate_limit_auth(request, identifier=f"mfa-verify:{user_id}")

    lab_user = (
        db.query(LabUser).filter(LabUser.id == user_id, LabUser.is_active).first()
    )
    if lab_user is None or lab_user.role not in PRIVILEGED_ROLES:
        log_action(
            db,
            action="login_mfa_failed",
            resource_type="auth",
            user_id=user_id,
            details="MFA verify rejected: account missing or no longer privileged",
            ip_address=client_ip,
        )
        db.commit()
        raise HTTPException(status_code=401, detail="MFA verification failed")

    from ..security.mfa_service import MFAService

    mfa = MFAService(db)
    verified = False
    try:
        if data.method == "totp":
            verified = bool(data.code) and mfa.verify_totp(user_id, data.code)
        elif data.method == "webauthn":
            verified = data.credential is not None and mfa.complete_webauthn_authentication(
                user_id, data.credential
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported MFA method")
    except HTTPException:
        raise
    except Exception:
        # WebAuthn verification raises a family of Invalid* exceptions; all
        # are treated as a failed factor (never a bypass).
        verified = False

    if not verified:
        log_action(
            db,
            action="login_mfa_failed",
            resource_type="auth",
            user_id=user_id,
            user_role=lab_user.role,
            details=f"MFA verification failed for method={data.method}",
            ip_address=client_ip,
        )
        db.commit()
        raise HTTPException(status_code=401, detail="MFA verification failed")

    # Consume the single-use challenge *before* issuing tokens.
    blacklist_token(jti, _pending_ttl_seconds(payload))

    # Re-check lab active status at the moment of token issuance.
    from ..models.lab import Lab

    lab = db.query(Lab).filter(Lab.id == lab_user.lab_id, Lab.is_active).first()
    if not lab and lab_user.role != "master_admin":
        log_action(
            db,
            action="login_denied",
            resource_type="auth",
            user_id=lab_user.id,
            user_role=lab_user.role,
            details="Login denied: laboratory deactivated during MFA",
            ip_address=client_ip,
        )
        db.commit()
        raise HTTPException(status_code=403, detail="Your laboratory account is deactivated")

    warm_perm_version(lab_user)
    base_payload = build_token_payload(lab_user)
    return _complete_login(db, response, lab_user, base_payload, lab_user.name, lab.name if lab else None, client_ip)


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Logout with two-layer revocation:
    1. Redis JTI blacklist — fast, rejects this specific token within milliseconds
    2. DB perm_version bump — survives Redis restart; invalidates ALL sessions for this user

    AUD-SEC-004: the token is now obtained through the SAME ``_extract_token``
    helper every protected route uses — Bearer header (mobile) first, then the
    httpOnly cookie (web). Previously only cookies were read, so a Bearer-only
    client's logout blacklisted nothing and bumped no version: its token stayed
    fully usable. Refresh tokens are cookie-based but are also tolerated in the
    Bearer slot for mobile clients that submit the refresh token there.
    """
    import time as _time

    user_id = None

    def _revoke(raw_token: str | None, *, refresh: bool = False) -> None:
        """Blacklist a presented token's JTI and capture its subject for the bump."""
        nonlocal user_id
        if not raw_token:
            return
        payload = decode_refresh_token(raw_token) if refresh else decode_token(raw_token)
        if not payload and not refresh:
            # A mobile client may place a refresh token in the Bearer slot.
            payload = decode_refresh_token(raw_token)
        if not payload:
            return
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and exp:
            remaining = int((exp - _time.time()) + 1)
            if remaining > 0:
                ttl = min(remaining, REFRESH_TOKEN_EXPIRE_DAYS * 86400) if refresh else remaining
                blacklist_token(jti, ttl)
        if not user_id:
            user_id = payload.get("user_id")

    # Layer 1: blacklist the access token (Bearer OR cookie — shared helper).
    _revoke(_extract_token(credentials, request))
    # R-SEC-004-A (found by Team C): _extract_token gives Bearer precedence, so a
    # stale/invalid Bearer header would shadow a valid access cookie — logout
    # returned 200 but blacklisted nothing and bumped no perm_version, leaving
    # the cookie session live. Revoke EVERY presented credential independently;
    # duplicate JTI blacklist writes are harmless and idempotent.
    if credentials and credentials.credentials:
        _revoke(credentials.credentials)
    cookie_access = request.cookies.get("access_token")
    if cookie_access:
        _revoke(cookie_access)
    # Layer 1b: blacklist the refresh token (cookie, or Bearer slot via helper).
    _revoke(request.cookies.get("refresh_token"), refresh=True)

    # Layer 2: bump perm_version in DB so ALL existing tokens become invalid
    # This is the safety net if Redis is wiped — get_current_user will reject
    # any token whose perm_ver no longer matches the DB value.
    if user_id:
        user = db.query(LabUser).filter(LabUser.id == user_id).first()
        if user is None:
            user = db.query(User).filter(User.id == user_id).first()
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
