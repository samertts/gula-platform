"""NR-065 — the fifteen orchestration tables may not be built as declared.

NR-059 classified the 42 national task and workflow endpoints and left one
question open: is national orchestration a feature GULA ships, or scaffolding
that was generated and never removed? That question is product intent and is not
derivable from the repository.

Unit 3 asked the question the approved decision actually gates on -- *before
creating schema, confirm tenancy, confirm audit, confirm state-machine
semantics, confirm idempotency and concurrency* -- and the answer does not
depend on product intent at all:

    tenancy    1 of 15 tables carries a tenant column (national_workflow_executions).
               The task list path filters on status, priority, category, assignee,
               queue_id and title, and on nothing else, because there is nothing
               else to filter on.
    audit      0 canonical audit calls in either package. `national_task_audit_logs`
               is a local status log -- task_id, action, actor_id, previous_status,
               new_status -- with no chain hash, no previous-hash link and no
               off-database anchor. It is not the hash-chained AuditLog that
               CLAUDE.md requires, and it carries no tenant either.
    concurrency  no idempotency key and no row locking anywhere in a package that
               contains a saga engine and a workflow state machine.

All fifteen extend `BaseEntity`, which is the one national base that has neither
`TenantMixin` nor `AuditMixin` -- `TenantEntity`, `AuditEntity` and
`TenantAuditEntity` all exist alongside it and were not used.

So this **corrects NR-059 §5**, which called shipping "the cheapest of the
NR-022-family decisions" on the grounds that ownership and implementation were
already in place. They are. Tenancy and audit are not. Building the fifteen as
declared would create a national-scale task and workflow surface where any
authorized caller lists every tenant's tasks and no mutation reaches the audit
chain -- CLAUDE.md security invariants #1 and #2, at national scale.

The invariant here is the same shape as NR-063: a precondition, not a
prohibition. Give these tables tenancy and audit, then build them. Either order
is fine. Only the omission fails.
"""

from __future__ import annotations

import ast
import pathlib
import re

from tests.orm_resolution import built_tables

BACKEND = pathlib.Path(__file__).resolve().parents[1]
APP = BACKEND / "app"

ORCHESTRATION_PACKAGES = (
    "app/national/task_engine",
    "app/national/workflow_runtime",
)

#: Columns that scope a row to a tenant. `assigned_to` and `created_by` are not
#: here on purpose: they say who, not whose.
_TENANT = frozenset({
    "lab_id", "tenant_id", "organization_id", "facility_id", "governorate_id",
})

#: Tokens that mean a package reaches the canonical hash-chained audit log.
#: Matched on a word boundary, which is load-bearing: plain substring matching
#: counts `TaskAuditLog(` -- this package's own local status log -- as a call to
#: the canonical `AuditLog(`, and the test silently passes on the very thing it
#: exists to reject. Found by negative proof, not by reading.
_AUDIT_TOKENS = (
    r"\blog_action\b", r"\baudit_service\b", r"\blog_access_decision\b",
    r"\bAuditLog\(", r"\brecord_audit\b", r"\bwrite_audit\b",
    r"\baudit_log\(",
)

#: Orchestration tables with no tenant column, measured at the time of writing.
#: Each is unbuilt, so this is latent. The ledger may shrink. It may never grow.
DECLARED_UNTENANTED_ORCHESTRATION_TABLES = frozenset({
    "national_saga_logs",
    "national_task_assignments",
    "national_task_audit_logs",
    "national_task_comments",
    "national_task_escalations",
    "national_task_queues",
    "national_task_sla_definitions",
    "national_tasks",
    "national_workflow_approvals",
    "national_workflow_compensations",
    "national_workflow_definitions",
    "national_workflow_execution_steps",
    "national_workflow_templates",
    "national_workflow_timers",
})


