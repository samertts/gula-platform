"""ICU high-alert infusion verification — final proof on the canonical lineage.

Subject: ``POST /critical-care/infusions/{id}/verify``, the independent second-actor
check that stands between a clinician and activating a high-alert infusion
(norepinephrine, insulin, heparin, potassium chloride, propofol, fentanyl,
midazolam, epinephrine).

This replaces the tripwire slice, which asserted the *defective* behaviour so it
would break when the defect was fixed.  On this lineage it broke, so the
expectations here are the repaired ones and they are asserted positively.  Nothing
below infers a result from the negation of a tripwire.

Every fixture seeds **per test**.  A module-scoped seed made the happy path answer
409 on an earlier run — the state had already been advanced by a previous test —
which is exactly the kind of artefact that gets mistaken for a defect.

One gap is recorded rather than papered over: ``critical_care`` contains **no**
``maybe_fail`` call site, so injection-based rollback cannot be exercised for this
operation.  Rollback is instead proven through a real in-transaction clinical
failure (the independent-actor rule), and the injection variant is reported
NOT_TESTED.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import text

from . import harness

pytestmark = harness.requires_postgres()

LAB_ID = 994201
OTHER_LAB_ID = 994202
INITIATOR_ID = 74201
VERIFIER_ID = 74202
SECOND_VERIFIER_ID = 74203
BED_ID = "final-icu-bed"
ADMISSION_ID = "final-icu-admission"
INFUSION_ID = "final-icu-infusion"
PATIENT_ID = "final-icu-patient"
HIGH_ALERT_MEDICATION = "norepinephrine"
OPERATION = "icu.infusion.verify"
AUDIT_ACTION = "clinical.icu.infusion.verify"
ENDPOINT = f"/critical-care/infusions/{INFUSION_ID}/verify"

NON_ADMIN_ROLES = ["technician", "doctor", "lab_admin", "staff", "citizen"]


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------


def _purge(S: Any) -> None:
    """``audit_logs`` is excluded on purpose: the database refuses to delete from
    it, which is itself an invariant asserted below.  Audit assertions are deltas
    against a baseline captured at setup, never absolute counts."""
    with S() as s:
        for lab in (LAB_ID, OTHER_LAB_ID):
            for table in (
                "clinical_command_receipts",
                "critical_care_infusions",
                "critical_care_admissions",
                "critical_care_beds",
                "lab_users",
            ):
                s.execute(text(f"DELETE FROM {table} WHERE lab_id=:l"), {"l": lab})
            s.execute(text("DELETE FROM labs WHERE id=:l"), {"l": lab})
        s.commit()


@pytest.fixture()
def Session() -> Any:
    S = harness.session_factory(pool_size=6)
    yield S
    harness.dispose(S)


@pytest.fixture()
def seeded(Session: Any) -> Any:
    """A high-alert infusion awaiting verification, plus two possible verifiers."""
    _purge(Session)
    now = datetime.now(UTC)
    with Session() as s:
        for lab, name in ((LAB_ID, "Final ICU Lab"), (OTHER_LAB_ID, "Final Foreign Lab")):
            s.execute(text("INSERT INTO labs (id,name,is_active) VALUES (:i,:n,true)"),
                      {"i": lab, "n": name})
        for uid, lab in ((INITIATOR_ID, LAB_ID), (VERIFIER_ID, LAB_ID),
                         (SECOND_VERIFIER_ID, LAB_ID)):
            s.execute(
                text("INSERT INTO lab_users (id,lab_id,name,email,password_hash,role,"
                     "is_active,perm_version) VALUES (:i,:l,:n,:e,'!synthetic-only',"
                     "'master_admin',true,1)"),
                {"i": uid, "l": lab, "n": f"Final Actor {uid}", "e": f"final-{uid}@example.invalid"},
            )
        s.execute(
            text("INSERT INTO critical_care_beds (id,lab_id,bed_label,icu_type,has_infusion_pump,"
                 "has_monitor,is_occupied,is_active,is_deleted,version,created_at,updated_at)"
                 " VALUES (:i,:l,'B1','adult_icu',true,true,true,true,false,1,:t,:t)"),
            {"i": BED_ID, "l": LAB_ID, "t": now},
        )
        s.execute(
            text("INSERT INTO critical_care_admissions (id,lab_id,patient_id,bed_id,status,"
                 "icu_type,admission_type,is_deleted,version,created_at,updated_at)"
                 " VALUES (:i,:l,:p,:b,'stable','adult_icu','emergency',false,1,:t,:t)"),
            {"i": ADMISSION_ID, "l": LAB_ID, "p": PATIENT_ID, "b": BED_ID, "t": now},
        )
        s.execute(
            text("INSERT INTO critical_care_infusions (id,lab_id,patient_id,admission_id,"
                 "medication,rate,start_time,initiated_by,status,is_deleted,version,"
                 "created_at,updated_at) VALUES (:i,:l,:p,:a,:m,'5 ml/hr',:t,:ini,"
                 "'awaiting_verification',false,1,:t,:t)"),
            {"i": INFUSION_ID, "l": LAB_ID, "p": PATIENT_ID, "a": ADMISSION_ID,
             "m": HIGH_ALERT_MEDICATION, "t": now, "ini": str(INITIATOR_ID)},
        )
        s.commit()
    yield
    harness.clear_overrides()
    _purge(Session)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _actor(user_id: int = VERIFIER_ID, lab_id: int = LAB_ID) -> harness.Actor:
    """``master_admin`` is the only one of sixteen roles holding ``system:admin``,
    which the whole ``critical-care`` router requires.  Whether that is the right
    clinical boundary is WP-003; it is not this module's question."""
    return harness.Actor(user_id=user_id, lab_id=lab_id, role="master_admin")


