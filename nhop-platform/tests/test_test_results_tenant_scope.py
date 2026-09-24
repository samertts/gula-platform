"""NR-092/F2 — a laboratory may only file results in its own name.

create_test_result took lab_id from the request BODY and checked only that such
a lab existed and was active. Nothing established that the caller WAS that
laboratory, so a result could be filed against any real lab, for any citizen,
and would be indistinguishable downstream from a genuine one.

These tests exercise the CONTROL, with a caller supplied through the trusted
context. They deliberately do not settle for the router's 503: an endpoint that
is unreachable proves nothing about whether its authorization is correct, and
the two states are asserted separately at the end of this module.
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
from app.models.lab import Lab, LabType

# Aliased: pytest tries to collect any imported name starting with "Test".
from app.models.test_result import TestResult as TestResultRow
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

OWN_LAB = uuid.uuid4()
OTHER_LAB = uuid.uuid4()
HEALTH_ID = "HID-F2-001"


def _as(client, role: str, *, lab_id=None, actor_id="lab-operator-1") -> None:
    def _provider(request: Request) -> TrustedContext:
        return publish(
            request,
            TrustedContext(actor_id=actor_id, role=role,
                           lab_id=str(lab_id) if lab_id else None),
        )
    client.app.dependency_overrides[require_trusted_context] = _provider


@pytest.fixture()
def client(session_factory, db_session, make_citizen):
    for lab_id, name in ((OWN_LAB, "Own Lab"), (OTHER_LAB, "Other Lab")):
        db_session.add(Lab(id=lab_id, name=name, license_number=f"LIC-{lab_id.hex[:8]}",
                           lab_type=LabType.private, province="Baghdad", is_active=True))
    make_citizen(db_session, health_id=HEALTH_ID)
    db_session.commit()

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
    client = TestClient(app)
    _as(client, "LAB", lab_id=OWN_LAB)
    return client


def _payload(lab_id, *, barcode=None):
    return {
        "health_id": HEALTH_ID,
        "lab_id": str(lab_id),
        "sample_barcode": barcode or uuid.uuid4().hex[:12].upper(),
        "test_code": "HGB",
        "test_name": "Haemoglobin",
        "category": "hematology",
        "value_numeric": 14.0,
        "unit": "g/dL",
        "reference_min": 12.0,
        "reference_max": 16.0,
    }


def test_a_a_lab_may_file_a_result_in_its_own_name(client):
    """Positive control. Without it, every denial below could be a denial of everything."""
    response = client.post("/v1/test-results/", json=_payload(OWN_LAB))
    assert response.status_code == 201, response.text


def test_b_a_lab_may_not_file_a_result_in_another_labs_name(client, db_session):
    response = client.post("/v1/test-results/", json=_payload(OTHER_LAB))
    assert response.status_code == 403, response.text


def test_c_a_forged_body_lab_id_does_not_move_the_caller(client):
    """The body names the RESOURCE; it never names the tenant."""
    assert client.post("/v1/test-results/", json=_payload(OTHER_LAB)).status_code == 403


def test_d_forged_identity_headers_confer_nothing(client):
    forged = {
        "X-Role": "MINISTRY", "X-Actor-Role": "MINISTRY", "X-Actor-Id": "impostor",
        "X-Lab-Id": str(OTHER_LAB), "X-Organization-Id": str(OTHER_LAB),
    }
    response = client.post("/v1/test-results/", json=_payload(OTHER_LAB), headers=forged)
    assert response.status_code == 403, response.text


def test_e_a_caller_carrying_no_laboratory_matches_nothing(client):
    """`None == None` is not "the same lab"."""
    _as(client, "LAB", lab_id=None)
    assert client.post("/v1/test-results/", json=_payload(OTHER_LAB)).status_code == 403
    assert client.post("/v1/test-results/", json=_payload(OWN_LAB)).status_code == 403


def test_e2_a_national_role_keeps_its_existing_reach(client):
    """The control must not narrow authority that was legitimately national."""
    _as(client, "MINISTRY", lab_id=None, actor_id="ministry-1")
    assert client.post("/v1/test-results/", json=_payload(OTHER_LAB)).status_code == 201


def test_f_a_denied_request_writes_no_result(client, db_session):
    before = db_session.query(TestResultRow).filter(TestResultRow.lab_id == OTHER_LAB).count()
    assert client.post("/v1/test-results/", json=_payload(OTHER_LAB)).status_code == 403
    db_session.expire_all()
    after = db_session.query(TestResultRow).filter(TestResultRow.lab_id == OTHER_LAB).count()
    assert after == before == 0, "a refused request must leave the target tenant untouched"


def test_g_a_denial_is_not_recorded_as_a_successful_mutation(client, db_session):
    """No audit row may claim a result was filed when none was."""
    from app.models.audit_log import AuditLog

    before = db_session.query(AuditLog).count()
    assert client.post("/v1/test-results/", json=_payload(OTHER_LAB)).status_code == 403
    db_session.expire_all()
    rows = db_session.query(AuditLog).offset(before).all()
    claimed = [r for r in rows if "creat" in str(getattr(r, "action", "")).lower()]
    assert claimed == [], f"a refused write was logged as a creation: {claimed}"


def test_h_unreachable_is_not_the_same_as_authorized(session_factory):
    """The two states this finding must never be allowed to conflate.

    Mounted the way production mounts it, with no identity provider federated,
    the route answers 503 -- it is unavailable. That says nothing about whether
    its tenant check is correct, which is what every test above measures. Both
    facts are recorded here so neither can stand in for the other.
    """
    app = FastAPI()
    app.include_router(results_router, prefix="/v1",
                       dependencies=[Depends(require_trusted_context)])
    unreachable = TestClient(app)
    assert unreachable.post("/v1/test-results/", json=_payload(OWN_LAB)).status_code == 503
