"""The LIMS result-release journey, driven end to end against real PostgreSQL.

WHY THIS JOURNEY
----------------
Releasing a laboratory result is the moment a number becomes clinical fact: it
leaves the laboratory and a clinician acts on it. `app/lims` serves 69 routes
and had five test modules, none of which drove this path. Two defects were
sitting in it, and both were invisible to every static check in the repository
because each needed the request to actually reach PostgreSQL.

DEFECT 1 -- EVERY LIMS MUTATION RETURNED 500
    `log_action(db, action, resource_type, resource_id, user_id, user_role,
    lab_id, details, ip_address)`. All four call sites in app/lims/services.py
    passed the description as the seventh positional argument, so it landed in
    `lab_id`. `audit_logs.lab_id` is an integer column, so PostgreSQL raised
    InvalidTextRepresentation and the mutation died with it:

        invalid input syntax for type integer:
        "LIMS order ACC-85c4dd63 created"

    Order creation, specimen registration, every specimen transition and result
    entry -- the whole LIMS write surface -- returned 500 on every call. And had
    it not crashed, the audit row would have carried no tenant at all.

    SQLite does not raise on this, which is why a suite that never touched
    PostgreSQL could not see it.

DEFECT 2 -- RELEASE WAS UNREACHABLE
    `release_result` required `specimen.status == "verified"` and then called
    `SpecimenService.transition(..., "released")`. state_machine.py, which calls
    itself the single source of truth, allows `verified -> validated` and
    `validated -> released`, so that transition was refused with 409 every time.
    The precondition and the transition contradicted each other and no release
    could ever complete. Resolved in the stricter direction: the specimen must
    be validated, which is one more control state before a result reaches a
    clinician, never one fewer.

WHAT IS PROVEN HERE
-------------------
Create -> validate -> authorize -> persist -> state transition -> audit ->
read back, plus the three refusals that matter: an unvalidated release, a
release by someone without senior authority, and a read from another
laboratory. Optimistic concurrency is exercised throughout rather than
asserted separately -- every mutating call carries If-Match, and the journey
only advances because the server's version answers match.

Skipped, never passed, when PostgreSQL is absent: the defects above are
PostgreSQL type semantics, so a SQLite run would prove nothing.
"""

from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

POSTGRES_URL = os.getenv("LIMS_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL, reason="LIMS_POSTGRES_URL is not configured",
)

SUFFIX = uuid.uuid4().hex[:8]

#: The specimen lifecycle from state_machine.py, walked in full. Skipping a
#: state is what defect 2 amounted to, so the journey never shortcuts one.
LIFECYCLE = ("registered", "collected", "received", "accepted",
             "analyzing", "analyzed", "verified")


@pytest.fixture(scope="module")
def journey():
    """Two laboratories, a senior and a junior user in each, and one app.

    The release policy is fail-closed by design and denies every capability
    unless the deployment enables it. Enabling it here is the point: a denied
    capability would answer a different question than the one this module asks.
    """
    os.environ.update({
        "GULA_RELEASE_ENABLED_CAPABILITIES": ",".join((
            "phase1.lims.orders", "phase1.lims.sample_tracking",
            "phase1.lims.result_entry", "phase1.lims.result_approval",
        )),
    })
    from app.database import get_db
    from app.factory import create_app
    from app.models.lab import Lab
    from app.models.lab_order import LabOrder
    from app.models.lab_user import LabUser
    from app.models.patient import Patient
    from app.models.subscription import LabSubscription
    from app.security.auth import create_token, hash_password
    from fastapi.testclient import TestClient

    engine = create_engine(POSTGRES_URL, future=True)
    SessionLocal = sessionmaker(bind=engine, future=True)

    ids: dict[str, dict] = {}
    with Session(engine) as db:
        for tag in ("a", "b"):
            lab = Lab(name=f"LIMS Journey {tag}{SUFFIX}", license_number=f"LJ-{tag}{SUFFIX}",
                      lab_type="private", city="Baghdad", is_active=True)
            db.add(lab)
            db.flush()
            db.add(LabSubscription(lab_id=lab.id, tier="enterprise", deployment_mode="single",
                                   security_level="standard", is_active=True))
            senior = LabUser(lab_id=lab.id, email=f"sen_{tag}{SUFFIX}@t.local", name="Senior",
                             password_hash=hash_password("Pw1!aaaa"), role="lab_admin",
                             is_active=True)
            junior = LabUser(lab_id=lab.id, email=f"jun_{tag}{SUFFIX}@t.local", name="Junior",
                             password_hash=hash_password("Pw1!aaaa"), role="lab_technician",
                             is_active=True)
            db.add_all([senior, junior])
            db.flush()
            patient = Patient(lab_id=lab.id, full_name=f"Journey Patient {tag}{SUFFIX}",
                              phone="07700001" + ("11" if tag == "a" else "22"),
                              gender="M")
            db.add(patient)
            db.flush()
            order = LabOrder(lab_id=lab.id, patient_id=patient.id)
            db.add(order)
            db.flush()
            ids[tag] = {"lab": lab.id, "senior": senior.id, "junior": junior.id,
                        "order": order.id}
        db.commit()

    # Tenant approval is part of the same fail-closed policy and is read from the
    # environment at request time, so it can only be set once the labs exist.
    os.environ["GULA_RELEASE_APPROVED_TENANT_IDS"] = f"{ids['a']['lab']},{ids['b']['lab']}"

    app = create_app()

    def _db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    # conftest pins DATABASE_URL to in-memory SQLite before any module fixture
    # runs, and app.database builds its engine at import. Overriding the
    # dependency is the seam conftest itself uses, pointed at PostgreSQL.
    app.dependency_overrides[get_db] = _db

    def headers(tag: str, who: str, role: str) -> dict:
        return {"Authorization": "Bearer " + create_token(
            {"user_id": ids[tag][who], "lab_id": ids[tag]["lab"], "role": role})}

    with TestClient(app, raise_server_exceptions=False) as client:
        yield {
            "client": client,
            "ids": ids,
            "engine": engine,
            "senior_a": headers("a", "senior", "lab_admin"),
            "junior_a": headers("a", "junior", "lab_technician"),
            "senior_b": headers("b", "senior", "lab_admin"),
        }
    engine.dispose()


