from __future__ import annotations

import os

import pytest

from app.blood_bank.infrastructure.models import BloodRequestModel, BloodReservationModel, BloodUnitModel, InventoryMovementModel
from app.blood_bank.domain.enums import ComponentStatus
from app.database import get_db
from app.main import app

from test_http_idempotency_postgres import _claims, _counts, _issue_counts, _payload, _prepare, _prepare_issue, _session_factory, _client, LAB_ID

POSTGRES_URL = os.getenv("BLOOD_BANK_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="BLOOD_BANK_POSTGRES_URL is not configured")


def _run_failure_retry(stage: str, key: str) -> tuple[int, int, dict[str, object]]:
    Session = _session_factory()
    _prepare(Session)
    os.environ["GULA_TEST_FAILURE_STAGE"] = stage
    try:
        with _client(Session) as client:
            first = client.post("/blood-bank/reservations", headers={"Idempotency-Key": key}, json=_payload())
        os.environ.pop("GULA_TEST_FAILURE_STAGE", None)
        with _client(Session) as client:
            retry = client.post("/blood-bank/reservations", headers={"Idempotency-Key": key}, json=_payload())
        counts = _counts(Session)
        # The rolled-back claim leaves no orphan; the retry owns the only receipt.
        receipts = _claims(Session, "blood.reservation.create", key)
        assert len(receipts) == 1
        assert receipts[0][0] == "completed"
        return first.status_code, retry.status_code, counts
    finally:
        os.environ.pop("GULA_TEST_FAILURE_STAGE", None)
        app.dependency_overrides.clear()
        with Session() as session:
            session.query(BloodReservationModel).filter(BloodReservationModel.lab_id == 991010).delete(synchronize_session=False)
            session.commit()
        Session.kw["bind"].dispose()


def test_failure_after_claim_rolls_back_and_same_key_retry_succeeds() -> None:
    first, retry, counts = _run_failure_retry("after_claim", "HTTP-FAIL-AFTER-CLAIM-001")
    assert first == 500
    assert retry == 201
    assert counts == {"reservations": 1, "movements": 1, "unit_status": "reserved"}


def test_failure_after_business_effect_rolls_back_and_same_key_retry_succeeds() -> None:
    first, retry, counts = _run_failure_retry("after_business_effect", "HTTP-FAIL-AFTER-EFFECT-001")
    assert first == 500
    assert retry == 201
    assert counts == {"reservations": 1, "movements": 1, "unit_status": "reserved"}


def test_failure_after_inventory_movement_rolls_back_and_same_key_retry_succeeds() -> None:
    first, retry, counts = _run_failure_retry("after_inventory_movement", "HTTP-FAIL-AFTER-MOVEMENT-001")
    assert first == 500
    assert retry == 201
    assert counts == {"reservations": 1, "movements": 1, "unit_status": "reserved"}


def test_failure_after_audit_preparation_rolls_back_and_same_key_retry_succeeds() -> None:
    first, retry, counts = _run_failure_retry("after_audit_preparation", "HTTP-FAIL-AFTER-AUDIT-001")
    assert first == 500
    assert retry == 201
    assert counts == {"reservations": 1, "movements": 1, "unit_status": "reserved"}


def _run_issue_failure(stage: str, key: str) -> None:
    Session = _session_factory()
    request_id, unit_id = _prepare_issue(Session)
    body = {"request_id": request_id, "quantity": 1}
    os.environ["GULA_TEST_FAILURE_STAGE"] = stage
    try:
        with _client(Session) as client:
            first = client.post("/blood-bank/inventory/issue", headers={"Idempotency-Key": key, "If-Match": "1"}, json=body)
        os.environ.pop("GULA_TEST_FAILURE_STAGE", None)
        with _client(Session) as client:
            retry = client.post("/blood-bank/inventory/issue", headers={"Idempotency-Key": key, "If-Match": "1"}, json=body)
        assert first.status_code == 500
        assert retry.status_code == 200
        assert _issue_counts(Session, request_id, unit_id) == {"fulfilled_units": 1, "unit_status": ComponentStatus.ISSUED.value, "movements": 1}
        receipts = _claims(Session, "blood.issue", key)
        assert len(receipts) == 1
        assert receipts[0][0] == "completed"
    finally:
        os.environ.pop("GULA_TEST_FAILURE_STAGE", None)
        app.dependency_overrides.clear()
        Session.kw["bind"].dispose()


def test_issue_failure_after_business_effect_rolls_back_and_same_key_retry_succeeds() -> None:
    _run_issue_failure("after_business_effect", "HTTP-ISSUE-FAIL-AFTER-EFFECT-001")


def test_issue_failure_after_inventory_movement_rolls_back_and_same_key_retry_succeeds() -> None:
    _run_issue_failure("after_inventory_movement", "HTTP-ISSUE-FAIL-AFTER-MOVEMENT-001")


def test_issue_failure_after_audit_preparation_rolls_back_and_same_key_retry_succeeds() -> None:
    _run_issue_failure("after_audit_preparation", "HTTP-ISSUE-FAIL-AFTER-AUDIT-001")


# ---- Phase 14C: failure after the business transaction commits ----
#
# The commit succeeded but the client never saw the response.  A same-key retry
# must replay the canonical conflict, never repeat the clinical effect.


def test_reservation_failure_after_commit_retry_does_not_duplicate() -> None:
    Session = _session_factory()
    _prepare(Session)
    key = "HTTP-FAIL-AFTER-COMMIT-001"
    os.environ["GULA_TEST_FAILURE_STAGE"] = "after_commit"
    try:
        with _client(Session) as client:
            first = client.post("/blood-bank/reservations", headers={"Idempotency-Key": key}, json=_payload())
        os.environ.pop("GULA_TEST_FAILURE_STAGE", None)
        # The effect is durably committed even though the client saw a failure.
        assert first.status_code == 500
        assert _counts(Session) == {"reservations": 1, "movements": 1, "unit_status": ComponentStatus.RESERVED.value}
        committed = _claims(Session, "blood.reservation.create", key)
        assert len(committed) == 1
        assert committed[0][0] == "completed"

        with _client(Session) as client:
            retry = client.post("/blood-bank/reservations", headers={"Idempotency-Key": key}, json=_payload())
        # Canonical replay behaviour, and no second effect of any kind.
        assert retry.status_code == 409
        assert retry.json()["code"] == "CONFLICT"
        assert _counts(Session) == {"reservations": 1, "movements": 1, "unit_status": ComponentStatus.RESERVED.value}
        after = _claims(Session, "blood.reservation.create", key)
        assert len(after) == 1
        assert after[0][0] == "completed"
        assert after[0][1] == committed[0][1]
        with Session() as session:
            assert session.query(BloodReservationModel).filter(BloodReservationModel.lab_id == LAB_ID).count() == 1
            assert session.query(InventoryMovementModel).filter(InventoryMovementModel.lab_id == LAB_ID, InventoryMovementModel.movement_type == "reserved").count() == 1
    finally:
        os.environ.pop("GULA_TEST_FAILURE_STAGE", None)
        app.dependency_overrides.clear()
        Session.kw["bind"].dispose()


def test_issue_failure_after_commit_retry_does_not_duplicate() -> None:
    Session = _session_factory()
    request_id, unit_id = _prepare_issue(Session)
    key = "HTTP-ISSUE-FAIL-AFTER-COMMIT-001"
    body = {"request_id": request_id, "quantity": 1}
    expected = {"fulfilled_units": 1, "unit_status": ComponentStatus.ISSUED.value, "movements": 1}
    os.environ["GULA_TEST_FAILURE_STAGE"] = "after_commit"
    try:
        with _client(Session) as client:
            first = client.post("/blood-bank/inventory/issue", headers={"Idempotency-Key": key, "If-Match": "1"}, json=body)
        os.environ.pop("GULA_TEST_FAILURE_STAGE", None)
        assert first.status_code == 500
        assert _issue_counts(Session, request_id, unit_id) == expected
        committed = _claims(Session, "blood.issue", key)
        assert len(committed) == 1
        assert committed[0][0] == "completed"

        with _client(Session) as client:
            retry = client.post("/blood-bank/inventory/issue", headers={"Idempotency-Key": key, "If-Match": "1"}, json=body)
        assert retry.status_code == 409
        assert retry.json()["code"] == "CONFLICT"
        assert _issue_counts(Session, request_id, unit_id) == expected
        after = _claims(Session, "blood.issue", key)
        assert len(after) == 1
        assert after[0][0] == "completed"
        assert after[0][1] == committed[0][1]
        with Session() as session:
            assert session.query(BloodUnitModel).filter(BloodUnitModel.lab_id == LAB_ID, BloodUnitModel.status == ComponentStatus.ISSUED.value).count() == 1
    finally:
        os.environ.pop("GULA_TEST_FAILURE_STAGE", None)
        app.dependency_overrides.clear()
        Session.kw["bind"].dispose()
