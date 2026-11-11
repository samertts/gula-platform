"""Recovery evidence: do the invariants survive the database going away?

WP-005.  ``FAILURE_MODES.md`` records eight modes with **no mechanism at all** —
FM-010 to FM-013 and FM-022 to FM-025 — covering database disconnect, process
restart, service restart and dependency failure.  The platform ships a circuit
breaker, a degraded mode and an auto-repair engine, so the absence was never a
claim that recovery is broken; it was an admission that nothing here could say
either way.  This module is the first thing that can.

Three invariants are re-asserted across a real interruption, using a real
guarded clinical command (``blood.reservation.create``) against real PostgreSQL:

* **INV-TXN-01** — an interruption before commit leaves zero committed effect.
  Not the same as the exception path: an exception runs ``except`` and
  ``rollback``, whereas a killed backend never runs either.  The guarantee has
  to come from the database, and this is what proves it does.
* **INV-IDEM-01** — after the database comes back, a replay of the same
  idempotency key is still refused.  A receipt that did not survive the restart
  would turn a retry into a second reservation of the same unit of blood.
* **INV-AUDIT-01 / INV-AUDIT-02** — audit rows survive the restart, and the
  append-only trigger still refuses ``DELETE`` afterwards.  A trigger is part of
  the schema, but "it was there before the restart" is not evidence that it is
  there after one.

Why a blood unit rather than the ICU infusion: ``critical_care_infusions``
cannot be exercised on a database an operator can build (NR-023/NR-028), while
the blood bank's seventeen tables match their ORM exactly at head.  Recovery is
a platform property, so it is proven on a path that is actually reachable.
"""

from __future__ import annotations

import datetime as dt
import os
import subprocess
import uuid
from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError, OperationalError

from . import harness

pytestmark = harness.requires_postgres()

LAB_ID = 994301
ACTOR_ID = 74301
OPERATION = "blood.reservation.create"
FACILITY_ID = "FAC-RECOVERY-01"
PATIENT_ID = "PAT-RECOVERY-01"

# Restarting a database cluster is destructive to everything on that instance, so
# it is gated the way ``failure_injection`` gates itself: opt in explicitly, never
# by default.  Without the gate the restart test does not silently pass — it
# reports that it did not run, which is a different thing from evidence.
RESTART_GATE = "GULA_RECOVERY_ALLOW_DB_RESTART"
RESTART_CMD = ["sudo", "pg_ctlcluster", "16", "main", "restart"]


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


@pytest.fixture()
def Session() -> Any:
    S = harness.session_factory(pool_size=4)
    yield S
    harness.dispose(S)


def _purge(S: Any) -> None:
    """Remove this module's own rows. ``audit_logs`` is excluded deliberately —
    the database refuses to delete from it, which is INV-AUDIT-02 and is asserted
    rather than worked around."""
    with S() as s:
        for table in (
            "blood_bank_inventory_movements",
            "blood_bank_traceability_events",
            "blood_bank_reservations",
            "blood_bank_crossmatches",
            "blood_bank_units",
            "clinical_command_receipts",
        ):
            s.execute(text(f"DELETE FROM {table} WHERE lab_id = :lab"), {"lab": LAB_ID})
        s.execute(text("DELETE FROM lab_users WHERE lab_id = :lab"), {"lab": LAB_ID})
        s.execute(text("DELETE FROM labs WHERE id = :lab"), {"lab": LAB_ID})
        s.commit()


@pytest.fixture()
def seeded(Session: Any) -> dict[str, str]:
    """A lab, an authorised actor, an available unit and a current crossmatch.

    Seeded through SQL rather than the ORM so the row shapes come from the
    migrated schema, not from the ORM's opinion of it.
    """
    _purge(Session)
    unit_id = f"UNIT-{uuid.uuid4().hex[:12]}"
    now = _now()
    with Session() as s:
        s.execute(
            text("INSERT INTO labs (id, name) VALUES (:id, :name)"),
            {"id": LAB_ID, "name": "Recovery Proof Lab"},
        )
        s.execute(
            text(
                "INSERT INTO lab_users (id, lab_id, name, email, password_hash, role) "
                "VALUES (:id, :lab, :name, :email, :pw, :role)"
            ),
            {
                "id": ACTOR_ID, "lab": LAB_ID, "name": "Recovery Actor",
                "email": "recovery.actor@example.test", "pw": "x", "role": "master_admin",
            },
        )
        s.execute(
            text(
                "INSERT INTO blood_bank_units "
                "(id, lab_id, blood_group, rh_factor, component, status, facility_id, "
                " storage_location, expiry_date, recalled, created_at, updated_at, is_deleted, version) "
                "VALUES (:id, :lab, 'O', 'positive', 'red_cells', 'available', :fac, "
                " 'FRIDGE-1', :exp, false, :now, :now, false, 1)"
            ),
            {"id": unit_id, "lab": LAB_ID, "fac": FACILITY_ID,
             "exp": now + dt.timedelta(days=20), "now": now},
        )
        s.execute(
            text(
                "INSERT INTO blood_bank_crossmatches "
                "(id, lab_id, patient_id, unit_id, status, verified_at, expires_at, "
                " created_at, updated_at, is_deleted, version) "
                "VALUES (:id, :lab, :pat, :unit, 'compatible', :now, :exp, :now, :now, false, 1)"
            ),
            {"id": f"XM-{uuid.uuid4().hex[:10]}", "lab": LAB_ID, "pat": PATIENT_ID,
             "unit": unit_id, "now": now, "exp": now + dt.timedelta(hours=12)},
        )
        s.commit()
    yield {"unit_id": unit_id}
    harness.clear_overrides()
    _purge(Session)