@pytest.fixture(scope="module")
def released(journey):
    """Walk the whole journey once and hand every step's outcome to the tests.

    One walk rather than one per assertion: each step depends on the state the
    previous one left, and re-running it per test would multiply PostgreSQL
    round trips without testing anything new.
    """
    client, ids = journey["client"], journey["ids"]
    senior, junior = journey["senior_a"], journey["junior_a"]
    out: dict[str, object] = {}

    def cmd(headers, version, key):
        return {**headers, "If-Match": str(version), "Idempotency-Key": f"{key}-{SUFFIX}"}

    order = client.post("/lims/orders", headers=senior, json={
        "order_id": ids["a"]["order"], "accession_number": f"ACC-{SUFFIX}",
        "priority": "routine"})
    out["order"] = order

    specimen = client.post("/lims/specimens", headers=senior, json={
        "order_id": ids["a"]["order"], "specimen_type": "serum",
        "barcode": f"BC{SUFFIX}"})
    out["specimen"] = specimen
    if specimen.status_code >= 300:
        out["transitions"] = []
        return out
    specimen_id = specimen.json()["id"]
    version = specimen.json()["version"]

    transitions = []
    for step, target in enumerate(LIFECYCLE):
        response = client.put(f"/lims/specimens/{specimen_id}/status",
                              headers=cmd(senior, version, f"sp{step}"),
                              json={"target_status": target})
        transitions.append((target, response))
        if response.status_code >= 300:
            break
        version = response.json()["version"]
    out["transitions"] = transitions

    result = client.post("/lims/results", headers=cmd(senior, version, "res"), json={
        "specimen_id": specimen_id, "test_code": "GLU", "test_name": "Glucose",
        "value_numeric": 5.4, "unit": "mmol/L"})
    out["result"] = result
    if result.status_code >= 300:
        return out
    result_id = result.json()["id"]
    result_version = result.json()["version"]
    out["result_id"] = result_id

    # Before any validation -- this must be refused.
    out["premature_release"] = client.post(
        f"/lims/results/{result_id}/release", headers=cmd(senior, result_version, "early"))

    validated = client.post(f"/lims/results/{result_id}/validate",
                            headers=cmd(senior, result_version, "val"),
                            json={"action": "validate", "signature_hash": f"sig-{SUFFIX}",
                                  "notes": "within reference range"})
    out["validate"] = validated
    if validated.status_code < 300:
        result_version = validated.json()["version"]

    specimen_validated = client.put(f"/lims/specimens/{specimen_id}/status",
                                    headers=cmd(senior, version, "spval"),
                                    json={"target_status": "validated"})
    out["specimen_validated"] = specimen_validated
    if specimen_validated.status_code < 300:
        version = specimen_validated.json()["version"]

    out["junior_release"] = client.post(
        f"/lims/results/{result_id}/release", headers=cmd(junior, result_version, "jun"))
    out["senior_release"] = client.post(
        f"/lims/results/{result_id}/release", headers=cmd(senior, result_version, "sen"))
    out["read_own"] = client.get(f"/lims/results/{result_id}/fhir", headers=senior)
    out["read_other_lab"] = client.get(f"/lims/results/{result_id}/fhir",
                                       headers=journey["senior_b"])
    return out


