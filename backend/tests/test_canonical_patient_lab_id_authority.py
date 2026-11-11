"""NR-148 closure proof: POST /api/v1/canonical-patients no longer lets the
request body choose the canonical patient's lab_id.

This file used to PROVE the live bypass (an admin authenticated against Lab
A could freely name Lab B, or a nonexistent lab, as a canonical patient's
owner) and mark it BLOCKED pending an MPI-ownership decision, since fixing
it was explicitly reserved for Abu Ali. That decision has since landed
(fix(security): the Master Patient Index had no scope rule at all
(NR-148)) — lab_id is PROVENANCE, server-derived from the caller, never the
request body — and the same fix is ported onto this branch's copy in
backend/app/services/mpi/scope.py / backend/app/routes/canonical_patient.py.
This file now proves the closure at the HTTP layer; the deeper property set
(visibility, national-only actions, own-patient linking) is covered in
test_canonical_patient_scope.py.
"""
from __future__ import annotations

from tests.conftest import auth_headers


def test_lab_a_admin_cannot_assign_a_canonical_patient_to_lab_b(
    client, db, make_lab, make_lab_user
):
    lab_a = make_lab()
    lab_b = make_lab()
    admin_a = make_lab_user(lab_a.id, role="admin")
    db.commit()

    resp = client.post(
        "/api/v1/canonical-patients",
        json={"full_name": "Test Patient", "lab_id": lab_b.id},
        headers=auth_headers(admin_a.id, lab_a.id, role="admin"),
    )
    # The schema no longer even accepts lab_id (extra fields are dropped by
    # default pydantic config here, not rejected — the meaningful assertion
    # is the recorded value below, not the status code).
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["lab_id"] == lab_a.id, (
        "the created record's lab_id must be the caller's own lab "
        "(provenance), never the attacker-supplied lab_b.id from the body"
    )


def test_lab_a_admin_creating_a_canonical_patient_ignores_a_nonexistent_lab_id_in_the_body(
    client, db, make_lab, make_lab_user
):
    lab_a = make_lab()
    admin_a = make_lab_user(lab_a.id, role="admin")
    db.commit()

    resp = client.post(
        "/api/v1/canonical-patients",
        json={"full_name": "Test Patient 2", "lab_id": 999999},
        headers=auth_headers(admin_a.id, lab_a.id, role="admin"),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["lab_id"] == lab_a.id