def _orchestration_models() -> dict[str, tuple[set[str], str]]:
    """table name -> (declared Column names, owning package)."""
    models: dict[str, tuple[set[str], str]] = {}
    for package in ORCHESTRATION_PACKAGES:
        for path in (BACKEND / package).rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
            except SyntaxError:
                continue
            for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
                table = None
                columns: set[str] = set()
                for stmt in cls.body:
                    if not isinstance(stmt, ast.Assign):
                        continue
                    target = stmt.targets[0]
                    if not isinstance(target, ast.Name):
                        continue
                    if target.id == "__tablename__" and isinstance(stmt.value, ast.Constant):
                        table = stmt.value.value
                    elif (
                        isinstance(stmt.value, ast.Call)
                        and getattr(stmt.value.func, "id", None) == "Column"
                    ):
                        columns.add(target.id)
                if table is not None:
                    models[table] = (columns, package)
    return models


def _built() -> set[str]:
    """NR-069. Resolved through the shared derivation, not the snapshot.

    This used to read `evidence-created-tables.json` directly, which is how it
    inherited the snapshot's three missing tables. One source of truth, derived
    from the migration chain.
    """
    return set(built_tables())


def _package_audits(package: str) -> bool:
    for path in (BACKEND / package).rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        if any(re.search(token, source) for token in _AUDIT_TOKENS):
            return True
    return False


def test_the_orchestration_surface_is_still_fifteen_tables() -> None:
    """Guard the guard: a scan finding nothing would gate nothing."""
    models = _orchestration_models()
    assert len(models) >= 15, (
        f"only {len(models)} orchestration tables found across "
        f"{ORCHESTRATION_PACKAGES}; the scan has drifted"
    )


def test_no_orchestration_table_is_built_without_tenant_scoping() -> None:
    """The precondition, and the reason this file exists.

    GULA is multi-tenant and CLAUDE.md invariant #1 requires every patient-data
    query to filter by the caller's tenant. Fourteen of these tables have no
    column to filter on, and the list path filters on none. Built as declared,
    one authorized caller would list every tenant's tasks.

    If a table appears here, the fix is not to delete this test. It is to give
    the table a tenant column and its queries a tenant filter first.
    """
    built = _built()
    live = sorted(
        table
        for table, (columns, _) in _orchestration_models().items()
        if table in built and not (columns & _TENANT)
    )
    assert live == [], (
        "these orchestration tables are built and carry no tenant column, so "
        "nothing scopes a row to a lab, facility or governorate. Add tenancy "
        f"before building them: {live}"
    )


def test_no_orchestration_table_is_built_without_canonical_audit() -> None:
    """CLAUDE.md invariant #2, applied before the schema exists rather than after.

    `national_task_audit_logs` is not a counter-example. It records a status
    transition; it has no chain hash, no link to the previous entry and no
    off-database anchor, so it is a log, not tamper-evident evidence.
    """
    built = _built()
    built_packages = {
        package
        for table, (_, package) in _orchestration_models().items()
        if table in built
    }
    offending = sorted(p for p in built_packages if not _package_audits(p))
    assert offending == [], (
        "these packages have tables built but contain no call reaching the "
        "hash-chained audit log, so national orchestration mutations would "
        f"leave no tamper-evident trail: {offending}"
    )


def test_the_untenanted_ledger_does_not_grow() -> None:
    """A new untenanted orchestration table is a new latent isolation gap."""
    current = {
        table
        for table, (columns, _) in _orchestration_models().items()
        if not (columns & _TENANT)
    }
    appeared = sorted(current - DECLARED_UNTENANTED_ORCHESTRATION_TABLES)
    assert appeared == [], (
        "new orchestration tables declare no tenant column. Use TenantEntity or "
        f"TenantAuditEntity rather than the bare BaseEntity: {appeared}"
    )


def test_the_untenanted_ledger_does_not_rot() -> None:
    """An entry that gained tenancy should be deleted, not left behind.

    Otherwise the ledger describes a codebase that no longer exists and the
    precondition above starts guarding a shrinking set by accident.
    """
    current = {
        table
        for table, (columns, _) in _orchestration_models().items()
        if not (columns & _TENANT)
    }
    resolved = sorted(DECLARED_UNTENANTED_ORCHESTRATION_TABLES - current)
    assert resolved == [], (
        "these tables now carry a tenant column, or no longer exist; remove "
        f"them from the ledger so it keeps describing the repository: {resolved}"
    )


#: The one tenant column in the orchestration surface, and the fact that makes
#: it not a counter-example: nothing populates it.
_VESTIGIAL_TENANT = ("national_workflow_executions", "tenant_id")