def test_a_the_write_surface_persists(released):
    """Defect 1. Every one of these returned 500 on PostgreSQL.

    This is the positive control for the whole module as well as a finding in
    its own right: if creation does not work, every refusal below would be
    satisfied for the wrong reason.
    """
    assert released["order"].status_code == 201, (
        f"POST /lims/orders: {released['order'].status_code} "
        f"{released['order'].text[:300]}")
    assert released["specimen"].status_code == 201, (
        f"POST /lims/specimens: {released['specimen'].status_code} "
        f"{released['specimen'].text[:300]}")
    assert released["result"].status_code == 201, (
        f"POST /lims/results: {released['result'].status_code} "
        f"{released['result'].text[:300]}")


def test_b_the_whole_declared_lifecycle_is_walkable(released):
    """Every state in state_machine.py's specimen lifecycle, in order."""
    assert len(released["transitions"]) == len(LIFECYCLE), (
        "the specimen lifecycle stopped early: "
        f"{[(t, r.status_code) for t, r in released['transitions']]}")
    for target, response in released["transitions"]:
        assert response.status_code == 200, (
            f"transition to {target}: {response.status_code} {response.text[:200]}")


def test_c_the_audit_row_carries_the_tenant(released, journey):
    """Defect 1's quieter half.

    The crash is the loud symptom; the silent one is an audit row with no
    laboratory on it. Security Invariant 2 requires the mutation to be audited,
    and an audit row that cannot say which tenant acted is not an audit row.
    """
    with journey["engine"].connect() as conn:
        rows = conn.execute(text(
            "SELECT lab_id, resource_type, details FROM audit_logs "
            "WHERE resource_type LIKE 'lims_%' AND lab_id = :lab "
            "ORDER BY id DESC LIMIT 20"
        ), {"lab": journey["ids"]["a"]["lab"]}).fetchall()

    assert rows, "no LIMS audit row carried this laboratory's id"
    assert all(row.lab_id == journey["ids"]["a"]["lab"] for row in rows)
    assert any(row.details for row in rows), (
        "every audit row has empty details -- the description is going "
        "somewhere other than the details column")


def test_d_an_unvalidated_result_cannot_be_released(released):
    """Clinical safety. A number a clinician acts on must have been validated."""
    response = released["premature_release"]
    assert response.status_code == 422, (
        f"an unvalidated result released with {response.status_code}: "
        f"{response.text[:300]}")


def test_e_release_requires_senior_authority(released):
    """Authorization, decided by the server from the token's role."""
    assert released["junior_release"].status_code == 403, (
        f"a lab_technician released a result: "
        f"{released['junior_release'].status_code} "
        f"{released['junior_release'].text[:300]}")


def test_f_a_senior_can_complete_the_release(released):
    """Defect 2. This could never return 200 before the precondition was fixed."""
    assert released["validate"].status_code == 200, (
        f"validate: {released['validate'].status_code} "
        f"{released['validate'].text[:300]}")
    assert released["specimen_validated"].status_code == 200, (
        f"specimen -> validated: {released['specimen_validated'].status_code} "
        f"{released['specimen_validated'].text[:300]}")
    assert released["senior_release"].status_code == 200, (
        f"release: {released['senior_release'].status_code} "
        f"{released['senior_release'].text[:300]}")


def test_g_the_released_result_reads_back(released):
    """The journey's point: the result is retrievable as FHIR afterwards."""
    response = released["read_own"]
    assert response.status_code == 200, response.text[:300]
    body = response.json()
    assert body["resourceType"] == "Observation"
    assert body["code"]["coding"][0]["code"] == "GLU", (
        "the read-back returned an Observation for a different test")


def test_h_another_laboratory_cannot_read_it(released):
    """Tenant isolation, at the end of the journey rather than in the abstract."""
    assert released["read_other_lab"].status_code == 404, (
        f"another laboratory read this result: "
        f"{released['read_other_lab'].status_code} "
        f"{released['read_other_lab'].text[:300]}")
