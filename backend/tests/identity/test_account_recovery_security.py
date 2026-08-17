from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pytest
from app._compat import UTC
from app.models.account_recovery import AccountRecoveryRequest
from app.models.audit_log import AuditLog
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.security.recovery import (
    APPROVED,
    EXPIRED,
    LOCKED,
    PENDING_REVIEW,
    RECOVERED,
    REQUESTED,
    RecoveryError,
    complete_password_recovery,
    request_password_recovery,
    verify_password_recovery,
)

from shared.auth.passwords import hash_password, verify_password


def _lab_user(db: Any, email: str = "recovery@example.test") -> LabUser:
    lab = Lab(
        name="Recovery Test Lab",
        license_number=f"REC-{email}",
        lab_type="private",
        city="Baghdad",
        is_active=True,
    )
    db.add(lab)
    db.flush()
    user = LabUser(
        lab_id=lab.id,
        name="Recovery User",
        email=email,
        password_hash=hash_password("OldPassword123!"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


def test_unknown_email_is_enumeration_resistant(db: Any) -> None:
    recovery, raw_token = request_password_recovery(
        db,
        email="unknown@example.test",
        idempotency_key="unknown-key",
        requested_ip="127.0.0.1",
    )
    assert recovery is None
    assert raw_token is None
    assert db.query(AccountRecoveryRequest).count() == 0


def test_request_is_idempotent_and_raw_token_is_not_persisted(db: Any) -> None:
    user = _lab_user(db)
    first, raw_token = request_password_recovery(
        db,
        email=user.email,
        idempotency_key="same-key",
        requested_ip="127.0.0.1",
    )
    second, replayed_token = request_password_recovery(
        db,
        email=user.email,
        idempotency_key="same-key",
        requested_ip="127.0.0.1",
    )
    assert first is not None and raw_token
    assert second is not None
    assert second.request_id == first.request_id
    assert replayed_token is None
    assert first.token_digest != raw_token
    assert len(first.token_digest or "") == 64


def test_state_machine_verify_complete_replay_and_revocation(db: Any) -> None:
    user = _lab_user(db)
    old_perm_version = user.perm_version
    recovery, raw_token = request_password_recovery(
        db,
        email=user.email,
        idempotency_key="state-machine-key",
        requested_ip="127.0.0.1",
    )
    assert recovery is not None and raw_token

    recovery.state = "requested"
    db.commit()
    verified = verify_password_recovery(db, token=raw_token)
    assert verified.state == APPROVED
    completed = complete_password_recovery(
        db,
        token=raw_token,
        new_password="NewRecoveryPassword123!",
    )
    assert completed.state == RECOVERED
    db.refresh(user)
    assert user.perm_version == old_perm_version + 1
    assert verify_password("NewRecoveryPassword123!", user.password_hash)
    assert completed.token_digest is None

    with pytest.raises(RecoveryError) as replay:
        verify_password_recovery(db, token=raw_token)
    assert replay.value.code in {"INVALID_RECOVERY", "RECOVERY_NOT_ACTIVE"}


def test_expired_recovery_is_terminal(db: Any) -> None:
    user = _lab_user(db, email="expired@example.test")
    recovery, raw_token = request_password_recovery(
        db,
        email=user.email,
        idempotency_key="expired-key",
        requested_ip="127.0.0.1",
    )
    assert recovery is not None and raw_token
    recovery.token_expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()

    with pytest.raises(RecoveryError) as expired:
        verify_password_recovery(db, token=raw_token)
    assert expired.value.code == "RECOVERY_EXPIRED"
    db.refresh(recovery)
    assert recovery.state == EXPIRED


def test_verification_attempt_limit_locks_request(db: Any) -> None:
    user = _lab_user(db, email="locked@example.test")
    recovery, raw_token = request_password_recovery(
        db,
        email=user.email,
        idempotency_key="locked-key",
        requested_ip="127.0.0.1",
    )
    assert recovery is not None and raw_token
    recovery.token_digest = "a" * 64
    recovery.state = "requested"
    recovery.max_attempts = 3
    db.commit()

    for _ in range(3):
        with pytest.raises(RecoveryError):
            verify_password_recovery(db, token=raw_token, request_id=recovery.request_id)
    db.refresh(recovery)
    assert recovery.state == LOCKED


def test_pending_review_never_becomes_recovery_success(db: Any) -> None:
    user = _lab_user(db, email="review@example.test")
    recovery, raw_token = request_password_recovery(
        db,
        email=user.email,
        idempotency_key="review-key",
        requested_ip="127.0.0.1",
    )
    assert recovery is not None and raw_token
    recovery.state = PENDING_REVIEW
    db.commit()

    with pytest.raises(RecoveryError) as pending:
        verify_password_recovery(db, token=raw_token)
    assert pending.value.code == "RECOVERY_PENDING_REVIEW"
    db.refresh(recovery)
    assert recovery.state == PENDING_REVIEW


def test_http_verify_then_reset_is_single_use(client: Any, db: Any) -> None:
    user = _lab_user(db, email="http-recovery@example.test")
    recovery, raw_token = request_password_recovery(
        db,
        email=user.email,
        idempotency_key="http-key",
        requested_ip="127.0.0.1",
    )
    assert recovery is not None and raw_token
    verified = client.post(
        "/auth/recovery/verify",
        json={"token": raw_token, "request_id": recovery.request_id},
    )
    assert verified.status_code == 200, verified.text
    assert verified.json()["status"] == APPROVED
    reset = client.post(
        "/auth/reset-password",
        json={
            "token": raw_token,
            "request_id": recovery.request_id,
            "new_password": "HttpRecoveryPassword123!",
        },
    )
    assert reset.status_code == 200, reset.text
    events = db.query(AuditLog).filter(AuditLog.action == "session_revoked", AuditLog.resource_id == user.id).all()
    assert any("password_recovery_completed" in str(event.details) for event in events)
    replay = client.post(
        "/auth/reset-password",
        json={
            "token": raw_token,
            "request_id": recovery.request_id,
            "new_password": "AnotherRecoveryPassword123!",
        },
    )
    assert replay.status_code in (400, 403, 409)


def test_high_risk_security_recovery_is_pending_review_and_owner_scoped(client: Any, db: Any) -> None:
    user = _lab_user(db, email="manual-review@example.test")
    login = client.post("/login", json={"email": user.email, "password": "OldPassword123!"})
    assert login.status_code == 200, login.text
    token = login.cookies.get("access_token")
    assert token
    headers = {"Authorization": f"Bearer {token}"}
    requested = client.post(
        "/auth/security/recovery-request",
        json={"operation": "lost_device"},
        headers=headers,
    )
    assert requested.status_code == 200, requested.text
    body = requested.json()
    assert body["status"] == PENDING_REVIEW
    assert body["operation"] == "lost_device"
    assert body["request_id"]

    status = client.get(f"/auth/recovery/{body['request_id']}", headers=headers)
    assert status.status_code == 200, status.text
    assert status.json()["status"] == PENDING_REVIEW
    db.refresh(user)
    assert user.perm_version == 1


def test_cross_account_recovery_token_cannot_verify_other_request(db: Any) -> None:
    first = _lab_user(db, email="first-account@example.test")
    second = _lab_user(db, email="second-account@example.test")
    first_recovery, first_token = request_password_recovery(
        db,
        email=first.email,
        idempotency_key="first-account-key",
        requested_ip="127.0.0.1",
    )
    second_recovery, _ = request_password_recovery(
        db,
        email=second.email,
        idempotency_key="second-account-key",
        requested_ip="127.0.0.1",
    )
    assert first_recovery is not None and second_recovery is not None and first_token
    with pytest.raises(RecoveryError):
        verify_password_recovery(db, token=first_token, request_id=second_recovery.request_id)
    db.refresh(second_recovery)
    assert second_recovery.state == REQUESTED


def test_password_policy_is_enforced_before_mutation(db: Any) -> None:
    user = _lab_user(db, email="policy@example.test")
    recovery, raw_token = request_password_recovery(
        db,
        email=user.email,
        idempotency_key="policy-key",
        requested_ip="127.0.0.1",
    )
    assert recovery is not None and raw_token
    verify_password_recovery(db, token=raw_token)
    old_hash = user.password_hash
    with pytest.raises(RecoveryError) as policy:
        complete_password_recovery(db, token=raw_token, new_password="short")
    assert policy.value.code == "PASSWORD_POLICY"
    db.refresh(user)
    assert user.password_hash == old_hash
