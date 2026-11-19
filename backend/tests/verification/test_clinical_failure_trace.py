"""What does a failing protected clinical command actually leave behind?

WP-002 / NR-024.  The finding was recorded as "a failing protected clinical command
writes no receipt and no audit row".  The ICU final proof already narrowed it: an
ordinary clinical refusal **is** audited, with the actor, the resource and the
reason.  NR-024's original measurement was taken when the *database itself* was the
failure, so ``guard.reject`` shared the broken dependency it was trying to record.

That narrower claim is what this module measures, by execution, and it splits into
two questions the register answered as one:

1. **Per stage.** ``ClinicalCommandGuard`` has five injectable stages. For each one
   that the reservation path reaches, what durable evidence survives — a receipt, a
   ``.rejected`` audit row, a metric, or nothing?
2. **When the audit write is the thing that fails.** ``reject()`` wraps
   ``log_action`` in ``try/except``, calls ``clinical_safety_metrics.record_audit_failure``
   and then **re-raises**. So there is a fallback, and there is a consequence to the
   re-raise. Both are measured rather than read.

Subject: ``POST /blood-bank/reservations`` → ``blood.reservation.create``, the one
guarded command that carries call sites for four of the five stages.
``critical_care`` has **no** ``maybe_fail`` call site at all, which is why the ICU
operation could not be used here and is reported NOT_TESTED for injection.
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

LAB_ID = 994501
ACTOR_ID = 74501
OPERATION = "blood.reservation.create"
AUDIT_OK = f"clinical.{OPERATION}"
AUDIT_REJECTED = f"clinical.{OPERATION}.rejected"
FACILITY_ID = "FAC-TRACE-01"
PATIENT_ID = "PAT-TRACE-01"
ENDPOINT = "/blood-bank/reservations"

# Stages the reservation path actually reaches, in execution order.
REACHED_STAGES = ["after_claim", "after_business_effect", "after_inventory_movement", "after_commit"]


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


@pytest.fixture()
def Session() -> Any:
    S = harness.session_factory(pool_size=4)
    yield S
    harness.dispose(S)


def _purge(S: Any) -> None:
    """``audit_logs`` is excluded: the database refuses deletes from it. Audit
    assertions are deltas against a baseline, never absolute counts."""
    with S() as s:
        for table in (
            "blood_bank_inventory_movements",
            "blood_bank_traceability_events",
            "blood_bank_reservations",
            "blood_bank_crossmatches",
            "blood_bank_units",
            "clinical_command_receipts",
        ):
            s.execute(text(f"DELETE FROM {table} WHERE lab_id = :l"), {"l": LAB_ID})
        s.execute(text("DELETE FROM lab_users WHERE lab_id = :l"), {"l": LAB_ID})
        s.execute(text("DELETE FROM labs WHERE id = :l"), {"l": LAB_ID})
        s.commit()


@pytest.fixture()
def seeded(Session: Any) -> dict[str, str]:
    from app.clinical.observability import clinical_safety_metrics

    _purge(Session)
    clinical_safety_metrics.reset_for_test()
    unit_id = f"UNIT-{uuid.uuid4().hex[:12]}"
    now = _now()
    with Session() as s:
        s.execute(text("INSERT INTO labs (id, name, is_active) VALUES (:i,:n,true)"),
                  {"i": LAB_ID, "n": "Failure Trace Lab"})
        s.execute(
            text("INSERT INTO lab_users (id,lab_id,name,email,password_hash,role,is_active,"
                 "perm_version) VALUES (:i,:l,:n,:e,'!synthetic','master_admin',true,1)"),
            {"i": ACTOR_ID, "l": LAB_ID, "n": "Trace Actor", "e": "trace@example.invalid"},
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
                 "verified_at,expires_at,created_at,updated_at,is_deleted,version) "
                 "VALUES (:i,:l,:p,:u,'compatible',:t,:exp,:t,:t,false,1)"),
            {"i": f"XM-{uuid.uuid4().hex[:10]}", "l": LAB_ID, "p": PATIENT_ID,
             "u": unit_id, "t": now, "exp": now + dt.timedelta(hours=12)},
        )
        s.commit()
    yield {"unit_id": unit_id}
    harness.clear_overrides()
    _purge(Session)


def _post(Session: Any, unit_id: str, key: str) -> Any:
    body = {"unit_id": unit_id, "order_id": "ORD-TRACE-01",
            "patient_id": PATIENT_ID, "facility_id": FACILITY_ID}
    actor = harness.Actor(user_id=ACTOR_ID, lab_id=LAB_ID, role="master_admin")
    try:
        with harness.client(Session, actor) as client:
            return client.post(ENDPOINT, json=body, headers={"Idempotency-Key": key})
    finally:
        harness.clear_overrides()


def _audit_count(Session: Any, action: str) -> int:
    return harness.committed(
        Session, "SELECT count(*) AS n FROM audit_logs WHERE lab_id=:l AND action=:a",
        l=LAB_ID, a=action,
    )[0]["n"]


def _reservations(Session: Any, unit_id: str) -> list[dict[str, Any]]:
    return harness.committed(
        Session,
        "SELECT id, status FROM blood_bank_reservations WHERE lab_id=:l AND unit_id=:u",
        l=LAB_ID, u=unit_id,
    )


# ---------------------------------------------------------------------------
# 1. Per-stage census
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("stage", REACHED_STAGES)
def test_every_injected_stage_leaves_some_durable_or_observable_trace(
    Session: Any, seeded: dict[str, str], monkeypatch: Any, stage: str
) -> None:
    """WP-002's acceptance question, asked per stage.

    The assertion is deliberately weak on *form* and strong on *existence*: an audit
    row, a receipt, or a metric — but not nothing. A clinical command that fails
    leaving no trace at all is the thing NR-024 is about.
    """
    from app.clinical.observability import clinical_safety_metrics

    unit_id = seeded["unit_id"]
    key = f"trace-{stage}-{uuid.uuid4().hex[:6]}"
    before_ok = _audit_count(Session, AUDIT_OK)
    before_rejected = _audit_count(Session, AUDIT_REJECTED)
    clinical_safety_metrics.reset_for_test()

    monkeypatch.setenv("GULA_TEST_FAILURE_STAGE", stage)
    response = _post(Session, unit_id, key)

    receipts = harness.receipts(Session, lab_id=LAB_ID, operation=OPERATION, key=key)
    after_ok = _audit_count(Session, AUDIT_OK) - before_ok
    after_rejected = _audit_count(Session, AUDIT_REJECTED) - before_rejected
    commands, audit_failures = clinical_safety_metrics.snapshot()

    trace = {
        "status": response.status_code,
        "receipts": len(receipts),
        "audit_ok": after_ok,
        "audit_rejected": after_rejected,
        "metric_commands": sum(commands.values()),
        "metric_audit_failures": sum(audit_failures.values()),
        "reservations": len(_reservations(Session, unit_id)),
    }
    assert (trace["receipts"] or trace["audit_ok"] or trace["audit_rejected"]
            or trace["metric_commands"] or trace["metric_audit_failures"]), (
        f"stage {stage} failed leaving NO trace of any kind: {trace}"
    )


def test_a_failure_after_commit_records_a_rejection_for_an_effect_that_committed(
    Session: Any, seeded: dict[str, str], monkeypatch: Any
) -> None:
    """``after_commit`` is the stage where the audit trail and reality can disagree.

    ``maybe_fail("after_commit")`` fires *after* ``db.commit()``, so the reservation
    is durable. The route's ``except`` then rolls back a finished transaction (a
    no-op) and calls ``guard.reject``. Whatever this records, it records about a
    clinical effect that actually happened — which is exactly what a reader of the
    audit trail must not be misled about.

    Measured, not assumed: the numbers below are whatever the platform really does.
    """
    unit_id = seeded["unit_id"]
    key = f"trace-aftercommit-{uuid.uuid4().hex[:6]}"
    before_rejected = _audit_count(Session, AUDIT_REJECTED)
    before_ok = _audit_count(Session, AUDIT_OK)

    monkeypatch.setenv("GULA_TEST_FAILURE_STAGE", "after_commit")
    response = _post(Session, unit_id, key)

    committed_effect = _reservations(Session, unit_id)
    assert committed_effect, (
        "after_commit no longer leaves the effect committed; the stage's meaning "
        f"changed and this test must be re-measured. response={response.status_code}"
    )
    assert committed_effect[0]["status"] == "reserved"

    rejected_delta = _audit_count(Session, AUDIT_REJECTED) - before_rejected
    ok_delta = _audit_count(Session, AUDIT_OK) - before_ok
    assert ok_delta == 1, (
        f"the successful activation was not audited before the post-commit failure "
        f"(ok={ok_delta}, rejected={rejected_delta})"
    )
    # Pin whichever way it behaves, so a change surfaces. Both rows present means the
    # trail carries a success AND a rejection for one effect; that is a reader hazard,
    # recorded rather than silently accepted.
    assert rejected_delta in (0, 1), f"unexpected rejection count {rejected_delta}"
    if rejected_delta == 1:
        rows = harness.audit_rows(Session, lab_id=LAB_ID, action=AUDIT_REJECTED)
        details = rows[-1]["details"]
        if isinstance(details, str):
            details = json.loads(details)
        assert details.get("resource_id"), details


# ---------------------------------------------------------------------------
# 2. NR-024's core: the audit write is itself the failure
# ---------------------------------------------------------------------------


def _install_audit_block(S: Any) -> None:
    with S() as s:
        s.execute(text(
            "CREATE OR REPLACE FUNCTION gula_test_block_audit_insert() RETURNS trigger AS $$ "
            "BEGIN RAISE EXCEPTION 'test-only: audit_logs insert refused'; END; $$ LANGUAGE plpgsql"
        ))
        s.execute(text(
            "CREATE TRIGGER gula_test_block_audit BEFORE INSERT ON audit_logs "
            "FOR EACH ROW EXECUTE FUNCTION gula_test_block_audit_insert()"
        ))
        s.commit()


def _remove_audit_block(S: Any) -> None:
    with S() as s:
        s.execute(text("DROP TRIGGER IF EXISTS gula_test_block_audit ON audit_logs"))
        s.execute(text("DROP FUNCTION IF EXISTS gula_test_block_audit_insert()"))
        s.commit()


def test_a_blood_bank_command_that_fails_leaves_no_rejection_record_at_all(
    Session: Any, seeded: dict[str, str], monkeypatch: Any
) -> None:
    """NR-024, root-caused: the handler has no rejection path to run.

    An AST census over all 36 guarded commands finds six with **no ``guard.reject``
    anywhere in the handler**, and all six are blood bank:
    ``blood.reservation.create``, ``blood.reservation.release``, ``blood.sample.create``,
    ``blood.reaction.create``, ``blood.return.create`` and ``blood.discard.create``.
    Their ``except`` branch is ``db.rollback(); _raise_blood_error(exc); raise`` — it
    rolls back and re-raises without recording anything.

    So the guard's audit-failure fallback is not merely fragile here; it is
    unreachable. Blocking the audit table is therefore not even necessary to
    demonstrate the gap, and this test does not block it: an ordinary injected
    failure already leaves no rejection record.
    """
    from app.clinical.observability import clinical_safety_metrics

    unit_id = seeded["unit_id"]
    key = f"trace-bb-noreject-{uuid.uuid4().hex[:6]}"
    clinical_safety_metrics.reset_for_test()
    before_rejected = _audit_count(Session, AUDIT_REJECTED)

    monkeypatch.setenv("GULA_TEST_FAILURE_STAGE", "after_business_effect")
    response = _post(Session, unit_id, key)

    assert response.status_code >= 400, response.status_code
    assert _audit_count(Session, AUDIT_REJECTED) == before_rejected, (
        "a rejection row appeared; this handler has gained a guard.reject and the "
        "finding must be re-measured"
    )
    assert _reservations(Session, unit_id) == [], "a clinical effect survived the failure"
    _commands, audit_failures = clinical_safety_metrics.snapshot()
    assert sum(audit_failures.values()) == 0, (
        f"the audit-failure counter fired without a reject path: {audit_failures}"
    )


def test_positive_control_a_route_that_does_call_reject_records_the_audit_failure(
    Session: Any, monkeypatch: Any
) -> None:
    """The control that makes the test above mean something.

    Without this, "no counter incremented" is equally consistent with a broken
    counter, a broken trigger, or a metrics singleton the test imported twice. Here
    the ICU verify route — which **does** call ``guard.reject`` — is driven into a
    clinical refusal while the database refuses audit inserts. The counter fires.

    That isolates the cause precisely: the blood bank gap is a missing rejection
    path, not a broken fallback.

    It also executes FM-026 masking for the first time: ``reject()`` re-raises after
    incrementing, so the client receives the audit failure rather than the clinical
    reason it was refused for.
    """
    from app.clinical.observability import clinical_safety_metrics

    lab, initiator, verifier = 994601, 74601, 74602
    infusion = "trace-icu-infusion"
    now = _now()

    def purge() -> None:
        with Session() as s:
            for table in ("clinical_command_receipts", "critical_care_infusions",
                          "critical_care_admissions", "critical_care_beds", "lab_users"):
                s.execute(text(f"DELETE FROM {table} WHERE lab_id=:l"), {"l": lab})
            s.execute(text("DELETE FROM labs WHERE id=:l"), {"l": lab})
            s.commit()

    purge()
    with Session() as s:
        s.execute(text("INSERT INTO labs (id,name,is_active) VALUES (:l,'Trace ICU',true)"), {"l": lab})
        for uid in (initiator, verifier):
            s.execute(
                text("INSERT INTO lab_users (id,lab_id,name,email,password_hash,role,is_active,"
                     "perm_version) VALUES (:i,:l,:n,:e,'!synthetic','master_admin',true,1)"),
                {"i": uid, "l": lab, "n": f"Trace {uid}", "e": f"trace-{uid}@example.invalid"},
            )
        s.execute(
            text("INSERT INTO critical_care_beds (id,lab_id,bed_label,icu_type,has_infusion_pump,"
                 "has_monitor,is_occupied,is_active,is_deleted,version,created_at,updated_at) "
                 "VALUES ('trace-bed',:l,'B1','adult_icu',true,true,true,true,false,1,:t,:t)"),
            {"l": lab, "t": now},
        )
        s.execute(
            text("INSERT INTO critical_care_admissions (id,lab_id,patient_id,bed_id,status,icu_type,"
                 "admission_type,is_deleted,version,created_at,updated_at) VALUES "
                 "('trace-adm',:l,'trace-pat','trace-bed','stable','adult_icu','emergency',"
                 "false,1,:t,:t)"),
            {"l": lab, "t": now},
        )
        s.execute(
            text("INSERT INTO critical_care_infusions (id,lab_id,patient_id,admission_id,medication,"
                 "rate,start_time,initiated_by,status,is_deleted,version,created_at,updated_at) "
                 "VALUES (:i,:l,'trace-pat','trace-adm','norepinephrine','5 ml/hr',:t,:ini,"
                 "'awaiting_verification',false,1,:t,:t)"),
            {"i": infusion, "l": lab, "t": now, "ini": str(initiator)},
        )
        s.commit()

    clinical_safety_metrics.reset_for_test()
    actor = harness.Actor(user_id=initiator, lab_id=lab, role="master_admin")  # the initiator
    _install_audit_block(Session)
    try:
        # The initiator verifying their own infusion is refused by the clinical rule,
        # which is what drives the route into guard.reject.
        with harness.client(Session, actor) as client:
            response = client.post(
                f"/critical-care/infusions/{infusion}/verify",
                headers={"Idempotency-Key": "trace-icu-key", "If-Match": "1"},
            )
    finally:
        _remove_audit_block(Session)
        harness.clear_overrides()

    _commands, audit_failures = clinical_safety_metrics.snapshot()
    assert sum(audit_failures.values()) >= 1, (
        f"the fallback did not fire on a route that does call reject: {audit_failures}"
    )

    # FM-026: the clinical reason is replaced by the audit failure.
    body = response.text
    assert "independent clinical actor" not in body, (
        "the clinical refusal reason survived, so the audit failure did not mask it — "
        f"re-measure FM-026. body={body[:200]}"
    )
    assert response.status_code >= 400, response.status_code

    # Nothing durable survived either.
    state = harness.committed(
        Session, "SELECT status, verified_by FROM critical_care_infusions WHERE id=:i", i=infusion,
    )
    assert state and state[0]["status"] == "awaiting_verification", state
    assert state[0]["verified_by"] is None, state
    purge()


def test_the_audit_failure_counter_is_in_memory_and_therefore_not_durable(
    Session: Any,
) -> None:
    """The fallback is a dict behind a lock, so it is per-process and per-worker.

    Stated as a test because "a metric was recorded" reads like durable evidence and
    is not: it does not survive a worker restart, it is not in the audit trail, and
    with ``WEB_CONCURRENCY`` workers each holds its own copy. Read from the object,
    not from the source, so a change to the sink fails here.
    """
    from app.clinical.observability import clinical_safety_metrics

    clinical_safety_metrics.record_audit_failure(operation="probe.op", resource_type="probe")
    _commands, failures = clinical_safety_metrics.snapshot()
    assert sum(failures.values()) >= 1

    clinical_safety_metrics.reset_for_test()
    _commands, after_reset = clinical_safety_metrics.snapshot()
    assert sum(after_reset.values()) == 0, (
        "the counter survived reset_for_test, so it is no longer purely in-process; "
        "re-measure whether a durable sink now exists"
    )
