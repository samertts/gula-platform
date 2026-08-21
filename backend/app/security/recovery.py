from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.config import (
    ACCOUNT_RECOVERY_MAX_ATTEMPTS,
    ACCOUNT_RECOVERY_TOKEN_TTL_MINUTES,
)
from app.models.account_recovery import AccountRecoveryRequest
from app.models.lab_user import LabUser
from app.models.user import User
from app.security.session import bump_perm_version
from app.services.audit_service import log_action
from shared.auth.passwords import hash_password

REQUESTED = "requested"
VERIFYING = "verifying"
VERIFIED = "verified"
APPROVED = "approved"
RECOVERED = "recovered"
FAILED = "failed"
EXPIRED = "expired"
REJECTED = "rejected"
LOCKED = "locked"
SUSPICIOUS = "suspicious"
CANCELLED = "cancelled"
PENDING_REVIEW = "pending_review"

_ACTIVE_STATES = (REQUESTED, VERIFYING, VERIFIED, APPROVED)
_HIGH_RISK_OPERATIONS = {"contact_change", "lost_device", "mfa_reset", "passkey_recovery", "account_unlock"}
_TERMINAL_STATES = (RECOVERED, FAILED, EXPIRED, REJECTED, LOCKED, SUSPICIOUS, CANCELLED)


class RecoveryError(ValueError):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_details(request: AccountRecoveryRequest, *, outcome: str, reason_code: str) -> dict[str, Any]:
    return {
        "operation": request.operation,
        "state": request.state,
        "outcome": outcome,
        "reason_code": reason_code,
        "request_id": request.request_id,
        "correlation_id": request.correlation_id,
        "account_kind": request.account_kind,
        "account_id": request.account_id,
        "lab_id": request.lab_id,
    }


def _audit(
    db: Session,
    request: AccountRecoveryRequest,
    *,
    action: str,
    outcome: str,
    reason_code: str,
) -> None:
    log_action(
        db,
        action=action,
        resource_type="account_recovery",
        resource_id=request.id,
        user_id=request.account_id,
        lab_id=request.lab_id,
        details=_safe_details(request, outcome=outcome, reason_code=reason_code),
        ip_address=request.requested_ip,
    )


def _lookup_account(db: Session, email: str) -> tuple[LabUser | User | None, str | None]:
    lab_user = db.query(LabUser).filter(LabUser.email == email, LabUser.is_active.is_(True)).first()
    if lab_user:
        return lab_user, "lab"
    citizen = (
        db.query(User)
        .filter(User.email == email, User.is_active.is_(True), User.is_verified.is_(True))
        .first()
    )
    return (citizen, "user") if citizen else (None, None)


def _load_account(db: Session, account_kind: str, account_id: int) -> LabUser | User | None:
    if account_kind == "lab":
        return db.query(LabUser).filter(LabUser.id == account_id).first()
    if account_kind == "user":
        return db.query(User).filter(User.id == account_id).first()
    return None


def request_password_recovery(
    db: Session,
    *,
    email: str,
    idempotency_key: str | None,
    requested_ip: str | None,
) -> tuple[AccountRecoveryRequest | None, str | None]:
    normalized_email = email.strip().lower()
    idempotency_digest = _digest(idempotency_key.strip()) if idempotency_key and idempotency_key.strip() else None

    if idempotency_digest:
        existing = (
            db.query(AccountRecoveryRequest)
            .filter(AccountRecoveryRequest.idempotency_key_digest == idempotency_digest)
            .first()
        )
        if existing:
            return existing, None

    account, account_kind = _lookup_account(db, normalized_email)
    if account is None or account_kind is None:
        # The caller must return the same generic response for this branch.
        return None, None

    # A new request supersedes older outstanding requests for the same account
    # and operation. This prevents multiple valid recovery paths from coexisting.
    db.query(AccountRecoveryRequest).filter(
        AccountRecoveryRequest.account_kind == account_kind,
        AccountRecoveryRequest.account_id == account.id,
        AccountRecoveryRequest.operation == "password_reset",
        AccountRecoveryRequest.state.in_(_ACTIVE_STATES),
    ).update(
        {
            AccountRecoveryRequest.state: CANCELLED,
            AccountRecoveryRequest.reason_code: "superseded_by_new_request",
            AccountRecoveryRequest.consumed_at: datetime.now(UTC),
            AccountRecoveryRequest.updated_at: datetime.now(UTC),
        },
        synchronize_session=False,
    )

    raw_token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    recovery = AccountRecoveryRequest(
        request_id=str(uuid.uuid4()),
        correlation_id=str(uuid.uuid4()),
        account_kind=account_kind,
        account_id=account.id,
        lab_id=getattr(account, "lab_id", None),
        operation="password_reset",
        state=REQUESTED,
        assurance_level="medium",
        risk_code="password_reset",
        token_digest=_digest(raw_token),
        idempotency_key_digest=idempotency_digest,
        max_attempts=ACCOUNT_RECOVERY_MAX_ATTEMPTS,
        created_at=now,
        updated_at=now,
        token_expires_at=now + timedelta(minutes=ACCOUNT_RECOVERY_TOKEN_TTL_MINUTES),
        requested_ip=requested_ip,
    )
    db.add(recovery)
    db.flush()
    _audit(db, recovery, action="recovery_requested", outcome="accepted", reason_code="password_reset_requested")
    db.commit()
    return recovery, raw_token