def _post(Session: Any, actor: harness.Actor | None, *, key: str | None,
          if_match: str | None = "1", endpoint: str = ENDPOINT) -> Any:
    headers: dict[str, str] = {}
    if key is not None:
        headers["Idempotency-Key"] = key
    if if_match is not None:
        headers["If-Match"] = if_match
    try:
        with harness.client(Session, actor) as client:
            return client.post(endpoint, headers=headers)
    finally:
        harness.clear_overrides()


def _state(Session: Any) -> dict[str, Any]:
    rows = harness.committed(
        Session,
        "SELECT status, version, verified_by, verified_at, initiated_by "
        "FROM critical_care_infusions WHERE id=:i AND lab_id=:l",
        i=INFUSION_ID, l=LAB_ID,
    )
    assert rows, "the seeded infusion disappeared"
    return rows[0]


def _audit_count(Session: Any) -> int:
    return harness.committed(
        Session, "SELECT count(*) AS n FROM audit_logs WHERE lab_id=:l AND action=:a",
        l=LAB_ID, a=AUDIT_ACTION,
    )[0]["n"]


def _receipts(Session: Any, key: str) -> list[dict[str, Any]]:
    return harness.receipts(Session, lab_id=LAB_ID, operation=OPERATION, key=key)


# ---------------------------------------------------------------------------
# 1. Authentication
# ---------------------------------------------------------------------------


def test_01_unauthenticated_caller_is_rejected(Session: Any, seeded: Any) -> None:
    """``actor=None`` leaves the real dependency in place, so this is a real 401."""
    r = _post(Session, None, key="final-unauth")
    assert r.status_code == 401, f"{r.status_code}: {r.text}"
    assert _state(Session)["status"] == "awaiting_verification"


# ---------------------------------------------------------------------------
# 2. Authorization
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("role", NON_ADMIN_ROLES)
def test_02_role_without_system_admin_is_rejected(Session: Any, seeded: Any, role: str) -> None:
    r = _post(Session, harness.Actor(user_id=VERIFIER_ID, lab_id=LAB_ID, role=role),
              key=f"final-role-{role}")
    assert r.status_code == 403, f"{role} got {r.status_code}: {r.text}"
    assert _state(Session)["status"] == "awaiting_verification", f"{role} changed state"


# ---------------------------------------------------------------------------
# 3. Tenant isolation
# ---------------------------------------------------------------------------


def test_03_cross_tenant_actor_cannot_see_or_mutate_the_infusion(
    Session: Any, seeded: Any
) -> None:
    """404, not 403: the answer must be indistinguishable from the row not existing,
    or it confirms to a foreign tenant that this patient's infusion is real."""
    r = _post(Session, _actor(user_id=VERIFIER_ID, lab_id=OTHER_LAB_ID), key="final-cross")
    assert r.status_code == 404, f"{r.status_code}: {r.text}"
    assert _state(Session)["status"] == "awaiting_verification"


# ---------------------------------------------------------------------------
# 4. Ownership — the clinical rule this endpoint exists for
# ---------------------------------------------------------------------------


