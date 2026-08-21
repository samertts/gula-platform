from __future__ import annotations

import contextlib
import hashlib
import os
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.account_recovery import AccountRecoveryRequest
from app.models.user import User
from app.security.dependencies import get_current_user
from app.security.rate_limit import get_client_ip, rate_limit_auth
from app.security.recovery import (
    APPROVED,
    PENDING_REVIEW,
    RecoveryError,
    complete_password_recovery,
    create_manual_review_request,
    mark_recovery_delivery_failed,
    mark_recovery_delivery_pending_review,
    request_password_recovery,
    verify_password_recovery,
)
from app.services.audit_service import log_action
from shared.auth.passwords import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["password-reset"])


class ForgotPasswordRequest(BaseModel):
    email: str = Field(min_length=1, max_length=320)


class RecoveryVerifyRequest(BaseModel):
    token: str = Field(min_length=1, max_length=128)
    request_id: str | None = Field(default=None, min_length=36, max_length=36)


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=1, max_length=256)
    request_id: str | None = Field(default=None, min_length=36, max_length=36)


class SecurityRecoveryRequest(BaseModel):
    operation: Literal["contact_change", "lost_device", "mfa_reset", "passkey_recovery", "account_unlock"]


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=10, max_length=256)


_GENERIC_RECOVERY_MESSAGE = "If the account exists, recovery instructions will be sent."


def _recovery_error(exc: RecoveryError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "code": exc.code,
            "message": exc.message,
            "message_ar": "تعذر إكمال طلب الاستعادة. تحقق من الرمز أو أعد المحاولة لاحقاً.",
        },
    )


def _token_rate_key(token: str) -> str:
    # The raw recovery secret never becomes a Redis key or a log value.
    return f"recovery:{hashlib.sha256(token.encode('utf-8')).hexdigest()[:32]}"