def _actor() -> harness.Actor:
    return harness.Actor(user_id=ACTOR_ID, lab_id=LAB_ID, role="master_admin")


def _body(unit_id: str) -> dict[str, Any]:
    return {
        "unit_id": unit_id, "order_id": "ORD-RECOVERY-01", "patient_id": PATIENT_ID,
        "facility_id": FACILITY_ID,
    }


def _unit_status(Session: Any, unit_id: str) -> tuple[str, int]:
    rows = harness.committed(
        Session, "SELECT status, version FROM blood_bank_units WHERE id = :id", id=unit_id
    )
    assert rows, "the seeded unit disappeared"
    return rows[0]["status"], rows[0]["version"]


def _reservations(Session: Any, unit_id: str) -> list[dict[str, Any]]:
    return harness.committed(
        Session,
        "SELECT id, status, version FROM blood_bank_reservations "
        "WHERE lab_id = :lab AND unit_id = :id",
        lab=LAB_ID, id=unit_id,
    )


# ---------------------------------------------------------------------------
# INV-TXN-01 across an interruption, not an exception
# ---------------------------------------------------------------------------


def test_a_backend_killed_mid_transaction_leaves_no_committed_effect(
    Session: Any, seeded: dict[str, str]
) -> None:
    """Kill the connection between the write and the commit; expect nothing.

    The route's ``except`` branch is not what is under test here — a terminated
    backend never reaches it. What is under test is whether the durable state can
    end up half-written when the process doing the writing simply stops.
    """
    unit_id = seeded["unit_id"]
    key = f"recovery-txn-{uuid.uuid4().hex[:8]}"

    with Session() as writer:
        pid = writer.execute(text("SELECT pg_backend_pid()")).scalar_one()
        # A real partial effect: claim the idempotency key and move the unit,
        # exactly as the route does, but stop short of committing.
        writer.execute(
            text(
                "INSERT INTO clinical_command_receipts "
                "(lab_id, actor_user_id, operation, idempotency_key, status, "
                " resource_type, resource_id, request_fingerprint, created_at) "
                "VALUES (:lab, :actor, :op, :key, 'claimed', 'blood_unit', :unit, "
                " 'fingerprint', :now)"
            ),
            {"lab": LAB_ID, "actor": ACTOR_ID, "op": OPERATION,
             "key": key, "unit": unit_id, "now": _now()},
        )
        writer.execute(
            text("UPDATE blood_bank_units SET status = 'reserved', version = version + 1 "
                 "WHERE id = :id"),
            {"id": unit_id},
        )
        writer.flush()

        # Terminate the writer from an independent connection.  This is the
        # interruption: no rollback runs, no handler runs, the backend is gone.
        with Session() as killer:
            killed = killer.execute(
                text("SELECT pg_terminate_backend(:pid)"), {"pid": pid}
            ).scalar_one()
            killer.commit()
        assert killed is True, "the writer backend was not terminated; the test proved nothing"

        # Named precisely: a terminated backend surfaces as OperationalError
        # (psycopg2 AdminShutdown).  Asserting on bare Exception would also pass
        # for an assertion error inside this block, which would prove nothing.
        with pytest.raises(OperationalError):
            writer.execute(text("SELECT 1"))

    # Committed state, read on a fresh connection.
    assert harness.receipts(Session, lab_id=LAB_ID, operation=OPERATION, key=key) == [], (
        "a receipt survived a transaction that was never committed"
    )
    status, version = _unit_status(Session, unit_id)
    assert (status, version) == ("available", 1), (
        f"the unit moved despite the interruption: {status} v{version}"
    )
    assert _reservations(Session, unit_id) == []


# ---------------------------------------------------------------------------
# The happy path, so the restart has something durable to preserve
# ---------------------------------------------------------------------------


def _reserve(Session: Any, unit_id: str, key: str) -> Any:
    """POST the guarded command.

    The ``with`` matters: entering the TestClient runs the app lifespan, which runs
    the startup guard, which marks the system ready in test mode. Called without
    it, ``ReadinessMiddleware`` answers every request with 503 and the test proves
    nothing about the route. Same mechanism the ICU slice uses.
    """
    try:
        with harness.client(Session, _actor()) as client:
            return client.post(
                "/blood-bank/reservations",
                json=_body(unit_id),
                headers={"Idempotency-Key": key},
            )
    finally:
        harness.clear_overrides()


