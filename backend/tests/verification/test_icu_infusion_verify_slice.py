"""Vertical slice: independent verification of a high-alert ICU infusion.

Why this operation was chosen.  ``POST /critical-care/infusions/{id}/verify``
carries, in one request, every control this verification layer exists to test:
a state transition (``awaiting_verification`` -> ``active``), an authorization
boundary, a tenant predicate, a row lock, an optimistic version, a durable
idempotency claim, an audit write, and one clinical rule that no generic
framework could infer — a high-alert infusion may only be activated by a
clinical actor *other than* the one who started it.  That is the second-nurse
check, expressed in code as ``verified_by != initiated_by``.

``critical_care`` also had, before this file, eight guarded clinical commands
and zero real-PostgreSQL tests: the highest ratio of protected clinical writes
to executed evidence in the platform.

What the run found.  On a database built by migrations, the operation cannot
execute at all.  ``critical_care_infusions`` has no ``verified_by`` and no
``verified_at`` column, because the migration that adds them
(``20260820_0005_icu_infusion_independent_verification``) sits on a branch that
only ``head`` reaches, and ``head`` cannot be applied — it fails earlier at the
pharmacy primary-key divergence, NR-003.  The route's first statement is a
``SELECT ... FOR UPDATE`` of the whole ORM row, so it raises ``UndefinedColumn``
before the guard, the version check, the tenant check or the clinical rule is
ever reached.

That makes most of the tests below *tripwires*: they assert the defective
behaviour that is true today, and say so in their own names and docstrings.
They are not an acceptance of it.  Each one fails the moment the schema is
repaired, which forces this file to be rewritten to the correct expectation
rather than quietly passing on a half-fixed system.  The two tests that are not
tripwires — the authorization boundary — pass on their merits, because that
control sits outside the handler and therefore still works.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from app.critical_care.infrastructure.models import ContinuousInfusionModel
from sqlalchemy import text

from . import harness

pytestmark = harness.requires_postgres()

# Synthetic identifiers, far outside any real range, so a mistaken run against a
# populated database touches nothing that exists.
LAB_ID = 994101
OTHER_LAB_ID = 994102
INITIATOR_ID = 74101
VERIFIER_ID = 74102
BED_ID = "verif-icu-bed"
ADMISSION_ID = "verif-icu-admission"
INFUSION_ID = "verif-icu-infusion"
PATIENT_ID = "verif-icu-patient"
HIGH_ALERT_MEDICATION = "norepinephrine"
OPERATION = "icu.infusion.verify"
AUDIT_ACTION = "clinical.icu.infusion.verify"
ENDPOINT = f"/critical-care/infusions/{INFUSION_ID}/verify"


def _purge(Session: Any) -> None:
    """Remove this module's synthetic rows.

    ``audit_logs`` is deliberately absent from this list.  The database refuses
    to delete from it — a ``audit_logs_deny_mutation`` trigger raises
    ``audit_logs is append-only: DELETE operation is not permitted`` — which is a
    control working exactly as intended and is proven on its own below.  Audit
    assertions here are therefore deltas against a baseline captured at setup,
    never absolute counts.
    """
    with Session() as session:
        for lab in (LAB_ID, OTHER_LAB_ID):
            session.execute(text("DELETE FROM clinical_command_receipts WHERE lab_id=:l"), {"l": lab})
            session.execute(text("DELETE FROM critical_care_infusions WHERE lab_id=:l"), {"l": lab})
            session.execute(text("DELETE FROM critical_care_admissions WHERE lab_id=:l"), {"l": lab})
            session.execute(text("DELETE FROM critical_care_beds WHERE lab_id=:l"), {"l": lab})
            session.execute(text("DELETE FROM lab_users WHERE lab_id=:l"), {"l": lab})
            session.execute(text("DELETE FROM labs WHERE id=:l"), {"l": lab})
        session.commit()


@pytest.fixture(scope="module")
def Session() -> Any:
    factory = harness.session_factory()
    _purge(factory)
    now = datetime.now(UTC)
    with factory() as session:
        for lab, name in ((LAB_ID, "Verification ICU Lab"), (OTHER_LAB_ID, "Verification Foreign Lab")):
            session.execute(
                text("INSERT INTO labs (id,name,is_active) VALUES (:i,:n,true)"), {"i": lab, "n": name}
            )
        for uid, nm in ((INITIATOR_ID, "Verification Initiator"), (VERIFIER_ID, "Verification Verifier")):
            session.execute(
                text(
                    "INSERT INTO lab_users (id,lab_id,name,email,password_hash,role,is_active,perm_version)"
                    " VALUES (:i,:l,:n,:e,'!synthetic-only','master_admin',true,1)"
                ),
                {"i": uid, "l": LAB_ID, "n": nm, "e": f"verif-{uid}@example.invalid"},
            )
        session.execute(
            text(
                "INSERT INTO critical_care_beds (id,lab_id,bed_label,icu_type,has_infusion_pump,has_monitor,"
                "is_occupied,is_active,is_deleted,version,created_at,updated_at)"
                " VALUES (:i,:l,'B1','adult_icu',true,true,true,true,false,1,:t,:t)"
            ),
            {"i": BED_ID, "l": LAB_ID, "t": now},
        )
        session.execute(
            text(
                "INSERT INTO critical_care_admissions (id,lab_id,patient_id,bed_id,status,icu_type,"
                "admission_type,is_deleted,version,created_at,updated_at)"
                " VALUES (:i,:l,:p,:b,'stable','adult_icu','emergency',false,1,:t,:t)"
            ),
            {"i": ADMISSION_ID, "l": LAB_ID, "p": PATIENT_ID, "b": BED_ID, "t": now},
        )
        session.execute(
            text(
                "INSERT INTO critical_care_infusions (id,lab_id,patient_id,admission_id,medication,rate,"
                "start_time,initiated_by,status,is_deleted,version,created_at,updated_at)"
                " VALUES (:i,:l,:p,:a,:m,'5 ml/hr',:t,:ini,'awaiting_verification',false,1,:t,:t)"
            ),
            {
                "i": INFUSION_ID,
                "l": LAB_ID,
                "p": PATIENT_ID,
                "a": ADMISSION_ID,
                "m": HIGH_ALERT_MEDICATION,
                "t": now,
                "ini": str(INITIATOR_ID),
            },
        )
        session.commit()
    yield factory
    _purge(factory)
    harness.dispose(factory)


def _post(Session: Any, actor: harness.Actor | None, *, key: str, if_match: str | None = "1") -> Any:
    headers = {"Idempotency-Key": key}
    if if_match is not None:
        headers["If-Match"] = if_match
    try:
        with harness.client(Session, actor) as client:
            return client.post(ENDPOINT, headers=headers)
    finally:
        harness.clear_overrides()


def _authorized() -> harness.Actor:
    """The one role that holds ``system:admin``, which the ICU router requires."""
    return harness.Actor(user_id=VERIFIER_ID, lab_id=LAB_ID, role="master_admin")


def _infusion_state(Session: Any) -> dict[str, Any]:
    rows = harness.committed(
        Session,
        "SELECT status, version, initiated_by FROM critical_care_infusions WHERE id=:i",
        i=INFUSION_ID,
    )
    assert len(rows) == 1
    return rows[0]


# ---------------------------------------------------------------------------
# Invariants that hold.  These are not tripwires.
# ---------------------------------------------------------------------------


def test_unauthenticated_caller_is_rejected(Session: Any) -> None:
    """INV-AUTHN: activating a high-alert infusion requires authentication.

    The real ``get_current_user`` dependency is left in place here rather than
    overridden, so this is the production authentication path and not a stub.
    """
    response = _post(Session, None, key="VERIF-AUTHN")
    assert response.status_code == 401
    assert _infusion_state(Session)["status"] == "awaiting_verification"


@pytest.mark.parametrize("role", ["technician", "doctor", "lab_admin", "staff", "citizen"])
def test_role_without_system_admin_is_rejected(Session: Any, role: str) -> None:
    """INV-AUTHZ: the ICU router admits only a role holding ``system:admin``.

    Measured, not assumed: of the sixteen roles in ``EXTENDED_VALID_ROLES``,
    exactly one — ``master_admin`` — carries ``system:admin``.  Whether a
    bedside clinical platform *should* be reachable only by the platform's most
    privileged role is an authorization-model question recorded as a finding,
    not settled here.  What this test pins is that the boundary is enforced.
    """
    response = _post(Session, harness.Actor(VERIFIER_ID, LAB_ID, role), key=f"VERIF-ROLE-{role}")
    assert response.status_code == 403
    assert _infusion_state(Session)["status"] == "awaiting_verification"


def test_no_partial_effect_survives_the_failed_command(Session: Any) -> None:
    """INV-TXN: a command that fails leaves the clinical row exactly as it was.

    This holds for the right reason and is worth pinning independently of why
    the command fails: the transaction is rolled back, the status is unchanged
    and the version has not advanced, so no half-verified infusion exists.
    """
    _post(Session, _authorized(), key="VERIF-NO-PARTIAL")
    state = _infusion_state(Session)
    assert state["status"] == "awaiting_verification"
    assert state["version"] == 1
    assert state["initiated_by"] == str(INITIATOR_ID)


# ---------------------------------------------------------------------------
# Tripwires.  Each asserts today's defective behaviour and fails once fixed.
# ---------------------------------------------------------------------------


def test_tripwire_happy_path_returns_500_because_the_column_is_absent(Session: Any) -> None:
    """TRIPWIRE for NR-023.  The clinical control cannot execute at all.

    Correct behaviour is 200 with ``status='active'``, ``verified_by`` set to
    the second actor and ``version`` advanced to 2.  Observed behaviour is 500,
    because the route's opening ``SELECT ... FOR UPDATE`` selects every ORM
    column and two of them do not exist in the database.

    When the schema is repaired this test fails.  That is the point: the correct
    expectations then have to be written deliberately, with the real transition
    proven, rather than inherited from a suite that had quietly gone green.
    """
    response = _post(Session, _authorized(), key="VERIF-HAPPY")
    assert response.status_code == 500
    assert _infusion_state(Session)["status"] == "awaiting_verification"


def test_tripwire_cross_tenant_attempt_returns_500_instead_of_404(Session: Any) -> None:
    """TRIPWIRE for NR-023.  The tenant predicate is never reached.

    The route does filter on ``lab_id``, so the intended answer is 404 and the
    isolation is present in the source.  It cannot be *proven* today, because
    the statement carrying that filter is the statement that raises.  Recording
    tenant isolation as VERIFIED for this endpoint on the strength of reading
    the filter would be exactly the inference this layer exists to refuse.
    """
    foreign = harness.Actor(user_id=VERIFIER_ID, lab_id=OTHER_LAB_ID, role="master_admin")
    response = _post(Session, foreign, key="VERIF-CROSS-TENANT")
    assert response.status_code == 500
    assert _infusion_state(Session)["status"] == "awaiting_verification"


@pytest.mark.parametrize(
    ("label", "if_match"),
    [("absent", None), ("stale", "99")],
)
def test_tripwire_precondition_failures_return_500_instead_of_their_own_code(
    Session: Any, label: str, if_match: str | None
) -> None:
    """TRIPWIRE for NR-023.  Version preconditions are masked by the 500.

    ``require_expected_version`` is called after the row is loaded, so neither
    a missing ``If-Match`` nor a stale one can produce its own status code.
    The CAS invariant is therefore UNKNOWN for this endpoint, not satisfied.
    """
    response = _post(Session, _authorized(), key=f"VERIF-IFM-{label}", if_match=if_match)
    assert response.status_code == 500


def test_tripwire_a_failed_clinical_command_writes_no_receipt_and_no_audit(Session: Any) -> None:
    """TRIPWIRE for NR-024.  The failure itself is unrecorded.

    ``guard.claim`` never runs, so there is no durable claim, and the route's
    ``except`` branch calls ``guard.reject`` — which needs the same database and
    fails for the same reason — so there is no audit row either.  A clinician's
    repeated, failing attempts to activate a vasopressor infusion leave the
    platform with no evidence that anything was attempted.

    Both counts are asserted to be zero *and* the operation is asserted to have
    actually been attempted, so this cannot pass by accident on a run where no
    request was sent.
    """
    before = len(harness.audit_rows(Session, lab_id=LAB_ID, action=AUDIT_ACTION))
    response = _post(Session, _authorized(), key="VERIF-AUDIT-GAP")
    after = len(harness.audit_rows(Session, lab_id=LAB_ID, action=AUDIT_ACTION))
    assert response.status_code == 500
    assert harness.receipts(Session, lab_id=LAB_ID, operation=OPERATION, key="VERIF-AUDIT-GAP") == []
    # A delta, not an absolute count: audit rows cannot be deleted between runs,
    # so an absolute zero would only hold on a database nobody had used.
    assert after == before


def test_tripwire_the_orm_declares_two_columns_the_database_lacks(Session: Any) -> None:
    """TRIPWIRE for NR-023, stated as the drift itself rather than a symptom.

    Pinned exactly, not loosely.  Asserting ``drift != set()`` would keep
    passing if a third column went missing; asserting the precise pair means any
    change in either direction — a repair, or a new divergence — fails here and
    has to be looked at.
    """
    drift = harness.missing_physical_columns(Session, ContinuousInfusionModel)
    assert drift == {"verified_by", "verified_at"}


# ---------------------------------------------------------------------------
# Scenarios that cannot be attempted yet, recorded as such.
# ---------------------------------------------------------------------------


def test_concurrency_and_idempotency_remain_unproven_for_this_operation(Session: Any) -> None:
    """The two invariants this slice most wanted to prove are still UNKNOWN.

    Racing two authorized actors at one infusion would today prove only that
    both receive 500, which says nothing about whether the row lock serialises a
    real contended transition.  Replaying one idempotency key would prove only
    that neither attempt created a claim.  Both remain UNKNOWN and must not be
    reported otherwise; the work packets record what will be run once the schema
    is repaired.

    This test asserts the precondition for that statement — that the operation
    is still unexecutable — so the claim of UNKNOWN is itself checked rather
    than asserted in prose alone.
    """
    first = _post(Session, _authorized(), key="VERIF-UNPROVEN")
    replay = _post(Session, _authorized(), key="VERIF-UNPROVEN")
    assert first.status_code == 500
    assert replay.status_code == 500
    assert harness.receipts(Session, lab_id=LAB_ID, operation=OPERATION, key="VERIF-UNPROVEN") == []


def test_the_audit_log_refuses_deletion_at_the_database_level(Session: Any) -> None:
    """INV-AUDIT-IMMUTABLE: audit history cannot be removed, by anyone.

    Found by accident and kept on purpose.  This module's own cleanup tried to
    delete its synthetic audit rows and the database refused:
    ``audit_logs_deny_mutation`` raises ``audit_logs is append-only: DELETE
    operation is not permitted``.  That is immutability enforced where it cannot
    be bypassed by application code, an ORM session or a direct SQL client.

    The assertion is on the refusal, not on a row count, so it holds on an empty
    table as well as a populated one.
    """
    from sqlalchemy.exc import InternalError

    with pytest.raises(InternalError) as raised, Session() as session:
        session.execute(text("DELETE FROM audit_logs WHERE lab_id = :l"), {"l": LAB_ID})
        session.commit()
    assert "append-only" in str(raised.value)