def test_04_the_initiator_cannot_verify_their_own_high_alert_infusion(
    Session: Any, seeded: Any
) -> None:
    """INV-ICU-01. If this yields, the second-actor control is decorative."""
    before = _state(Session)
    r = _post(Session, _actor(user_id=INITIATOR_ID), key="final-self")
    assert r.status_code == 422, f"the initiator was allowed through: {r.status_code} {r.text}"
    assert "independent" in r.text.lower(), f"unexpected refusal reason: {r.text}"
    after = _state(Session)
    assert (after["status"], after["version"]) == (before["status"], before["version"])
    assert after["verified_by"] is None and after["verified_at"] is None


# ---------------------------------------------------------------------------
# 5. Valid transition
# ---------------------------------------------------------------------------


def test_05_an_independent_verifier_activates_the_infusion(Session: Any, seeded: Any) -> None:
    baseline = _audit_count(Session)
    key = "final-happy"
    r = _post(Session, _actor(), key=key)
    assert r.status_code == 200, f"{r.status_code}: {r.text}"

    after = _state(Session)
    assert after["status"] == "active"
    assert after["version"] == 2, f"optimistic lock did not advance: {after}"
    assert after["verified_by"] == str(VERIFIER_ID), after
    assert after["verified_at"] is not None
    assert after["verified_by"] != after["initiated_by"], (
        "the verifier and the initiator are the same actor"
    )
    assert len(_receipts(Session, key)) == 1
    assert _audit_count(Session) == baseline + 1, "the successful activation was not audited"


# ---------------------------------------------------------------------------
# 6. Invalid transition
# ---------------------------------------------------------------------------


def test_06_an_already_active_infusion_cannot_be_verified_again(
    Session: Any, seeded: Any
) -> None:
    assert _post(Session, _actor(), key="final-first").status_code == 200
    settled = _state(Session)

    r = _post(Session, _actor(user_id=SECOND_VERIFIER_ID), key="final-second",
              if_match=str(settled["version"]))
    assert r.status_code in (409, 422), f"a second activation was accepted: {r.status_code} {r.text}"
    after = _state(Session)
    assert (after["status"], after["version"], after["verified_by"]) == (
        settled["status"], settled["version"], settled["verified_by"]
    ), f"the refused attempt still changed state: {settled} -> {after}"


# ---------------------------------------------------------------------------
# 7-8. If-Match
# ---------------------------------------------------------------------------


def test_07_a_missing_if_match_is_refused_with_its_own_status(Session: Any, seeded: Any) -> None:
    r = _post(Session, _actor(), key="final-no-ifmatch", if_match=None)
    assert r.status_code == 428, f"{r.status_code}: {r.text}"
    assert _state(Session)["status"] == "awaiting_verification"


def test_08_a_stale_if_match_is_refused(Session: Any, seeded: Any) -> None:
    r = _post(Session, _actor(), key="final-stale", if_match="99")
    assert r.status_code == 409, f"{r.status_code}: {r.text}"
    assert _state(Session)["status"] == "awaiting_verification"


# ---------------------------------------------------------------------------
# 9-10. Idempotency and replay
# ---------------------------------------------------------------------------


def test_09_a_missing_idempotency_key_is_refused(Session: Any, seeded: Any) -> None:
    r = _post(Session, _actor(), key=None)
    assert r.status_code == 400, f"{r.status_code}: {r.text}"
    assert _state(Session)["status"] == "awaiting_verification"


def test_10_a_replay_of_the_same_key_is_refused_not_repeated(Session: Any, seeded: Any) -> None:
    """The clinically important one: a retried request must not verify twice."""
    key = "final-replay"
    assert _post(Session, _actor(), key=key).status_code == 200
    after_first = _state(Session)

    replay = _post(Session, _actor(), key=key, if_match=str(after_first["version"]))
    assert replay.status_code in (409, 422), (
        f"the replay was executed rather than refused: {replay.status_code} {replay.text}"
    )
    assert _state(Session) == after_first, "the replay changed durable state"
    assert len(_receipts(Session, key)) == 1, "the replay created a second receipt"


# ---------------------------------------------------------------------------
# 11. Concurrent actors — exactly one durable effect
# ---------------------------------------------------------------------------


