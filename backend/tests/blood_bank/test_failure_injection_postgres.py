from __future__ import annotations

import os

import pytest

from app.blood_bank.infrastructure.models import BloodRequestModel, BloodReservationModel, BloodUnitModel, InventoryMovementModel
from app.blood_bank.domain.enums import ComponentStatus
from app.database import get_db
from app.main import app

from test_http_idempotency_postgres import _counts, _issue_counts, _payload, _prepare, _prepare_issue, _session_factory, _client

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


def test_issue_failure_after_business_effect_rolls_back_and_same_key_retry_succeeds() -> None:
    Session = _session_factory()
    request_id, unit_id = _prepare_issue(Session)
    key = "HTTP-ISSUE-FAIL-AFTER-EFFECT-001"
    body = {"request_id": request_id, "quantity": 1}
    os.environ["GULA_TEST_FAILURE_STAGE"] = "after_business_effect"
    try:
        with _client(Session) as client:
            first = client.post("/blood-bank/inventory/issue", headers={"Idempotency-Key": key, "If-Match": "1"}, json=body)
        os.environ.pop("GULA_TEST_FAILURE_STAGE", None)
        with _client(Session) as client:
            retry = client.post("/blood-bank/inventory/issue", headers={"Idempotency-Key": key, "If-Match": "1"}, json=body)
        assert first.status_code == 500
        assert retry.status_code == 200
        assert _issue_counts(Session, request_id, unit_id) == {"fulfilled_units": 1, "unit_status": ComponentStatus.ISSUED.value, "movements": 1}
    finally:
        os.environ.pop("GULA_TEST_FAILURE_STAGE", None)
        app.dependency_overrides.clear()
        Session.kw["bind"].dispose()
