"""Independent proof for NR-148 (Abu Ali's negative register): POST
/api/v1/canonical-patients lets the request body choose the canonical
patient's lab_id, with no server-side correction against the caller's own
lab. Unlike the care_continuum finding, this surface IS built by a real
migration (20260716_0016_canonical_patient_unification.py), so this is a
live bypass, not a latent one.

Per this pass's explicit instruction, this file does NOT fix the endpoint:
MPI/canonical-patient semantics belong to Abu Ali (NR-148 is open on his own
branch too, precisely because it isn't obvious what "correct" looks like
here — CanonicalPatient.lab_id is nullable with ondelete=SET NULL, so a
canonical/MPI record may legitimately be lab-agnostic; whether it should
ALSO be force-set to the creating caller's own lab, or left as a
genuinely cross-lab-shared identity record, is a product/architecture
decision this pass is not authorized to make). This file only proves the
bypass is real and pins it as a regression guard until that decision is
made.
"""
from __future__ import annotations

from tests.conftest import auth_headers


def test_lab_a_admin_can_assign_a_canonical_patient_to_lab_b(
    client, db, make_lab, make_lab_user
):
    """Live P0/P1 candidate, NOT fixed here — see module docstring.

    An admin authenticated against Lab A creates a canonical patient and
    freely names Lab B (a lab they have no relationship to) as its owner
    via the request body. Nothing on the server side corrects this to the
    caller's own lab_id, or requires it to be null.
    """
    lab_a = make_lab()
    lab_b = make_lab()
    admin_a = make_lab_user(lab_a.id, role="admin")
    db.commit()

    resp = client.post(
        "/api/v1/canonical-patients",
        json={"full_name": "Test Patient", "lab_id": lab_b.id},
        headers=auth_headers(admin_a.id, lab_a.id, role="admin"),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["lab_id"] == lab_b.id, (
        "confirms the body's lab_id was honored verbatim, not corrected to "
        "the caller's own lab or rejected — see module docstring: this is "
        "NR-148, open and NOT fixed here pending an MPI-ownership decision"
    )


def test_lab_a_admin_can_assign_a_canonical_patient_to_a_lab_that_does_not_exist(
    client, db, make_lab, make_lab_user
):
    """Same gap, sharper: the body's lab_id is not even checked for
    existence — only the SQL FK (ondelete=SET NULL) stands in the way, and
    that only prevents an invalid *foreign key*, not an unauthorized valid
    one."""
    lab_a = make_lab()
    admin_a = make_lab_user(lab_a.id, role="admin")
    db.commit()
    nonexistent_lab_id = 999999

    resp = client.post(
        "/api/v1/canonical-patients",
        json={"full_name": "Test Patient 2", "lab_id": nonexistent_lab_id},
        headers=auth_headers(admin_a.id, lab_a.id, role="admin"),
    )
    # Whatever the DB does with a dangling FK (accepts it under SQLite's lax
    # FK enforcement, or 500s under Postgres) is not the point: the request
    # was never rejected for authorization reasons before reaching the DB.
    assert resp.status_code != 403, (
        "if this ever starts returning 403, NR-148 has been fixed — remove "
        "this test's negative framing and replace it with a real ownership "
        "proof (own lab allowed, other lab denied)"
    )