@router.post("/forgot-password")
def forgot_password(
    req: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    """Start password recovery without account enumeration.

    No token is returned in the response. If a real email provider is not
    explicitly enabled and configured, the request is moved to PENDING_REVIEW
    rather than pretending that delivery succeeded.
    """
    rate_limit_auth(request, max_per_minute=5, identifier=req.email)
    recovery, raw_token = request_password_recovery(
        db,
        email=str(req.email),
        idempotency_key=idempotency_key,
        requested_ip=get_client_ip(request),
    )
    if recovery is None:
        return {"message": _GENERIC_RECOVERY_MESSAGE}
    if raw_token is None:
        return {"message": _GENERIC_RECOVERY_MESSAGE}

    email_enabled = os.getenv("ACCOUNT_RECOVERY_EMAIL_ENABLED", "false").lower() == "true"
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    if not email_enabled or not smtp_host:
        mark_recovery_delivery_pending_review(db, recovery)
        return {"message": _GENERIC_RECOVERY_MESSAGE}

    try:
        from app.platform.notifications import NotificationService

        result = NotificationService().send_notification(
            channel="email",
            to=str(req.email),
            subject="GULA account recovery",
            body=(
                "Use this one-time recovery token only through the official GULA recovery client. "
                f"Request ID: {recovery.request_id}. Token: {raw_token}. It expires shortly and must never be shared."
            ),
        )
        if not result.success:
            mark_recovery_delivery_failed(db, recovery)
            return {"message": _GENERIC_RECOVERY_MESSAGE}
    except Exception:
        # The exception path is deliberately generic and never logs the token.
        mark_recovery_delivery_failed(db, recovery)
        return {"message": _GENERIC_RECOVERY_MESSAGE}

    with contextlib.suppress(Exception):
        log_action(
            db,
            action="recovery_delivery_dispatched",
            resource_type="account_recovery",
            resource_id=recovery.id,
            user_id=recovery.account_id,
            lab_id=recovery.lab_id,
            details={
                "request_id": recovery.request_id,
                "correlation_id": recovery.correlation_id,
                "channel": "email",
            },
            ip_address=recovery.requested_ip,
        )
        db.commit()
    return {"message": _GENERIC_RECOVERY_MESSAGE}


@router.post("/recovery/verify")
def verify_recovery(
    req: RecoveryVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    rate_limit_auth(request, max_per_minute=5, identifier=_token_rate_key(req.token))
    try:
        recovery = verify_password_recovery(db, token=req.token, request_id=req.request_id)
    except RecoveryError as exc:
        raise _recovery_error(exc) from exc
    return {
        "status": recovery.state,
        "message": "Recovery verified. Continue with the password reset.",
    }


@router.post("/reset-password")
def reset_password(
    req: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    rate_limit_auth(request, max_per_minute=5, identifier=_token_rate_key(req.token))
    try:
        # Compatibility path: a verified delivery token may complete directly,
        # but the server still records every state transition before mutation.
        recovery = verify_password_recovery(db, token=req.token, request_id=req.request_id)
        if recovery.state not in {APPROVED}:
            raise RecoveryError("RECOVERY_VERIFICATION_REQUIRED", "Recovery verification is required before reset", 403)
        complete_password_recovery(db, token=req.token, new_password=req.new_password, request_id=req.request_id)
    except RecoveryError as exc:
        # If the explicit verify endpoint already approved the token, complete
        # without attempting a second verification transition.
        if exc.code == "RECOVERY_NOT_VERIFIABLE":
            try:
                complete_password_recovery(db, token=req.token, new_password=req.new_password, request_id=req.request_id)
            except RecoveryError as nested:
                raise _recovery_error(nested) from nested
        else:
            raise _recovery_error(exc) from exc
    return {"message": "Password reset successful. All previous sessions require re-authentication."}


@router.post("/security/recovery-request")
def request_security_recovery(
    req: SecurityRecoveryRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rate_limit_auth(request, max_per_minute=3, identifier=getattr(current_user, "email", None))
    try:
        recovery = create_manual_review_request(
            db,
            account=current_user,
            operation=req.operation,
            requested_ip=get_client_ip(request),
        )
    except RecoveryError as exc:
        raise _recovery_error(exc) from exc
    return {
        "request_id": recovery.request_id,
        "status": PENDING_REVIEW,
        "operation": recovery.operation,
        "message": "Security recovery request submitted for manual review. No account security state was changed.",
    }


@router.get("/recovery/{request_id}")
def get_recovery_status(
    request_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    account_kind = "user" if isinstance(current_user, User) else "lab"
    recovery = (
        db.query(AccountRecoveryRequest)
        .filter(
            AccountRecoveryRequest.request_id == request_id,
            AccountRecoveryRequest.account_id == current_user.id,
            AccountRecoveryRequest.account_kind == account_kind,
        )
        .first()
    )
    if recovery is None:
        raise HTTPException(status_code=404, detail="Recovery request not found")
    return {
        "request_id": recovery.request_id,
        "status": recovery.state,
        "operation": recovery.operation,
        "assurance_level": recovery.assurance_level,
        "created_at": recovery.created_at,
        "updated_at": recovery.updated_at,
    }


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rate_limit_auth(request, max_per_minute=5, identifier=getattr(current_user, "email", None))
    if not verify_password(req.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.password_hash = hash_password(req.new_password)
    from app.security.session import bump_perm_version

    bump_perm_version(
        current_user,
        db,
        actor_id=current_user.id,
        actor_role=getattr(current_user, "role", None),
        reason="password_changed",
    )
    log_action(
        db,
        action="session_revoked",
        resource_type="account_security",
        resource_id=current_user.id,
        user_id=current_user.id,
        user_role=getattr(current_user, "role", None),
        lab_id=getattr(current_user, "lab_id", None),
        details={"reason_code": "password_changed"},
        ip_address=get_client_ip(request),
    )
    log_action(
        db,
        action="password_changed",
        resource_type="account_security",
        resource_id=current_user.id,
        user_id=current_user.id,
        user_role=getattr(current_user, "role", None),
        lab_id=getattr(current_user, "lab_id", None),
        details={"reason_code": "current_password_verified"},
        ip_address=get_client_ip(request),
    )
    db.commit()
    return {"message": "Password changed successfully. Other sessions require re-authentication."}
