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
import json
import pathlib
import re

BACKEND = pathlib.Path(__file__).resolve().parents[1]
APP = BACKEND / "app"
EVIDENCE = BACKEND.parent / "docs" / "architecture" / "evidence-created-tables.json"

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
    return set(json.loads(EVIDENCE.read_text(encoding="utf-8")))


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
