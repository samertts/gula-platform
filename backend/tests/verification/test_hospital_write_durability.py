"""Hospital writes must actually persist, and their audit rows must be coherent.

Two defects on the same path, the second hidden behind the first.

NR-064 -- five ``log_action`` calls passed their arguments POSITIONALLY against
a signature of ``(db, action, resource_type, resource_id, user_id, user_role,
lab_id, details)``.  So ``resource_type`` received the new row's id,
``resource_id`` received the ``lab_id``, ``lab_id`` was never recorded at all,
and the request payload landed in ``user_role`` -- a varchar column, which
psycopg2 refused outright::

    (psycopg2.ProgrammingError) can't adapt type 'dict'

Every call to ``POST /hospital/`` was therefore a 500, as were campus creation,
hospital update, deactivation and appointment creation.

NR-065 -- with that crash removed, the next defect became visible: not one of
the 20 mutating methods in ``HospitalService`` called ``commit()``.  They
``flush()``, which assigns the primary key so the response body looks like a
successful creation, and ``get_db()`` then yields, rolls back only on
exception, and closes.  A flush without a commit is discarded when the request
ends, so the route returned a populated 201 for a row that never existed.

The ordering is the point: the crash MASKED the durability defect.  Fixing only
the audit call would have turned a visible 500 into a silent data-loss bug,
which is strictly worse.  Both are fixed together and both are asserted here.

WHY THE GUARDED METHODS MUST **NOT** COMMIT.

Five of the twenty run inside ``_run_hospital_command``'s ``ClinicalCommandGuard``:
it claims an idempotency receipt, runs the mutation, records completion, and only
then commits -- rolling back if completion fails.  A commit inside the mutation
would publish the clinical change before its receipt was recorded, and the
guard's rollback could no longer undo it.  So ``assign_bed``, ``discharge_bed``,
``transfer_bed``, ``update_operation_theater_status`` and
``complete_surgical_safety_checklist`` deliberately do not commit, and the last
test in this file pins that distinction in both directions.
"""

from __future__ import annotations

import ast
import pathlib
import uuid

import pytest
from sqlalchemy import text

from tests.verification import harness

pytestmark = harness.requires_postgres()

_SERVICE = pathlib.Path(__file__).resolve().parents[2] / "app" / "services" / "hospital_service.py"

# Methods whose transaction is owned by ClinicalCommandGuard, not by themselves.
_GUARD_OWNED = frozenset({
    "assign_bed",
    "discharge_bed",
    "transfer_bed",
    "update_operation_theater_status",
    "complete_surgical_safety_checklist",
})


@pytest.fixture
def Session():
    factory = harness.session_factory()
    yield factory
    harness.dispose(factory)


@pytest.fixture
def lab_id(Session):
    session = Session()
    try:
        return session.execute(text("SELECT id FROM labs ORDER BY id LIMIT 1")).scalar_one()
    finally:
        session.close()


@pytest.fixture
def created_codes(Session):
    """Track hospital codes this module creates, and deactivate them afterwards.

    GULA does not operationally delete business entities, so cleanup here sets
    is_deleted rather than issuing DELETE -- the same disposition the product's
    own deactivate path uses.
    """
    codes: list[str] = []
    yield codes
    session = Session()
    try:
        for code in codes:
            session.execute(
                text("UPDATE hospitals SET is_deleted = true, is_active = false WHERE code = :c"),
                {"c": code},
            )
        session.commit()
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Durability, proven across an independent connection
# ---------------------------------------------------------------------------


def test_creating_a_hospital_persists_beyond_the_request(Session, lab_id, created_codes):
    """The core claim: a 201 must mean the row is really there.

    The read is issued from a SEPARATE session factory -- its own engine and its
    own connection -- because a read on the request's own session would see the
    uncommitted flush and report success either way.
    """
    code = f"DUR{uuid.uuid4().hex[:8].upper()}"
    created_codes.append(code)
    actor = harness.Actor(user_id=1, lab_id=lab_id, role="admin")

    with harness.client(Session, actor) as api:
        response = api.post(
            "/hospital/",
            json={"code": code, "name": "Durability Probe", "hospital_type": "general"},
        )

    assert response.status_code == 201, response.text
    assert response.json()["code"] == code

    verifier = harness.session_factory()
    session = verifier()
    try:
        rows = session.execute(
            text("SELECT id, lab_id FROM hospitals WHERE code = :c"), {"c": code}
        ).fetchall()
        assert len(rows) == 1, (
            "the route returned 201 but an independent connection cannot see the "
            "row: the flush was never committed"
        )
    finally:
        session.close()
        harness.dispose(verifier)