def mark_recovery_delivery_pending_review(db: Session, recovery: AccountRecoveryRequest) -> None:
    recovery.state = PENDING_REVIEW
    recovery.reason_code = "recovery_delivery_provider_unavailable"
    recovery.touch()
    _audit(
        db,
        recovery,
        action="recovery_review_pending",
        outcome="pending_review",
        reason_code="recovery_delivery_provider_unavailable",
    )
    db.commit()


def mark_recovery_delivery_failed(db: Session, recovery: AccountRecoveryRequest) -> None:
    recovery.state = FAILED
    recovery.reason_code = "recovery_delivery_failed"
    recovery.failed_at = datetime.now(UTC)
    recovery.token_digest = None
    recovery.touch()
    _audit(
        db,
        recovery,
        action="recovery_rejected",
        outcome="denied",
        reason_code="recovery_delivery_failed",
    )
    db.commit()


def create_manual_review_request(
    db: Session,
    *,
    account: LabUser | User,
    operation: str,
    requested_ip: str | None,
) -> AccountRecoveryRequest:
    if operation not in _HIGH_RISK_OPERATIONS:
        raise RecoveryError("UNSUPPORTED_RECOVERY_OPERATION", "This security operation requires a dedicated contract", 422)

    account_kind = "user" if isinstance(account, User) else "lab"
    existing = (
        db.query(AccountRecoveryRequest)
        .filter(
            AccountRecoveryRequest.account_kind == account_kind,
            AccountRecoveryRequest.account_id == account.id,
            AccountRecoveryRequest.operation == operation,
            AccountRecoveryRequest.state == PENDING_REVIEW,
        )
        .order_by(AccountRecoveryRequest.created_at.desc())
        .first()
    )
    if existing:
        return existing

    now = datetime.now(UTC)
    recovery = AccountRecoveryRequest(
        request_id=str(uuid.uuid4()),
        correlation_id=str(uuid.uuid4()),
        account_kind=account_kind,
        account_id=account.id,
        lab_id=getattr(account, "lab_id", None),
        operation=operation,
        state=PENDING_REVIEW,
        assurance_level="high",
        risk_code=f"{operation}_requires_manual_review",
        reason_code="no_provider_or_step_up_contract",
        max_attempts=ACCOUNT_RECOVERY_MAX_ATTEMPTS,
        created_at=now,
        updated_at=now,
        requested_ip=requested_ip,
    )
    db.add(recovery)
    db.flush()
    _audit(
        db,
        recovery,
        action="recovery_review_pending",
        outcome="pending_review",
        reason_code="no_provider_or_step_up_contract",
    )
    db.commit()
    return recovery