def test_11_two_concurrent_verifiers_produce_exactly_one_activation(
    Session: Any, seeded: Any
) -> None:
    """Two *different* actors, so the per-actor receipt cannot serialise them
    (INV-IDEM-02).  Only the row lock can, which is what is under test."""
    before = _state(Session)
    assert before["version"] == 1

    def attempt(user_id: int, key: str):
        own = harness.session_factory(pool_size=2)
        try:
            return _post(own, _actor(user_id=user_id), key=key, if_match="1").status_code
        finally:
            harness.dispose(own)

    first, second = harness.race(
        lambda: attempt(VERIFIER_ID, "final-race-a"),
        lambda: attempt(SECOND_VERIFIER_ID, "final-race-b"),
    )
    outcomes = sorted([first, second])
    assert outcomes.count(200) == 1, f"expected exactly one success, got {outcomes}"
    assert all(c in (200, 409, 422) for c in outcomes), f"unexpected outcomes {outcomes}"

    after = _state(Session)
    assert after["status"] == "active"
    assert after["version"] == 2, f"two writers advanced the version twice: {after}"
    assert after["verified_by"] in (str(VERIFIER_ID), str(SECOND_VERIFIER_ID))


# ---------------------------------------------------------------------------
# 12. Audit persistence
# ---------------------------------------------------------------------------


def test_12_the_activation_is_audited_and_the_history_cannot_be_deleted(
    Session: Any, seeded: Any
) -> None:
    baseline = _audit_count(Session)
    assert _post(Session, _actor(), key="final-audit").status_code == 200
    assert _audit_count(Session) == baseline + 1

    rows = harness.audit_rows(Session, lab_id=LAB_ID, action=AUDIT_ACTION)
    assert rows, "no audit row for the activation"
    latest = rows[-1]
    assert str(latest["user_id"]) == str(VERIFIER_ID), latest
    assert latest["resource_type"] == "icu_infusion", latest
    assert latest["chain_hash"], "the audit row carries no chain hash"

    # Which infusion was verified is recorded in ``details``, not in the indexed
    # ``resource_id`` column.  That is not a slip: ``audit_logs.resource_id`` is
    # INTEGER while all thirteen ``critical_care_*`` tables have VARCHAR primary
    # keys, so ``ClinicalCommandGuard._audit_resource_id`` returns None for a
    # non-numeric id and the guard preserves the real value in the JSON instead.
    # Asserted as it actually is, and pinned — see test_17.
    assert latest["resource_id"] is None, (
        f"resource_id is now populated ({latest['resource_id']!r}); the recorded "
        "finding is stale and the audit contract must be re-measured"
    )
    details = latest["details"]
    if isinstance(details, str):
        details = json.loads(details)
    assert details.get("resource_id") == INFUSION_ID, (
        f"the infusion identity is absent from the audit row entirely: {details}"
    )
    assert details.get("state_before") == "awaiting_verification"
    assert details.get("state_after") == "active"
    assert details.get("version_before") == 1 and details.get("version_after") == 2

    # The refusal is enforced below the application, where it cannot be bypassed.
    from sqlalchemy.exc import DatabaseError

    with pytest.raises(DatabaseError) as refused, Session() as s:
        s.execute(text("DELETE FROM audit_logs WHERE lab_id=:l"), {"l": LAB_ID})
        s.commit()
    assert "append-only" in str(refused.value), str(refused.value)


# ---------------------------------------------------------------------------
# 13. Rollback on a real in-transaction failure
# ---------------------------------------------------------------------------


def test_13_a_failed_command_leaves_no_partial_clinical_effect(
    Session: Any, seeded: Any
) -> None:
    """The independent-actor violation fails *inside* the transaction, after the
    guard has claimed and after the row was locked.  Nothing may survive it.

    The failure *does* leave a durable trace on this lineage — see test_18, which
    asserts it positively. NR-024's "a failing protected command writes nothing"
    was measured when the database itself was the failure (``UndefinedColumn``), so
    ``guard.reject`` shared the broken dependency it was trying to record. An
    ordinary clinical refusal is audited. That distinction is recorded rather than
    left as a blanket claim.
    """
    before = _state(Session)
    key = "final-rollback"
    r = _post(Session, _actor(user_id=INITIATOR_ID), key=key)
    assert r.status_code == 422

    after = _state(Session)
    assert after == before, f"a failed command changed durable state: {before} -> {after}"
    assert harness.committed(
        Session,
        "SELECT count(*) AS n FROM critical_care_infusions "
        "WHERE id=:i AND status='active'", i=INFUSION_ID,
    )[0]["n"] == 0


# ---------------------------------------------------------------------------
# 14. Retry behaviour
# ---------------------------------------------------------------------------


