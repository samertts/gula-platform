"""NR-144 — the clinician who verified a result is the caller, not a field.

`PUT /v1/test-results/{id}/verify` is the attestation step: it moves a result to
`verified` and records WHO stood behind it. That name arrived in the request
body:

    row.verified_by = payload.verified_by

So the record of who attested a clinical result was whatever string the client
chose to send. It is the same defect NR-128 closed for `lab_id` a few lines
above in the same module -- a client-authored identity written into the
clinical record -- and the sweep that found it (NR-142) found it by asking the
same question of every remaining tree.

These tests exercise the control with a caller supplied through the trusted
context, and assert the unreachable case separately at the end: an endpoint
that 503s proves nothing about whether its attestation is correct.
"""
from __future__ import annotations

import uuid

import pytest
from app.api.v1.test_results import router as results_router
from app.core.database import get_db
from app.core.trusted_context import (
    TrustedContext,
    publish,
    require_trusted_context,
)
from app.models.audit_log import AuditLog
from app.models.lab import Lab, LabType

# Aliased: pytest tries to collect any imported name starting with "Test".
from app.models.test_result import ResultStatus
from app.models.test_result import TestResult as TestResultRow
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

LAB = uuid.uuid4()
HEALTH_ID = "HID-NR144-001"
VERIFIER = "dr-kareem-7"
IMPOSTOR = "prof-someone-important"


def _as(client, actor_id: str, *, role: str = "LAB") -> None:
    def _provider(request: Request) -> TrustedContext:
        return publish(
            request,
            TrustedContext(actor_id=actor_id, role=role, lab_id=str(LAB)),
        )
    client.app.dependency_overrides[require_trusted_context] = _provider


@pytest.fixture()
def seed(session_factory, db_session, make_citizen, make_lab, make_result):
    db_session.add(Lab(id=LAB, name="Verifying Lab", license_number=f"LIC-{LAB.hex[:8]}",
                       lab_type=LabType.private, province="Baghdad", is_active=True))
    citizen = make_citizen(db_session, health_id=HEALTH_ID)
    db_session.commit()
    return make_result(db_session, citizen_id=citizen.id, lab_id=LAB)


@pytest.fixture()
def client(session_factory, seed):
    app = FastAPI()
    app.include_router(results_router, prefix="/v1",
                       dependencies=[Depends(require_trusted_context)])

    def _override():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override
    c = TestClient(app)
    _as(c, VERIFIER)
    return c


def _row(session_factory, result_id):
    session = session_factory()
    try:
        return session.get(TestResultRow, result_id)
    finally:
        session.close()


# ─── positive ───────────────────────────────────────────────────────────────

def test_a_a_caller_may_verify_and_is_recorded_as_the_verifier(client, seed, session_factory):
    """Positive control. Without it, every assertion below could be a refusal of everything."""
    response = client.put(f"/v1/test-results/{seed.id}/verify")
    assert response.status_code == 200, response.text
    assert response.json()["verified_by"] == VERIFIER

    row = _row(session_factory, seed.id)
    assert row.status == ResultStatus.verified
    assert row.verified_by == VERIFIER
    assert row.verified_at is not None


def test_b_verification_needs_no_request_body_at_all(client, seed):
    """The caller has nothing left to say, so the endpoint takes nothing."""
    assert client.put(f"/v1/test-results/{seed.id}/verify").status_code == 200


# ─── negative ───────────────────────────────────────────────────────────────

def test_c_a_body_naming_another_verifier_is_not_believed(client, seed, session_factory):
    """The old request shape, replayed. It must not reach the record."""
    response = client.put(f"/v1/test-results/{seed.id}/verify",
                          json={"verified_by": IMPOSTOR})
    assert response.status_code == 200, response.text
    assert response.json()["verified_by"] == VERIFIER

    row = _row(session_factory, seed.id)
    assert row.verified_by == VERIFIER
    assert row.verified_by != IMPOSTOR


def test_d_forged_identity_headers_confer_nothing(client, seed, session_factory):
    forged = {
        "X-Role": "MINISTRY", "X-Actor-Id": IMPOSTOR,
        "X-Actor-Role": "MINISTRY", "X-Lab-Id": str(uuid.uuid4()),
    }
    response = client.put(f"/v1/test-results/{seed.id}/verify", headers=forged)
    assert response.status_code == 200, response.text
    assert _row(session_factory, seed.id).verified_by == VERIFIER


def test_e_the_audit_row_records_the_derived_verifier(client, seed, session_factory):
    client.put(f"/v1/test-results/{seed.id}/verify", json={"verified_by": IMPOSTOR})

    session = session_factory()
    try:
        entries = [a for a in session.query(AuditLog).all()
                   if a.action == "test_result.verify"]
    finally:
        session.close()

    assert len(entries) == 1, "verification must leave exactly one audit row"
    entry = entries[0]
    assert entry.actor_id == VERIFIER
    assert entry.metadata_json["verified_by"] == VERIFIER
    assert IMPOSTOR not in str(entry.metadata_json)


def test_f_a_denied_second_verification_does_not_rewrite_the_verifier(
    client, seed, session_factory
):
    assert client.put(f"/v1/test-results/{seed.id}/verify").status_code == 200

    _as(client, IMPOSTOR)
    response = client.put(f"/v1/test-results/{seed.id}/verify",
                          json={"verified_by": IMPOSTOR})
    assert response.status_code == 409, response.text

    row = _row(session_factory, seed.id)
    assert row.verified_by == VERIFIER, "a refused verification rewrote the record"


# ─── (H) unreachable is not the same as authorized ──────────────────────────

def test_g_unreachable_is_not_the_same_as_correct(seed, session_factory):
    """The served router has no identity provider, so it 503s.

    Asserted on its own, and never as a substitute for the assertions above:
    a control that is never reached is a control that was never tested.
    """
    from app.main import app as served_app

    def _override():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    served_app.dependency_overrides[get_db] = _override
    try:
        response = TestClient(served_app).put(f"/v1/test-results/{seed.id}/verify")
    finally:
        served_app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 503, response.text
    assert _row(session_factory, seed.id).verified_by is None