def verify_password_recovery(
    db: Session,
    *,
    token: str,
    request_id: str | None = None,
) -> AccountRecoveryRequest:
    token_digest = _digest(token)
    now = datetime.now(UTC)
    query = db.query(AccountRecoveryRequest)
    if request_id:
        recovery = (
            query.filter(AccountRecoveryRequest.request_id == request_id)
            .with_for_update()
            .first()
        )
    else:
        recovery = (
            query.filter(AccountRecoveryRequest.token_digest == token_digest)
            .with_for_update()
            .first()
        )
    if recovery is None:
        raise RecoveryError("INVALID_RECOVERY", "Invalid or expired recovery request")

    if request_id and not hmac.compare_digest(recovery.token_digest or "", token_digest):
        recovery.attempt_count += 1
        if recovery.attempt_count >= recovery.max_attempts:
            recovery.state = LOCKED
            recovery.reason_code = "verification_attempt_limit"
            recovery.failed_at = now
        recovery.touch()
        _audit(db, recovery, action="recovery_verification_attempt", outcome="denied", reason_code="invalid_token")
        db.commit()
        if recovery.state == LOCKED:
            raise RecoveryError("RECOVERY_LOCKED", "Recovery request is temporarily locked", 429)
        raise RecoveryError("INVALID_RECOVERY", "Invalid or expired recovery request")

    if recovery.state == PENDING_REVIEW:
        raise RecoveryError("RECOVERY_PENDING_REVIEW", "Recovery request requires manual review", 409)
    if recovery.state in _TERMINAL_STATES:
        raise RecoveryError("RECOVERY_NOT_ACTIVE", "Recovery request is no longer active", 409)
    token_expires_at = _utc(recovery.token_expires_at)
    if token_expires_at is None or token_expires_at <= now:
        recovery.state = EXPIRED
        recovery.reason_code = "token_expired"
        recovery.failed_at = now
        recovery.touch()
        _audit(db, recovery, action="recovery_verification_attempt", outcome="denied", reason_code="token_expired")
        db.commit()
        raise RecoveryError("RECOVERY_EXPIRED", "Invalid or expired recovery request")
    if recovery.attempt_count >= recovery.max_attempts:
        recovery.state = LOCKED
        recovery.reason_code = "verification_attempt_limit"
        recovery.failed_at = now
        recovery.touch()
        _audit(db, recovery, action="recovery_verification_attempt", outcome="denied", reason_code="verification_attempt_limit")
        db.commit()
        raise RecoveryError("RECOVERY_LOCKED", "Recovery request is temporarily locked", 429)
    if recovery.state not in {REQUESTED, VERIFYING}:
        raise RecoveryError("RECOVERY_NOT_VERIFIABLE", "Recovery request cannot be verified", 409)

    recovery.state = VERIFYING
    recovery.attempt_count += 1
    recovery.touch()
    _audit(db, recovery, action="recovery_verification_attempt", outcome="accepted", reason_code="token_verified")

    # Password reset is medium assurance and can be approved after possession
    # of the server-issued token. Contact, MFA, passkey, unlock, and lost-device
    # operations are intentionally not routed through this auto-approval path.
    recovery.state = VERIFIED
    recovery.verified_at = now
    recovery.state = APPROVED
    recovery.approved_at = now
    recovery.reason_code = "password_reset_token_verified"
    recovery.touch()
    _audit(db, recovery, action="recovery_approved", outcome="approved", reason_code="password_reset_token_verified")
    db.commit()
    return recovery


def complete_password_recovery(
    db: Session,
    *,
    token: str,
    new_password: str,
    request_id: str | None = None,
) -> AccountRecoveryRequest:
    if len(new_password) < 12 or len(new_password) > 256 or not new_password.strip():
        raise RecoveryError("PASSWORD_POLICY", "New password does not meet the minimum security policy", 422)

    token_digest = _digest(token)
    now = datetime.now(UTC)
    query = db.query(AccountRecoveryRequest).filter(
        AccountRecoveryRequest.operation == "password_reset",
        AccountRecoveryRequest.state == APPROVED,
    )
    if request_id:
        query = query.filter(AccountRecoveryRequest.request_id == request_id)
    else:
        query = query.filter(AccountRecoveryRequest.token_digest == token_digest)
    recovery = query.with_for_update().first()
    if recovery is None:
        raise RecoveryError("RECOVERY_VERIFICATION_REQUIRED", "Recovery verification is required before reset", 403)
    if not hmac.compare_digest(recovery.token_digest or "", token_digest):
        raise RecoveryError("INVALID_RECOVERY", "Invalid or expired recovery request")
    token_expires_at = _utc(recovery.token_expires_at)
    if token_expires_at is None or token_expires_at <= now:
        recovery.state = EXPIRED
        recovery.reason_code = "token_expired_before_completion"
        recovery.failed_at = now
        recovery.touch()
        _audit(db, recovery, action="recovery_completed", outcome="denied", reason_code="token_expired_before_completion")
        db.commit()
        raise RecoveryError("RECOVERY_EXPIRED", "Invalid or expired recovery request")

    account = _load_account(db, recovery.account_kind, recovery.account_id)
    if account is None or not getattr(account, "is_active", False):
        recovery.state = REJECTED
        recovery.reason_code = "account_not_recoverable"
        recovery.failed_at = now
        recovery.touch()
        _audit(db, recovery, action="recovery_rejected", outcome="denied", reason_code="account_not_recoverable")
        db.commit()
        raise RecoveryError("ACCOUNT_NOT_RECOVERABLE", "Account cannot be recovered", 403)

    account.password_hash = hash_password(new_password)
    if isinstance(account, LabUser):
        account.reset_token = None
        account.reset_token_expires = None

    # This is the revocation boundary: every existing access/refresh token with
    # the old permission version becomes invalid and re-authentication is needed.
    bump_perm_version(
        account,
        db,
        actor_id=account.id,
        actor_role=getattr(account, "role", None),
        reason="password_recovery_completed",
    )
    _audit(
        db,
        recovery,
        action="session_revoked",
        outcome="revoked",
        reason_code="password_recovery_completed",
    )
    recovery.state = RECOVERED
    recovery.reason_code = "password_reset_completed"
    recovery.recovered_at = now
    recovery.consumed_at = now
    recovery.token_digest = None
    recovery.touch()
    _audit(db, recovery, action="recovery_completed", outcome="recovered", reason_code="password_reset_completed")
    db.commit()
    return recovery