def test_14_a_retry_after_a_precondition_failure_succeeds_with_a_fresh_key(
    Session: Any, seeded: Any
) -> None:
    """A client that gets a 409 for a stale If-Match must be able to re-read and
    retry.  A lockout-style dead end here would strand a clinical action."""
    assert _post(Session, _actor(), key="final-retry-stale", if_match="99").status_code == 409
    current = _state(Session)
    assert current["status"] == "awaiting_verification"

    retried = _post(Session, _actor(), key="final-retry-ok",
                    if_match=str(current["version"]))
    assert retried.status_code == 200, f"the corrected retry was refused: {retried.text}"
    assert _state(Session)["status"] == "active"


# ---------------------------------------------------------------------------
# 15. Regression guards — the schema conditions this proof depends on
# ---------------------------------------------------------------------------


def test_15_the_verification_columns_exist_and_the_table_does_not_drift(
    Session: Any
) -> None:
    """If this fails, every positive result above is unreachable, so it is asserted
    explicitly rather than assumed from the fact that the tests passed."""
    physical = harness.physical_columns(Session, "critical_care_infusions")
    assert {"verified_by", "verified_at"} <= physical, sorted(physical)

    from app.critical_care.infrastructure.models import ContinuousInfusionModel

    missing = harness.missing_physical_columns(Session, ContinuousInfusionModel)
    assert missing == set(), f"critical_care_infusions drifts from its ORM by {sorted(missing)}"


def test_16_the_database_under_test_was_built_by_migrations(Session: Any) -> None:
    """A ``create_all`` database would make the drift check above vacuous."""
    stamp = harness.committed(Session, "SELECT version_num FROM alembic_version")
    assert stamp, "no alembic_version row: this database was not built by migrations"
    assert stamp[0]["version_num"] == "20260909_0001", (
        f"expected canonical head 20260909_0001, found {stamp[0]['version_num']}"
    )


# ---------------------------------------------------------------------------
# 17-18. Findings this proof turned up, pinned so they cannot drift silently
# ---------------------------------------------------------------------------


def test_17_clinical_audit_rows_cannot_use_the_indexed_resource_id_column(
    Session: Any,
) -> None:
    """``audit_logs.resource_id`` is INTEGER; every clinical resource id is a string.

    This is a schema-shape limitation with a deliberate compensation, not a coding
    slip: the guard's ``_audit_resource_id`` docstring says as much, and the true id
    goes into ``details``. The consequence is still concrete — no audit query can
    filter clinical events by ``resource_id``, for any of the thirteen
    ``critical_care_*`` tables, and a reviewer who writes the obvious query gets
    silence rather than an error.
    """
    audit_type = harness.committed(
        Session,
        "SELECT data_type FROM information_schema.columns "
        "WHERE table_name='audit_logs' AND column_name='resource_id'",
    )
    assert audit_type and audit_type[0]["data_type"] == "integer", (
        f"audit_logs.resource_id is no longer integer ({audit_type}); re-measure the "
        "finding and retire this pin"
    )
    string_keyed = harness.committed(
        Session,
        "SELECT count(*) AS n FROM information_schema.columns "
        "WHERE column_name='id' AND table_name LIKE 'critical_care%' "
        "AND data_type='character varying'",
    )[0]["n"]
    assert string_keyed == 13, f"expected 13 string-keyed ICU tables, found {string_keyed}"


def test_18_a_refused_command_is_audited_with_its_clinical_reason(
    Session: Any, seeded: Any
) -> None:
    """A refused high-alert verification must be reconstructable afterwards.

    This is the positive form of what NR-024 recorded as missing. It is asserted
    here because the refusal path is the one a safety investigation reads: who
    attempted it, on what, and why it was stopped.
    """
    rejected_action = f"{AUDIT_ACTION}.rejected"
    baseline = harness.committed(
        Session, "SELECT count(*) AS n FROM audit_logs WHERE lab_id=:l AND action=:a",
        l=LAB_ID, a=rejected_action,
    )[0]["n"]

    assert _post(Session, _actor(user_id=INITIATOR_ID), key="final-reject-audit").status_code == 422

    rows = harness.audit_rows(Session, lab_id=LAB_ID, action=rejected_action)
    assert len(rows) == baseline + 1, (
        "the refused command left no audit row; NR-024 applies to this path after all"
    )
    latest = rows[-1]
    assert str(latest["user_id"]) == str(INITIATOR_ID), latest
    details = latest["details"]
    if isinstance(details, str):
        details = json.loads(details)
    assert "independent clinical actor" in (details.get("reason") or ""), details
    assert details.get("resource_id") == INFUSION_ID, details
    assert details.get("state_before") == "awaiting_verification", details
