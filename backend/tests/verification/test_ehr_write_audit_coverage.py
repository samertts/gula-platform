"""NR-082 — every EHR clinical write must leave an attributable audit row.

CLAUDE.md Security Invariant #2 is *"All mutations MUST write to the audit log"*.
Reconnaissance (docs/architecture/NR-070-ehr-route-reconnaissance.md §4) measured
52 of 55 EHR write routes writing no audit row by any mechanism. It also called
the repair "one decorator line per route", and that was wrong in two ways this
module pins:

* the decorator read the actor from ``request.state.user_id`` / ``.lab_id``, and
  **nothing in app/ ever sets either** -- ``middleware.py:153`` sets only
  ``request_id``. Every row it wrote was user 0 of lab 0, which also made those
  rows invisible to ``fhir_search_provenance``, whose filter is
  ``AuditLog.lab_id == current_user.lab_id``;
* none of the 51 ``ehr.py`` write routes declares a ``request`` parameter, so the
  decorator's ``if request and db`` guard would have written **nothing at all**
  while the routes looked audited. A silent no-op is the worst outcome available.

So the assertions here deliberately ratchet both ways: not merely that a row
exists, but that it carries the real actor, the real tenant, the real role and a
resource type that is not mislabelled.

SCOPE THIS CANNOT PROVE, stated so no one reads more into it: **no migration
creates any ``ehr_*`` table** -- 0 of 101 migration files, and 0 such tables in
every verification database. The 51 routes therefore cannot be exercised over
HTTP against a migrated database at all; that is NR-079's uncreatable-table
ledger, not this finding. What is proven here is the mechanism, against real
PostgreSQL, plus a structural ratchet over the whole route surface.
"""

from __future__ import annotations

import ast
import json
import pathlib
import uuid

import pytest
from app.audit import audit_log
from sqlalchemy import text

from tests.verification.harness import dispose, requires_postgres, session_factory

_EHR_ROUTES = pathlib.Path(__file__).resolve().parents[2] / "app" / "routes" / "ehr.py"
_FHIR_ROUTES = pathlib.Path(__file__).resolve().parents[2] / "app" / "routes" / "ehr_fhir.py"

#: The real EHR model class names. A resource_type outside this set would be an
#: invented classification rather than the record's own type.
_EHR_MODEL_CLASSES = {
    "AllergyIntolerance", "CarePlan", "CarePlanActivity", "CarePlanGoal",
    "ClinicalAttachment", "ClinicalNote", "ConditionRecord", "DiagnosisRecord",
    "FamilyHistoryRecord", "ImmunizationRecord", "MedicationAdministration",
    "MedicationDispense", "MedicationRequest", "MedicationStatement",
    "PatientTimelineEvent", "ProblemListItem", "RiskFactorRecord",
    "SocialHistoryRecord",
}

#: audit_logs.action and .resource_type are both VARCHAR(50) in PostgreSQL. An
#: over-long action would fail the INSERT at runtime, not at import.
_ACTION_COLUMN_WIDTH = 50


def _write_routes(path: pathlib.Path) -> list[tuple[ast.FunctionDef, list[ast.expr]]]:
    """Every non-GET router-decorated function, with its decorator list."""
    tree = ast.parse(path.read_text())
    out = []
    for fn in tree.body:
        if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        methods = [
            d.func.attr.lower()
            for d in fn.decorator_list
            if isinstance(d, ast.Call)
            and isinstance(d.func, ast.Attribute)
            and isinstance(d.func.value, ast.Name)
            and d.func.value.id == "router"
        ]
        if methods and methods != ["get"]:
            out.append((fn, fn.decorator_list))
    return out


def _audit_decorator(decorators: list[ast.expr]) -> ast.Call | None:
    for d in decorators:
        if isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "audit_log":
            return d
    return None


def _kwarg(call: ast.Call, name: str) -> str | None:
    for k in call.keywords:
        if k.arg == name and isinstance(k.value, ast.Constant):
            return k.value.value
    return None


def _branch_on_batch_commits(fn: ast.FunctionDef) -> bool:
    """True when some ``if ... "batch" ...`` branch commits inside its own body.

    Read out of the tree rather than matched against ``ast.unparse`` output: that
    normalises every string literal to single quotes, so a search for
    ``'bundle_type == "batch"'`` silently never matches. It cost this test a
    false failure, which is the cheap version of the same mistake a source-grep
    ratchet makes when it passes on a commented-out line.
    """
    for node in ast.walk(fn):
        if not isinstance(node, ast.If):
            continue
        compares_batch = any(
            isinstance(c, ast.Constant) and c.value == "batch"
            for c in ast.walk(node.test)
        )
        if not compares_batch:
            continue
        commits = any(
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Attribute)
            and inner.func.attr == "commit"
            for stmt in node.body
            for inner in ast.walk(stmt)
        )
        if commits:
            return True
    return False