def test_the_guarded_command_succeeds_once_and_refuses_its_own_replay(
    Session: Any, seeded: dict[str, str]
) -> None:
    """Baseline. Without this, a post-restart refusal could be a refusal for any
    reason at all, and the restart evidence would be worthless."""
    unit_id = seeded["unit_id"]
    key = f"recovery-base-{uuid.uuid4().hex[:8]}"

    first = _reserve(Session, unit_id, key)
    assert first.status_code == 201, first.text
    assert len(_reservations(Session, unit_id)) == 1
    assert _unit_status(Session, unit_id)[0] == "reserved"
    claims = harness.receipts(Session, lab_id=LAB_ID, operation=OPERATION, key=key)
    assert len(claims) == 1, f"expected exactly one receipt, got {claims}"

    replay = _reserve(Session, unit_id, key)
    assert replay.status_code in (409, 422), (
        f"a replay of a completed command was not refused: {replay.status_code} {replay.text}"
    )
    assert len(_reservations(Session, unit_id)) == 1, "the replay created a second reservation"


# ---------------------------------------------------------------------------
# INV-IDEM-01, INV-AUDIT-01 and INV-AUDIT-02 across a real process restart
# ---------------------------------------------------------------------------


def _restart_database() -> None:
    subprocess.run(RESTART_CMD, check=True, capture_output=True, timeout=120)


@pytest.mark.skipif(
    os.environ.get(RESTART_GATE) != "1",
    reason=(
        f"{RESTART_GATE}=1 not set. This test restarts the PostgreSQL cluster, which is "
        "destructive to every database on the instance, so it never runs by default. "
        "A skip here is NOT evidence that recovery works."
    ),
)
def test_committed_state_receipts_and_audit_survive_a_database_restart(
    Session: Any, seeded: dict[str, str]
) -> None:
    """Reserve a unit, restart PostgreSQL, then re-assert every invariant.

    The replay after the restart is the one that matters clinically: if the
    receipt did not survive, the retry a client sends after an outage would
    reserve the same unit of blood a second time.
    """
    unit_id = seeded["unit_id"]
    key = f"recovery-restart-{uuid.uuid4().hex[:8]}"

    assert _reserve(Session, unit_id, key).status_code == 201
    before_reservations = _reservations(Session, unit_id)
    before_receipts = harness.receipts(Session, lab_id=LAB_ID, operation=OPERATION, key=key)
    before_audit = harness.committed(
        Session, "SELECT count(*) AS n FROM audit_logs WHERE lab_id = :lab", lab=LAB_ID
    )[0]["n"]
    assert len(before_reservations) == 1 and len(before_receipts) == 1

    harness.dispose(Session)
    _restart_database()

    # A brand-new engine, so nothing is answered from a pooled connection or an
    # identity map that predates the restart.
    After = harness.session_factory(pool_size=4)
    try:
        assert After().execute(text("SELECT 1")).scalar_one() == 1, "database did not come back"

        # INV-TXN-01 / durability: the committed effect is intact and unchanged.
        after_reservations = _reservations(After, unit_id)
        assert after_reservations == before_reservations, (
            f"reservation state changed across the restart: {before_reservations} -> "
            f"{after_reservations}"
        )
        assert _unit_status(After, unit_id)[0] == "reserved"

        # INV-IDEM-01: the receipt survived, so the replay is still refused.
        after_receipts = harness.receipts(After, lab_id=LAB_ID, operation=OPERATION, key=key)
        assert after_receipts == before_receipts, (
            f"the idempotency receipt did not survive the restart: {after_receipts}"
        )
        replay = _reserve(After, unit_id, key)
        assert replay.status_code in (409, 422), (
            f"after the restart a replay was accepted: {replay.status_code} {replay.text}"
        )
        assert len(_reservations(After, unit_id)) == 1, (
            "the post-restart replay reserved the same unit of blood twice"
        )

        # INV-AUDIT-01: the audit history survived.
        after_audit = harness.committed(
            After, "SELECT count(*) AS n FROM audit_logs WHERE lab_id = :lab", lab=LAB_ID
        )[0]["n"]
        assert after_audit >= before_audit, (
            f"audit rows were lost across the restart: {before_audit} -> {after_audit}"
        )

        # INV-AUDIT-02: the append-only trigger is still enforced afterwards.
        with pytest.raises(DatabaseError) as refused, After() as s:
            s.execute(text("DELETE FROM audit_logs WHERE lab_id = :lab"), {"lab": LAB_ID})
            s.commit()
        assert "append-only" in str(refused.value), (
            f"the append-only trigger did not survive the restart: {refused.value}"
        )
    finally:
        harness.clear_overrides()
        harness.dispose(After)