def test_the_audit_row_for_that_creation_is_coherent(Session, lab_id, created_codes):
    """Each of the six misaligned fields is asserted individually.

    Before the fix this row could not be written at all; the values below are
    what the corrected keyword call records.
    """
    code = f"AUD{uuid.uuid4().hex[:8].upper()}"
    created_codes.append(code)
    actor = harness.Actor(user_id=1, lab_id=lab_id, role="hospital_admin")

    with harness.client(Session, actor) as api:
        response = api.post(
            "/hospital/",
            json={"code": code, "name": "Audit Probe", "hospital_type": "general"},
        )
    assert response.status_code == 201, response.text
    hospital_id = response.json()["id"]

    verifier = harness.session_factory()
    session = verifier()
    try:
        row = session.execute(
            text(
                "SELECT action, resource_type, resource_id, user_id, user_role, lab_id, details "
                "FROM audit_logs WHERE action = 'hospital.create' AND resource_id = :rid "
                "ORDER BY id DESC LIMIT 1"
            ),
            {"rid": hospital_id},
        ).fetchone()
        assert row is not None, "the creation wrote no audit row"
        action, resource_type, resource_id, user_id, user_role, audit_lab_id, details = row

        assert action == "hospital.create"
        # Was the hospital's id, in a column meant to name the kind of resource.
        assert resource_type == "hospital"
        # Was the lab_id.
        assert resource_id == hospital_id
        assert user_id == 1
        # Was the entire request payload dict, which psycopg2 could not adapt.
        assert user_role == "hospital_admin"
        # Was never recorded at all, so the audit trail had no tenant attribution.
        assert audit_lab_id == lab_id
        # This is where the payload belongs.
        assert details and code in details
    finally:
        session.close()
        harness.dispose(verifier)


def test_a_department_creation_also_persists(Session, lab_id, created_codes):
    """A second, non-audited write path -- durability is not specific to one method."""
    code = f"DEP{uuid.uuid4().hex[:8].upper()}"
    created_codes.append(code)
    actor = harness.Actor(user_id=1, lab_id=lab_id, role="admin")

    with harness.client(Session, actor) as api:
        hospital = api.post(
            "/hospital/",
            json={"code": code, "name": "Dept Parent", "hospital_type": "general"},
        )
        assert hospital.status_code == 201, hospital.text
        hospital_id = hospital.json()["id"]

        dept = api.post(
            f"/hospital/{hospital_id}/departments",
            json={"code": f"D{uuid.uuid4().hex[:6].upper()}", "name": "Cardiology"},
        )

    assert dept.status_code in (200, 201), dept.text
    dept_id = dept.json()["id"]

    verifier = harness.session_factory()
    session = verifier()
    try:
        found = session.execute(
            text("SELECT count(*) FROM hospital_departments WHERE id = :i"), {"i": dept_id}
        ).scalar_one()
        assert found == 1, "department returned success but did not persist"
    finally:
        session.close()
        harness.dispose(verifier)


# ---------------------------------------------------------------------------
# Static guards against recurrence
# ---------------------------------------------------------------------------


def _service_functions() -> dict[str, ast.AST]:
    tree = ast.parse(_SERVICE.read_text())
    out = {}
    for cls in tree.body:
        if isinstance(cls, ast.ClassDef):
            for fn in cls.body:
                if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[fn.name] = fn
    return out


def _calls(fn: ast.AST, attr: str) -> bool:
    return any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == attr
        for n in ast.walk(fn)
    )


def test_no_log_action_call_passes_its_arguments_positionally():
    """The defect class, banned outright.

    ``log_action`` takes eight parameters of which four are ids or names that
    read alike. Positional calls are how resource_type came to hold an id and
    user_role a dict, so every call site must name its arguments.
    """
    offenders = []
    for name, fn in _service_functions().items():
        for node in ast.walk(fn):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "log_action"
                and len(node.args) > 1  # db is legitimately positional
            ):
                offenders.append(f"{name} (line {node.lineno}): {len(node.args)} positional args")
    assert offenders == [], (
        "log_action called positionally -- this is exactly how resource_type came "
        "to hold a row id and user_role a payload dict:\n  " + "\n  ".join(offenders)
    )


def test_every_flushing_method_either_commits_or_is_guard_owned():
    """Durability, as a structural invariant rather than a one-off repair.

    Asserted in BOTH directions: a method that flushes must commit unless its
    transaction belongs to ClinicalCommandGuard, and a guard-owned method must
    NOT commit, because committing early would defeat the guard's rollback.
    """
    missing_commit, unexpected_commit = [], []
    for name, fn in _service_functions().items():
        if not _calls(fn, "flush"):
            continue
        commits = _calls(fn, "commit")
        if name in _GUARD_OWNED:
            if commits:
                unexpected_commit.append(name)
        elif not commits:
            missing_commit.append(name)

    assert missing_commit == [], (
        "these methods flush without committing, so their writes are discarded "
        "when the request ends:\n  " + "\n  ".join(sorted(missing_commit))
    )
    assert unexpected_commit == [], (
        "these methods run inside ClinicalCommandGuard and must not commit -- "
        "doing so publishes the change before its receipt and defeats the "
        "guard's rollback:\n  " + "\n  ".join(sorted(unexpected_commit))
    )


def test_the_guard_owned_set_still_matches_the_routes():
    """Keeps _GUARD_OWNED honest if a route stops using the guard.

    Without this, moving a method out of _run_hospital_command would silently
    exempt it from the durability requirement above.
    """
    routes = (_SERVICE.parent.parent / "routes" / "hospital.py").read_text()
    for name in _GUARD_OWNED:
        assert f"HospitalService.{name}" in routes, f"{name} is no longer called by the routes"
    assert "_run_hospital_command" in routes
