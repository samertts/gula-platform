"""NR-150 — POST /identity/link must not answer questions about other laboratories.

THE DEFECT THIS PINS
--------------------
The handler runs two patient queries two lines apart. The first scoped to the
caller::

    Patient.id == data.patient_id, Patient.lab_id == current_user.lab_id

The second did not::

    Patient.national_id_hash == nid_hash, Patient.id != patient.id

So the 409 was computed over the whole `patients` table. Any authenticated lab
caller could create one throwaway patient in its own laboratory and loop this
endpoint over candidate national identifiers: 409 meant "that identifier is on
a record somewhere in the country", 200 meant it was not. On 200 the hash is
overwritten, so the same throwaway row probes again indefinitely. Iraqi
national identifiers are structured and enumerable, and there is no rate limit
on the path. That is an existence oracle over the national population, reached
with ordinary lab credentials.

It was fixed on 2026-09-19 by scoping the duplicate check to the caller's own
laboratory, and until this module there was nothing to stop it coming back.
That matters more here than usual: the register records this as the third
instance of one signature -- two queries in a single handler, one tenant-scoped
and one not -- after NR-141 and NR-146. A defect class that has recurred three
times is not held off by a comment.

WHY BOTH DIRECTIONS ARE TESTED
------------------------------
`test_b` alone would pass if someone deleted the duplicate check outright,
which is a different defect: two patients in one laboratory silently sharing a
national identifier, and the response says nothing is wrong. `test_c` is the
control that separates "scoped correctly" from "not checked at all". A guard
that cannot tell those apart is not guarding the invariant, only the status
code.

The oracle is about what the caller can *learn*, so the assertions are on the
response the attacker sees, not on the query. Reading the SQL would prove the
filter is present; only the response proves it is load-bearing.

Evidence level: real route, real token, real ORM query, over the suite's
SQLite engine. The defect is a missing WHERE clause -- query semantics SQLite
reproduces exactly -- so nothing here depends on PostgreSQL.
"""

from __future__ import annotations

import pytest
from app.models.patient import Patient
from app.services.identity import hash_national_id

from tests.conftest import auth_headers

#: One identifier, used by the victim record in the *other* laboratory. Its
#: value is irrelevant; what matters is that the attacker never supplied it and
#: has no right to learn that it exists.
VICTIM_NATIONAL_ID = "19900101234"


@pytest.fixture()
def two_labs(db, make_lab, make_lab_user):
    """Attacker's laboratory and a victim laboratory that share nothing.

    The attacker gets exactly what NR-150 describes: ordinary credentials and
    one throwaway patient of their own to probe with.
    """
    attacker_lab = make_lab(name="NR-150 Attacker Lab")
    victim_lab = make_lab(name="NR-150 Victim Lab")

    attacker = make_lab_user(lab_id=attacker_lab.id, role="admin",
                             email="nr150-attacker@test.com")

    throwaway = Patient(lab_id=attacker_lab.id, full_name="NR-150 Throwaway",
                        phone="07700000001", gender="M")
    victim = Patient(lab_id=victim_lab.id, full_name="NR-150 Victim",
                     phone="07700000002", gender="F",
                     national_id_hash=hash_national_id(VICTIM_NATIONAL_ID))
    db.add_all([throwaway, victim])
    db.flush()

    return {
        "headers": auth_headers(attacker.id, attacker_lab.id, role="admin"),
        "attacker_lab_id": attacker_lab.id,
        "throwaway_id": throwaway.id,
        "victim_id": victim.id,
    }


def test_a_the_probe_reaches_the_handler(client, two_labs):
    """Positive control.

    Every assertion below reads a status code. If the route were unregistered,
    the auth token rejected, or the throwaway patient invisible to its own
    laboratory, the responses would be 404 or 401 -- and `test_b` would pass
    for a reason that has nothing to do with tenant scope. This pins that the
    probe actually executes the handler.
    """
    response = client.post(
        "/identity/link",
        json={"patient_id": two_labs["throwaway_id"], "national_id": "19900101999"},
        headers=two_labs["headers"],
    )

    assert response.status_code == 200, (
        f"the probe never reached the duplicate check: {response.status_code} "
        f"{response.text[:300]}"
    )


def test_b_another_laboratorys_national_id_is_not_disclosed(client, db, two_labs):
    """The finding. A national ID held only by another lab must read as free.

    A 409 here is the oracle: it tells a caller with no relationship to the
    victim laboratory that this identifier is on a patient record somewhere in
    the country.
    """
    response = client.post(
        "/identity/link",
        json={"patient_id": two_labs["throwaway_id"],
              "national_id": VICTIM_NATIONAL_ID},
        headers=two_labs["headers"],
    )

    assert response.status_code != 409, (
        "POST /identity/link answered 409 for a national ID held only by "
        "another laboratory. That response is an existence oracle over the "
        "national population, reachable with ordinary lab credentials (NR-150)"
    )
    assert response.status_code == 200, (
        f"unexpected status {response.status_code}: {response.text[:300]}"
    )

    # The victim's record is untouched -- the caller learned nothing and
    # changed nothing outside its own laboratory.
    victim = db.get(Patient, two_labs["victim_id"])
    assert victim.national_id_hash == hash_national_id(VICTIM_NATIONAL_ID)


def test_c_a_duplicate_inside_the_callers_own_lab_is_still_refused(
    client, db, two_labs,
):
    """The control that stops `test_b` being satisfied by deleting the check.

    Without this, removing the duplicate query altogether -- so two patients in
    one laboratory can share a national identifier with no complaint -- would
    turn every assertion above green.
    """
    sibling = Patient(lab_id=two_labs["attacker_lab_id"], full_name="NR-150 Sibling",
                      phone="07700000003", gender="M",
                      national_id_hash=hash_national_id(VICTIM_NATIONAL_ID))
    db.add(sibling)
    db.flush()

    response = client.post(
        "/identity/link",
        json={"patient_id": two_labs["throwaway_id"],
              "national_id": VICTIM_NATIONAL_ID},
        headers=two_labs["headers"],
    )

    assert response.status_code == 409, (
        "a national ID already linked to another patient in the caller's OWN "
        f"laboratory was accepted ({response.status_code}); the duplicate check "
        "is gone rather than scoped"
    )


def test_d_lookup_does_not_disclose_another_laboratorys_patient(client, two_labs):
    """The sibling read path, pinned in the same module because it is the same question.

    GET /identity/lookup takes a national ID and returns the patient holding
    it. It is scoped correctly today; it is covered here because it is the
    other place in this file where a national identifier selects a patient
    row, and the NR-150 comment sits two functions above it.
    """
    response = client.get(
        "/identity/lookup",
        params={"national_id": VICTIM_NATIONAL_ID},
        headers=two_labs["headers"],
    )

    assert response.status_code == 200, response.text[:300]
    assert response.json()["found"] is False, (
        "GET /identity/lookup returned another laboratory's patient (NR-150 class)"
    )
