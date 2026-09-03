from __future__ import annotations

import os

import pytest

from app.blood_bank.infrastructure.models import BloodReservationModel
from app.database import get_db
from app.main import app

from test_http_idempotency_postgres import _counts, _payload, _prepare, _session_factory, _client

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