# ── Structural ratchet over the whole surface ──────────────────────────────


def test_every_ehr_clinical_write_route_carries_an_audit_decorator():
    routes = _write_routes(_EHR_ROUTES)
    assert len(routes) == 51, f"the EHR write surface changed: {len(routes)} write routes, expected 51"
    unaudited = [fn.name for fn, decs in routes if _audit_decorator(decs) is None]
    assert unaudited == [], f"clinical writes with no audit row (Invariant #2): {unaudited}"


def test_each_audit_action_names_its_own_resource_and_verb():
    """A shared action string would make 51 routes indistinguishable in the log."""
    seen: dict[str, str] = {}
    for fn, decs in _write_routes(_EHR_ROUTES):
        call = _audit_decorator(decs)
        assert call is not None
        action = _kwarg(call, "action")
        resource_type = _kwarg(call, "resource_type")
        assert action and action.startswith("ehr."), f"{fn.name}: action {action!r} is not namespaced"
        assert action.count(".") == 2, f"{fn.name}: action {action!r} is not ehr.<resource>.<verb>"
        verb = action.rsplit(".", 1)[1]
        assert verb in {"create", "update", "soft_delete"}, f"{fn.name}: unknown verb {verb!r}"
        if fn.name.startswith("delete_"):
            # All 18 DELETE routes are soft deletes. An action reading "delete"
            # would claim a hard delete the PERMANENT DATA RULE forbids.
            assert verb == "soft_delete", f"{fn.name} is a soft delete; its action must say so"
        assert len(action) <= _ACTION_COLUMN_WIDTH, f"{fn.name}: action exceeds VARCHAR(50)"
        assert resource_type in _EHR_MODEL_CLASSES, f"{fn.name}: {resource_type!r} is not an EHR model class"
        assert len(resource_type) <= _ACTION_COLUMN_WIDTH
        assert action not in seen, f"{fn.name} and {seen[action]} share the action {action!r}"
        seen[action] = fn.name
    assert len(seen) == 51


def test_the_router_decorator_stays_outside_the_audit_decorator():
    """Reversed, FastAPI would register the undecorated function and audit nothing."""
    for fn, decs in _write_routes(_EHR_ROUTES):
        names = [
            "router" if (isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                         and isinstance(d.func.value, ast.Name) and d.func.value.id == "router")
            else "audit" if (isinstance(d, ast.Call) and isinstance(d.func, ast.Name)
                             and d.func.id == "audit_log")
            else "other"
            for d in decs
        ]
        assert names.index("router") < names.index("audit"), (
            f"{fn.name}: @router must sit above @audit_log or the wrapper is never registered"
        )


def test_no_ehr_write_route_is_async_while_the_decorator_is_sync():
    """A sync wrapper around a coroutine returns it un-awaited and audits nothing."""
    for path in (_EHR_ROUTES, _FHIR_ROUTES):
        for fn, decs in _write_routes(path):
            if _audit_decorator(decs) is not None:
                assert not isinstance(fn, ast.AsyncFunctionDef), f"{fn.name} is async and decorated"


def test_the_fhir_write_routes_are_audited_and_batch_persists_on_its_own():
    """All four FHIR writes carry an audit row, which completes 55 of 55.

    ``fhir_batch`` was deliberately held back one commit: it committed only for
    ``type: "transaction"``, and ``body.get("type", "batch")`` defaults to
    ``batch``, whose entries were applied with ``db.add`` and never committed
    while the response reported ``201``. Decorating it in that state would have
    made the decorator's own ``db.commit()`` the thing that persisted a batch
    entry -- a data-integrity repair smuggled in as a side effect of an audit
    change. The two landed together instead, and the persistence contract is
    proven behaviourally in ``tests/test_fhir_batch_persistence.py`` (NR-084).

    The source check below is what keeps the pairing honest: if the batch path
    ever loses its own commit again, the audit commit silently becomes the only
    thing making a batch entry durable.
    """
    routes = _write_routes(_FHIR_ROUTES)
    assert len(routes) == 4, f"the FHIR write surface changed: {len(routes)} write routes, expected 4"
    unaudited = [fn.name for fn, decs in routes if _audit_decorator(decs) is None]
    assert unaudited == [], f"FHIR writes with no audit row (Invariant #2): {unaudited}"

    batch = [fn for fn, _ in routes if fn.name == "fhir_batch"]
    assert len(batch) == 1, "fhir_batch is gone or renamed; re-derive this pin"
    assert _branch_on_batch_commits(batch[0]), (
        "fhir_batch is audited without a commit of its own on the batch path: "
        "the audit commit would be what persists a batch entry"
    )


