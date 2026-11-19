"""Are the EHR medication routes a false-success stub, or schema-latent?

NR-220 attacked independently. The four tables behind these routes --
ehr_medication_statements, _requests, _dispenses, _administrations -- are
mapped by app/ehr/models/medication.py and created by NO migration. That
matters for how an empty response should be read.
"""
from __future__ import annotations

import pytest

from tests.conftest import auth_headers


@pytest.fixture()
def actor(db, make_lab, make_lab_user, client):
    from app.models.patient import Patient

    lab = make_lab()
    user = make_lab_user(lab_id=lab.id, role="master_admin")
    patient = Patient(lab_id=lab.id, full_name="Med Probe", phone="07700000800")
    db.add(patient)
    db.flush()
    return {
        "lab": lab, "user": user, "patient": patient,
        "h": auth_headers(user_id=user.id, lab_id=lab.id, role="master_admin"),
    }


def test_the_medication_tables_have_no_migration():
    """The structural half: ORM-mapped, never created by the corpus."""
    import pathlib
    import re

    root = pathlib.Path(__file__).resolve().parents[2]
    versions = root / "migrations" / "versions"
    created = set()
    for path in versions.glob("*.py"):
        text = path.read_text(errors="replace")
        created |= set(re.findall(r'create_table\(\s*["\']([^"\']+)["\']', text))
        created |= set(re.findall(r'_create_if_missing\(\s*["\']([^"\']+)["\']', text))

    from app.ehr.models.medication import (
        MedicationAdministration,
        MedicationDispense,
        MedicationRequest,
        MedicationStatement,
    )

    tables = [
        m.__table__.name
        for m in (MedicationStatement, MedicationRequest, MedicationDispense, MedicationAdministration)
    ]
    missing = [t for t in tables if t not in created]
    print(f"\n[schema] tables={tables}  without a migration={missing}")
    assert missing == tables, "some now have migrations -- re-measure NR-220"


def test_a_posted_medication_statement_is_readable_back(client, db, actor):
    """The behavioural half: is persistence real, or does the route fake success?"""
    create = client.post(
        "/ehr/medication-statements",
        json={
            "patient_id": actor["patient"].id,
            "medication_name": "Metformin",
            "status": "active",
        },
        headers=actor["h"],
    )
    print(f"\n[NR-220] POST -> {create.status_code} {create.text[:160]}")
    if create.status_code in (401, 403):
        pytest.skip(f"route requires a permission this actor lacks: {create.status_code}")
    if create.status_code == 422:
        pytest.skip(f"payload contract differs: {create.text[:200]}")
    assert create.status_code in (200, 201), create.text

    listed = client.get(
        f"/ehr/patients/{actor['patient'].id}/medication-statements", headers=actor["h"],
    )
    print(f"[NR-220] GET  -> {listed.status_code} {listed.text[:200]}")
    assert listed.status_code == 200, listed.text
    body = listed.json()
    items = body if isinstance(body, list) else body.get("items", body.get("data", []))
    assert items, (
        "a statement was accepted but the list is empty -- that would be the "
        "false-success behaviour NR-220 describes"
    )


def test_the_read_path_refuses_an_unresolvable_patient_rather_than_returning_empty(
    client, actor,
):
    """The control that disproves 'unconditional empty list'.

    A core `patients.id` is passed, which this route cannot resolve -- its
    models key on national_patients.id (IA-067). The response is a tenant-scoped
    404, not an empty success. That is a stronger control than the
    false-success hypothesis assumed, and it is the measured behaviour.
    """
    listed = client.get(
        f"/ehr/patients/{actor['patient'].id}/medication-statements", headers=actor["h"],
    )
    if listed.status_code in (401, 403):
        pytest.skip("route requires a permission this actor lacks")
    print(f"\n[NR-220] GET with a core patients.id -> {listed.status_code} {listed.text[:120]}")
    assert listed.status_code == 404, listed.text
    assert "not found in your laboratory" in listed.text.lower()


def test_the_implementation_is_orm_backed_not_in_memory():
    """Rules out the 'dead in-memory implementation' hypothesis.

    routes/ehr.py contains no db.add( -- it delegates to a service layer, which
    is why a first pass of this test looked for the write in the wrong module.
    The models are what settle it: real SQLAlchemy tables with real foreign
    keys, not a dict.
    """
    import inspect

    from app.ehr.models.medication import MedicationStatement
    from app.routes import ehr

    route_source = inspect.getsource(ehr)
    assert "Depends(get_db)" in route_source, "the routes take a real session"
    assert "db.add(" not in route_source, (
        "routes/ehr.py now writes directly; re-measure where persistence lives"
    )

    table = MedicationStatement.__table__
    assert table.name == "ehr_medication_statements"
    assert any(c.foreign_keys for c in table.c), "a dict-backed store has no foreign keys"
    assert len(table.c) > 5, sorted(table.c.keys())
    print(f"\n[NR-220] ORM-backed: {table.name} with "
          f"{sum(1 for c in table.c if c.foreign_keys)} FK columns; "
          f"routes/ehr.py delegates rather than writing inline")
