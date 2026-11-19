"""A released blood reservation must be audited with the versions that really occurred.

The release handler passes ``version_before=reservation.version - 1`` — an arithmetic
guess rather than the value it read. Every other guarded command in the platform
captures the real prior version into a variable and passes that: the seven blood bank
handlers that have a rejection path do, and so do all 38 sites in ``critical_care``
and ``lims``.

The guess is wrong twice over, because ``BloodBankService.release_reservation`` does
not increment ``reservation.version`` at all — it advances the *unit's* version, and
only sets the reservation's status, ``released_at`` and ``release_reason``. So with a
reservation at version N the audit row claims **N-1 -> N**, while the truth is
**N -> N**: a prior value that never existed, and an "after" value presented as the
result of an increment that never happened.

This is an audit-content defect, not a data-integrity one. The service locks the
reservation and the unit with ``FOR UPDATE`` and refuses anything but ``reserved``,
so a concurrent double release is already serialised and fails closed. What is wrong
is only what the audit trail says happened.
"""

from __future__ import annotations

import datetime as dt
import json
import uuid
from typing import Any

import pytest
from sqlalchemy import text

from . import harness

pytestmark = harness.requires_postgres()

LAB_ID = 994701
ACTOR_ID = 74701
FACILITY_ID = "FAC-REL-01"
PATIENT_ID = "PAT-REL-01"
RELEASE_AUDIT = "clinical.blood.reservation.release"


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


@pytest.fixture()
def Session() -> Any:
    S = harness.session_factory(pool_size=4)
    yield S
    harness.dispose(S)


def _purge(S: Any) -> None:
    with S() as s:
        for table in (
            "blood_bank_inventory_movements", "blood_bank_traceability_events",
            "blood_bank_reservations", "blood_bank_crossmatches", "blood_bank_units",
            "clinical_command_receipts",
        ):
            s.execute(text(f"DELETE FROM {table} WHERE lab_id = :l"), {"l": LAB_ID})
        s.execute(text("DELETE FROM lab_users WHERE lab_id = :l"), {"l": LAB_ID})
        s.execute(text("DELETE FROM labs WHERE id = :l"), {"l": LAB_ID})
        s.commit()


@pytest.fixture()
def reserved(Session: Any) -> dict[str, Any]:
    """An actually-reserved reservation, created through the real route."""
    _purge(Session)
    unit_id = f"UNIT-{uuid.uuid4().hex[:12]}"
    now = _now()
    with Session() as s:
        s.execute(text("INSERT INTO labs (id,name,is_active) VALUES (:l,'Release Audit Lab',true)"),
                  {"l": LAB_ID})
        s.execute(
            text("INSERT INTO lab_users (id,lab_id,name,email,password_hash,role,is_active,"
                 "perm_version) VALUES (:i,:l,'Release Actor',:e,'!synthetic','master_admin',true,1)"),
            {"i": ACTOR_ID, "l": LAB_ID, "e": "release@example.invalid"},
        )
        s.execute(
            text("INSERT INTO blood_bank_units (id,lab_id,blood_group,rh_factor,component,status,"
                 "facility_id,storage_location,expiry_date,recalled,created_at,updated_at,"
                 "is_deleted,version) VALUES (:i,:l,'O','positive','red_cells','available',:f,"
                 "'FRIDGE-1',:exp,false,:t,:t,false,1)"),
            {"i": unit_id, "l": LAB_ID, "f": FACILITY_ID,
             "exp": now + dt.timedelta(days=20), "t": now},
        )
        s.execute(
            text("INSERT INTO blood_bank_crossmatches (id,lab_id,patient_id,unit_id,status,"
                 "verified_at,expires_at,created_at,updated_at,is_deleted,version) VALUES "
                 "(:i,:l,:p,:u,'compatible',:t,:exp,:t,:t,false,1)"),
            {"i": f"XM-{uuid.uuid4().hex[:10]}", "l": LAB_ID, "p": PATIENT_ID, "u": unit_id,
             "t": now, "exp": now + dt.timedelta(hours=12)},
        )
        s.commit()

    actor = harness.Actor(user_id=ACTOR_ID, lab_id=LAB_ID, role="master_admin")
    try:
        with harness.client(Session, actor) as client:
            created = client.post(
                "/blood-bank/reservations",
                json={"unit_id": unit_id, "order_id": "ORD-REL-01",
                      "patient_id": PATIENT_ID, "facility_id": FACILITY_ID},
                headers={"Idempotency-Key": f"rel-seed-{uuid.uuid4().hex[:6]}"},
            )
    finally:
        harness.clear_overrides()
    assert created.status_code == 201, created.text

    rows = harness.committed(
        Session,
        "SELECT id, version, status FROM blood_bank_reservations WHERE lab_id=:l AND unit_id=:u",
        l=LAB_ID, u=unit_id,
    )
    assert len(rows) == 1, rows
    yield {"reservation_id": rows[0]["id"], "version": rows[0]["version"], "unit_id": unit_id}
    harness.clear_overrides()
    _purge(Session)


def _release(Session: Any, reservation_id: str, if_match: int) -> Any:
    actor = harness.Actor(user_id=ACTOR_ID, lab_id=LAB_ID, role="master_admin")
    try:
        with harness.client(Session, actor) as client:
            return client.post(
                f"/blood-bank/reservations/{reservation_id}/release",
                json={"reason": "no longer required"},
                headers={"Idempotency-Key": f"rel-{uuid.uuid4().hex[:8]}",
                         "If-Match": str(if_match)},
            )
    finally:
        harness.clear_overrides()


def test_the_release_audit_row_states_the_versions_that_actually_occurred(
    Session: Any, reserved: dict[str, Any]
) -> None:
    before = reserved["version"]
    response = _release(Session, reserved["reservation_id"], before)
    assert response.status_code == 200, response.text

    after_rows = harness.committed(
        Session, "SELECT version, status FROM blood_bank_reservations WHERE id=:i",
        i=reserved["reservation_id"],
    )
    assert after_rows and after_rows[0]["status"] == "released", after_rows
    actual_after = after_rows[0]["version"]

    audit = harness.audit_rows(Session, lab_id=LAB_ID, action=RELEASE_AUDIT)
    assert audit, "the release was not audited at all"
    details = audit[-1]["details"]
    if isinstance(details, str):
        details = json.loads(details)

    assert details.get("version_before") == before, (
        f"the audit states version_before={details.get('version_before')} but the row was "
        f"read at version {before}; a value that never existed is recorded as fact"
    )
    assert details.get("version_after") == actual_after, (
        f"the audit states version_after={details.get('version_after')} but the row is at "
        f"version {actual_after}"
    )