# ── Real-PostgreSQL proof of the mechanism ─────────────────────────────────


@requires_postgres()
class TestDecoratorAgainstRealPostgres:
    @pytest.fixture(autouse=True)
    def _session(self):
        Session = session_factory(pool_size=2)
        self.Session = Session
        yield
        dispose(Session)

    @staticmethod
    def _actor(lab_id: int = 4242):
        # No FK constrains audit_logs.user_id or .lab_id, so a synthetic actor
        # exercises attribution without seeding an unrelated tenant.
        from types import SimpleNamespace
        return SimpleNamespace(id=97531, lab_id=lab_id, role="physician")

    def _row(self, db, action: str):
        return db.execute(
            text("SELECT user_id, user_role, lab_id, resource_type, resource_id, details "
                 "FROM audit_logs WHERE action = :a"),
            {"a": action},
        ).all()

    def test_a_clinical_write_is_attributed_to_its_real_actor_and_tenant(self):
        action = f"t.{uuid.uuid4().hex[:20]}"
        record_id = uuid.uuid4().hex.upper()[:26]

        @audit_log(action=action, resource_type="ClinicalNote")
        def endpoint(*, current_user, db):
            return {"id": record_id}

        with self.Session() as db:
            endpoint(current_user=self._actor(), db=db)
        with self.Session() as db:
            rows = self._row(db, action)

        assert len(rows) == 1, "the decorator wrote no audit row"
        user_id, user_role, lab_id, resource_type, resource_id, details = rows[0]
        # Ratchet both ways: a row that exists but records user 0 of lab 0 is the
        # defect this repair closes, not evidence that it is closed.
        assert user_id == 97531, f"actor not recorded: user_id={user_id}"
        assert user_id != 0
        assert lab_id == 4242, f"tenant not recorded: lab_id={lab_id}"
        assert lab_id != 0
        assert user_role == "physician", f"role not recorded: {user_role!r}"
        assert resource_type == "ClinicalNote", "a clinical note must not be labelled a FHIR resource"
        assert resource_id is None, "a 26-char ULID must not be forced into an INTEGER column"
        assert json.loads(details)["record_id"] == record_id

    def test_an_unattributable_mutation_is_refused_not_written_as_user_zero(self):
        action = f"t.{uuid.uuid4().hex[:20]}"

        @audit_log(action=action, resource_type="ClinicalNote")
        def endpoint(*, db):
            return {"id": "01ARZ3NDEKTSV4RRFFQ69G5FAV"}

        with self.Session() as db, pytest.raises(RuntimeError, match="no authenticated actor"):
            endpoint(db=db)
        with self.Session() as db:
            assert self._row(db, action) == [], "an anonymous audit row was written anyway"

    def test_a_fhir_row_keeps_the_two_keys_provenance_search_reads(self):
        """``fhir_search_provenance`` matches on details.fhir_resource_type/_id."""
        action = f"t.{uuid.uuid4().hex[:20]}"

        @audit_log(action=action)  # resource_type defaults to "FHIR"
        def endpoint(*, current_user, db):
            return {"resourceType": "Condition", "id": "condition-77"}

        with self.Session() as db:
            endpoint(current_user=self._actor(), db=db)
        with self.Session() as db:
            rows = self._row(db, action)

        assert len(rows) == 1
        details = json.loads(rows[0][5])
        assert rows[0][3] == "FHIR"
        assert details["fhir_resource_type"] == "Condition"
        assert details["fhir_resource_id"] == "condition-77"
        # And the tenant is now real, which is what makes the row reachable:
        # the Provenance filter is lab_id == current_user.lab_id.
        assert rows[0][2] == 4242

    def test_a_clinical_row_is_not_given_fhir_detail_keys(self):
        action = f"t.{uuid.uuid4().hex[:20]}"

        @audit_log(action=action, resource_type="MedicationAdministration")
        def endpoint(*, current_user, db):
            return {"id": "01ARZ3NDEKTSV4RRFFQ69G5FAV"}

        with self.Session() as db:
            endpoint(current_user=self._actor(), db=db)
        with self.Session() as db:
            rows = self._row(db, action)

        details = json.loads(rows[0][5])
        assert "fhir_resource_type" not in details, "a medication administration is not a FHIR resource"
        assert "fhir_resource_id" not in details


def test_the_decorator_refuses_to_wrap_an_async_endpoint():
    with pytest.raises(TypeError, match="async endpoint"):
        @audit_log(action="t.async", resource_type="ClinicalNote")
        async def endpoint(*, current_user, db):  # pragma: no cover - never called
            return {}
