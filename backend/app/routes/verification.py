"""Safe email/phone verification for citizen and provider onboarding.

The verification code is stored only as a SHA-256 digest in the configured
short-lived cache. In demo/test environments the code is returned explicitly
so the isolated environment can be tested without an external mail/SMS vendor.
Production responses never include the code.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from ..config import DEMO_MODE, IS_PRODUCTION
from ..database import get_db
from ..models.user import User
from ..security.rate_limit import get_client_ip, rate_limit_auth
from ..security.redis_client import cache
from ..services.audit_service import log_action

router = APIRouter(prefix="/auth/verification", tags=["auth / verification"])

_CODE_TTL_SECONDS = 15 * 60
_MAX_ATTEMPTS = 5


def _normalize_identifier(value: str) -> str:
    return value.strip().lower()


def _cache_key(identifier: str) -> str:
    digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()
    return f"verification:code:{digest}"


def _attempt_key(identifier: str) -> str:
    digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()
    return f"verification:attempts:{digest}"


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _find_user(db: Session, identifier: str) -> User | None:
    return (
        db.query(User)
        .filter((User.email == identifier) | (User.phone == identifier))
        .first()
    )


class VerificationRequest(BaseModel):
    identifier: str

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        value = _normalize_identifier(value)
        if len(value) < 5 or len(value) > 100:
            raise ValueError("Invalid verification identifier")
        return value


class VerificationConfirmRequest(VerificationRequest):
    code: str

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        if len(value) != 6 or not value.isdigit():
            raise ValueError("Verification code must contain six digits")
        return value


_GENERIC_MESSAGE = (
    "If the account exists, a verification code has been sent."
)


def _issue_code(user: User, identifier: str) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    channel = "email" if user.email and identifier == user.email else "sms"
    cache.set(
        _cache_key(identifier),
        json.dumps({"digest": _hash_code(code), "user_id": user.id, "channel": channel}),
        ex=_CODE_TTL_SECONDS,
    )
    cache.set(_attempt_key(identifier), "0", ex=_CODE_TTL_SECONDS)

    message = (
        f"Your GULA verification code is {code}. It expires in 15 minutes."
    )
    if channel == "email":
        from ..notifications.service import get_service

        get_service().send_email(user.email, "GULA account verification", message)
    elif user.phone:
        from ..notifications.service import get_service

        get_service().send_sms(user.phone, message)
    return code


@router.post("/request", status_code=202)
def request_verification(
    data: VerificationRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    rate_limit_auth(request)
    identifier = data.identifier
    user = _find_user(db, identifier)

    # Keep the response identical for unknown and known identifiers.
    response: dict[str, object] = {"message": _GENERIC_MESSAGE}
    if user and not user.is_verified and user.is_active:
        code = _issue_code(user, identifier)
        log_action(
            db,
            action="verification_requested",
            resource_type="user",
            resource_id=user.id,
            user_id=user.id,
            user_role=user.role,
            details="Account verification code requested",
            ip_address=get_client_ip(request),
        )
        db.commit()
        if DEMO_MODE or not IS_PRODUCTION:
            response["demo_code"] = code
    return response


@router.post("/confirm")
def confirm_verification(
    data: VerificationConfirmRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    rate_limit_auth(request)
    identifier = data.identifier
    entry = cache.get(_cache_key(identifier))
    user = _find_user(db, identifier)

    if not entry or not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    attempts = int(cache.get(_attempt_key(identifier)) or "0")
    if attempts >= _MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many verification attempts")
    cache.set(_attempt_key(identifier), attempts + 1, ex=_CODE_TTL_SECONDS)

    try:
        stored = json.loads(entry)
    except json.JSONDecodeError:
        stored = {}
    valid = hmac.compare_digest(str(stored.get("digest", "")), _hash_code(data.code))
    if int(stored.get("user_id", -1)) != user.id or not valid:
        log_action(
            db,
            action="verification_failed",
            resource_type="user",
            resource_id=user.id,
            user_id=user.id,
            user_role=user.role,
            details="Invalid account verification code",
            ip_address=get_client_ip(request),
        )
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    user.is_verified = True
    user.perm_version = (user.perm_version or 1) + 1
    log_action(
        db,
        action="verification_confirmed",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        user_role=user.role,
        details="Account verification completed",
        ip_address=get_client_ip(request),
    )
    db.commit()
    cache.delete(_cache_key(identifier))
    cache.delete(_attempt_key(identifier))
    return {
        "message": "Account verified successfully",
        "message_ar": "تم التحقق من الحساب بنجاح",
        "user_id": user.id,
    }