#: Packages whose routes would have to supply tenancy for it to be real.
_ORCHESTRATION_ROUTE_MODULES = (
    "app/national/task_engine/api/routes.py",
    "app/national/workflow_runtime/api/routes.py",
)


def test_the_one_tenant_column_is_still_never_populated() -> None:
    """NR-065, sharpened: the surface is not 1-of-15 tenanted. It is 0-of-15.

    `national_workflow_executions.tenant_id` exists, and `tenant_id` appears in
    exactly six places across both packages -- a domain-entity default, a service
    parameter defaulting to None, the value passed through to the model, and the
    column itself. **No route supplies it.** The routes derive `created_by` from
    `current_user.id` and stop there, so the column is written as NULL on every
    path that could write it.

    That matters for the activation review rather than for today's behaviour.
    The tenancy question for national orchestration is undecided in code, and
    the two available answers disagree: `TenantMixin.lab_id` is an INTEGER
    pointing at `labs.id`, while the only signal the package itself carries is
    an optional `String(100)`. Choosing between them decides whether a national
    workflow is scoped to a lab, a facility, a governorate or an organization --
    a national data-model decision with no evidence behind it in this repository.

    So if a route starts supplying `tenant_id`, that decision has been taken.
    This fails at that moment, and the ledger and the NR-065 record must say
    which answer was chosen and why. It is not here to prevent the work; it is
    here to stop the answer being adopted by accident.
    """
    populating = []
    for module in _ORCHESTRATION_ROUTE_MODULES:
        path = BACKEND / module
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, FileNotFoundError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "tenant_id":
                populating.append(f"{module}:{getattr(node.value, 'lineno', '?')}")
    assert populating == [], (
        "an orchestration route now supplies tenant_id, which means the national "
        "tenancy question has been answered. Record which answer (lab, facility, "
        "governorate or organization) and why in NR-065 before relying on it: "
        f"{populating}"
    )


# ── NR-065 Unit 8 ────────────────────────────────────────────────────────────
#
# Tenancy was never the only precondition, and after the Unit 8 caller trace it
# is not the most urgent one. Both orchestration routers are registered
# (`factory.py:695` and `:698`) and **neither contains a single
# `require_permission`**: every endpoint is guarded by `get_current_user` alone.
# So on the day these tables are built, any authenticated principal -- including
# a laboratory technician whose account has no national role at all -- can
# create, execute, cancel, reassign and delete national workflows and tasks, and
# list every one that exists.
#
# A scope column does not help with that. Scoping decides *which* rows an
# authorized caller may see; it cannot decide authorization where none is
# performed. Building the tables with a correct `organization_id` and no
# permission check would produce a correctly-labelled open door.
#
# Two more shapes found in the same trace, both of which outlive any scope column:
#
# * `TaskEngineService.update_task` assigns straight from the request body --
#   `for key, value in updates.items(): if hasattr(task, key) ... setattr(...)`,
#   excluding only `id`, `created_at` and `version`. `created_by`, `assigned_to`,
#   `assigned_by`, `status` and `correlation_id` are all writable, so a caller
#   can rewrite the audit-relevant actor fields and jump the state machine.
# * `POST /{task_id}/assign` passes `data.get("assigned_by")` and
#   `POST /{task_id}/escalate` passes `data.get("escalated_to")` from the body.
#   The server holds `current_user` and uses it for `created_by` on the same
#   handler set; the actor of an assignment is taken from the client instead.
#
# All three were latent for exactly one reason: the tables are unbuilt. That was
# the precondition this section held.
#
# NR-070 IS NOW FIXED, so these three are no longer preconditions gated on
# "while the tables are unbuilt" -- they are unconditional. A precondition that
# stays conditional after the condition is met stops holding anything: it would
# pass again the moment someone reverted the fix and left the tables unbuilt,
# which is the state the finding came from. The assertions below therefore ask
# for the absence of the defect, full stop.
#
# One entry below is a CORRECTION of my own earlier classification rather than a
# fix: `escalated_to` was listed as a client-supplied actor, and it is not one.
# It is the escalation *target*, which the caller legitimately chooses. The
# actor on that path is `escalated_by` -- a field the entity and the column have
# carried all along and which nothing ever wrote. Changing the code to satisfy
# the wrong half of a ledger would have been the worse repair.

_ROUTE_MODULES = (
    "app/national/task_engine/api/routes.py",
    "app/national/workflow_runtime/api/routes.py",
)

#: The service method whose body is assigned from the request body wholesale.
_MASS_ASSIGNMENT = (
    "app/national/task_engine/application/service.py",
    "update_task",
)

#: Handlers that must never take an actor identifier from the request body while
#: holding an authenticated `current_user` on the same call. `escalated_to` was
#: here and has been removed on evidence: it names the escalation target, not
#: the actor, and the caller choosing it is the feature.
_CLIENT_SUPPLIED_ACTORS = (
    ("app/national/task_engine/api/routes.py", "assigned_by"),
)


def _orchestration_tables_built() -> list[str]:
    return sorted(t for t in DECLARED_UNTENANTED_ORCHESTRATION_TABLES if t in _built())


def test_every_orchestration_router_declares_a_permission_check() -> None:
    """NR-065 Unit 8 / NR-070, now held rather than predicted.

    Scope is meaningless where authorization is absent, so this used to say
    "not while the tables are unbuilt". Both routers now carry
    `require_permission("system:admin")` at the router -- the same string, in the
    same place, as the thirteen national routers that already guarded
    themselves -- so the assertion is unconditional.

    The structural half of this claim (that the dependency is actually attached
    to every route of the running application, not merely named in the file) is
    proved against `create_app()` in `test_national_orchestration_authorization.py`.
    This one holds the source-level convention the sibling comparison rests on.
    """
    unguarded = []
    for module in _ROUTE_MODULES:
        source = (BACKEND / module).read_text(encoding="utf-8")
        if "require_permission" not in source:
            unguarded.append(module)

    # The sibling packages establish the convention: this is an omission in two
    # packages, not a gap in the platform's habits.
    siblings = sorted(
        str(path.relative_to(BACKEND))
        for path in (APP / "national").rglob("routes.py")
        if "__pycache__" not in path.parts
        and str(path.relative_to(BACKEND)) not in _ROUTE_MODULES
        and "require_permission" in path.read_text(encoding="utf-8")
    )

    assert unguarded == [], (
        f"these orchestration routers perform no permission check at all "
        f"({unguarded}). Every endpoint would depend only on `get_current_user`, "
        "so any authenticated account -- national role or not -- could create, "
        "execute, cancel and reassign national workflows and tasks. "
        f"{len(siblings)} sibling national route modules declare "
        f"`require_permission` ({siblings}); this is not a platform habit to "
        "follow, it is an omission that was fixed and must stay fixed"
    )


#: NR-070 / NR-072. Registered national route modules that declare no
#: `require_permission` anywhere. The ledger may shrink; it may never grow.
#:
#: IT IS NOW EMPTY. All three entries were closed by reusing the permission the
#: other thirteen already carry rather than by inventing one, so this has
#: hardened from "these three are known exceptions" into "every national route
#: module declares a permission check". The commentary below is kept because it
#: records what the exceptions were and why the third was a separate finding.
#:
#: The third entry was found by this guard rather than by the caller trace, and
#: it is a different finding from the orchestration two. `app/national/intelligence`
#: performs **no database access at all** -- no `SessionLocal`, no `get_db`, no
#: `.query(` anywhere in the package -- so its `/clinical/care-gaps/{patient_id}`
#: and `/clinical/risk-score/{patient_id}` endpoints read no patient data. The
#: path parameter is echoed rather than resolved, and `calculate_risk_score`
#: builds its entire "patient" from `age` and `gender` query parameters. It is an
#: authorization gap on stateless compute, not a disclosure (NR-072).
DECLARED_UNGUARDED_NATIONAL_ROUTERS: frozenset[str] = frozenset()


def _unguarded_national_routers() -> list[str]:
    return sorted(
        str(path.relative_to(BACKEND))
        for path in (APP / "national").rglob("routes.py")
        if "__pycache__" not in path.parts
        and "require_permission" not in path.read_text(encoding="utf-8")
    )


def test_no_new_national_router_drops_its_permission_check() -> None:
    """Hold the convention the fix will be measured against.

    NR-070 is stated as "these packages forgot", and that is only worth anything
    while the rest have not. Every other national route module declares
    `require_permission`; if one stops, the baseline this precondition appeals to
    is gone and the finding needs restating rather than inheriting.
    """
    appeared = [
        m for m in _unguarded_national_routers()
        if m not in DECLARED_UNGUARDED_NATIONAL_ROUTERS
    ]
    assert appeared == [], (
        "these national route modules declare no `require_permission` and are "
        "not in the ledger. Every endpoint in them depends on `get_current_user` "
        f"alone, so any authenticated account reaches the whole surface: {appeared}"
    )


def test_the_unguarded_router_ledger_does_not_rot() -> None:
    """A module that gained its permission check must leave the ledger."""
    unguarded = set(_unguarded_national_routers())
    resolved = sorted(DECLARED_UNGUARDED_NATIONAL_ROUTERS - unguarded)
    assert resolved == [], (
        "these modules now declare `require_permission`; remove them from the "
        f"ledger so the ratchet keeps its grip: {resolved}"
    )


#: Fields that must never become caller-writable through the update path,
#: whatever the mechanism. Adding one of these to `_TASK_UPDATABLE_FIELDS` is
#: the easy way to make the allowlist "pass" while restoring the defect, so the
#: allowlist itself is checked rather than only its presence.
_NEVER_CALLER_WRITABLE = frozenset({
    "id", "created_at", "created_by", "version", "status",
    "assigned_to", "assigned_by", "started_at", "completed_at",
    "escalation_level", "correlation_id",
})


def test_the_task_update_path_consults_an_allowlist() -> None:
    """`update_task` used to write whatever the body named, actor fields included.

    This asserted the absence of `setattr` at first, which was wrong: the fix
    still sets attributes, it just decides which ones first. Asserting the
    absence of the mechanism rather than the absence of the *decision* would
    have failed on the correct code and passed on a filtered loop that let
    `created_by` through. So the assertion is that the allowlist is consulted --
    and, below, that the allowlist is not quietly widened.
    """
    module, method = _MASS_ASSIGNMENT
    tree = ast.parse((BACKEND / module).read_text(encoding="utf-8"))

    consulted = False
    for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
        if fn.name != method:
            continue
        names = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
        consulted = {"_reject_unknown", "_TASK_UPDATABLE_FIELDS"} <= names

    assert consulted, (
        f"{module}::{method} no longer checks the request body against "
        "`_TASK_UPDATABLE_FIELDS`. The loop this replaced excluded only id, "
        "created_at and version, so `created_by`, `assigned_by`, `assigned_to` "
        "and `status` were all client-writable -- the actor fields an audit "
        "trail relies on, and a way past the state machine the transition "
        "methods enforce"
    )


def test_the_allowlist_never_grows_to_include_an_actor_or_state_field() -> None:
    """The allowlist is the fix; widening it is the same defect with a list."""
    from app.national.task_engine.application.service import _TASK_UPDATABLE_FIELDS

    leaked = sorted(_NEVER_CALLER_WRITABLE & _TASK_UPDATABLE_FIELDS)
    assert leaked == [], (
        "these fields are caller-writable through PUT /national/tasks/{id} "
        f"again: {leaked}. Status belongs to the transition methods, the "
        "assignment fields to assign_task and delegate_task, and created_by to "
        "whoever created the row"
    )


def test_no_actor_identifier_is_taken_from_the_request_body() -> None:
    """The server knows who is calling; these handlers used to ask the caller."""
    offending = []
    for module, field in _CLIENT_SUPPLIED_ACTORS:
        source = (BACKEND / module).read_text(encoding="utf-8")
        if f'data.get("{field}")' in source or f'data["{field}"]' in source:
            offending.append(f"{module}:{field}")

    assert offending == [], (
        f"these handlers take an actor identifier from the request body: "
        f"{offending}. `current_user` is already resolved on the same handler "
        "and is used for `created_by`; an assignment attributed to whoever the "
        "caller names is not an audit record"
    )
