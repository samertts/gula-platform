"""NR-063 — a table may not be built while its create path is an unvalidated passthrough.

Found while resolving NR-022's nine REVIEW sites. They could not be decided from
their call sites, and the reason turned out to matter more than the question:
the call sites are generic passthroughs. `create_risk_stratification(db, data)`
is a route taking a bare `data: dict` -- no request model -- handed to
`RiskStratification(**data)`. The code cannot express who `assessed_by` means
because nothing in the code ever sets it.

Measured across `app/`: **103** sites construct an ORM model by splatting a
function parameter (`Model(**param)`).

    28  set tenant and/or actor server-side
    75  set neither -- the request body controls every column

The 28 are the defensible pattern, e.g.::

    ClinicalTask(lab_id=lab_id, created_by=user_id, assigned_by=user_id, **data)

`lab_id` and the actor come from the authenticated user, and a body key that
collides with them raises TypeError rather than overriding them. Those paths
also audit. The residual risk is arbitrary *non-tenant* columns.

The 75 are `Model(**data)` with nothing server-set, concentrated in
care_continuum (40), clinical (18) and ehr (17). On those, the request body
would decide `lab_id`, `verified_by`, `is_deleted` -- everything.

Server-setting is detected in both forms it takes here: an explicit keyword
on the call, and a pre-splat `data["key"] = value` mutation. Counting only
the first reported `create_compliance_check` as unguarded when it does set
the actor by mutation -- a false positive worth not shipping in a guard that
is supposed to block schema work.

**Today that is latent, and this file's job is to keep it that way.** Every one
of the 75 targets a table no migration builds, so the write fails with
UndefinedTable before a row exists. The danger is not the current state; it is
that NR-022 and NR-059 are both about building unbuilt tables. Building one of
them without first giving it a validated create path would convert 75 latent
mass-assignment paths into live ones, including tenant assignment on
TenantAuditEntity models.

So the invariant is a precondition, not a prohibition: fix the create path, then
build the table. Either order is fine. Only the omission fails.
"""

from __future__ import annotations

import ast
import collections
import json
import pathlib

BACKEND = pathlib.Path(__file__).resolve().parents[1]
APP = BACKEND / "app"
EVIDENCE = BACKEND.parent / "docs" / "architecture" / "evidence-created-tables.json"

#: Names that, when passed explicitly alongside the splat, mean the server -- not
#: the caller -- decided tenancy and actor.
_SERVER_SET = frozenset({
    "lab_id", "tenant_id", "created_by", "user_id", "actor_id", "organization_id",
    "checked_by",
})

#: Modules whose create paths splat an unvalidated parameter with nothing
#: server-set, and the number of such sites. This ledger may shrink. It may
#: never grow.
DECLARED_UNGUARDED_PASSTHROUGH = {
    "app/services/care_continuum_service.py": 40,
    "app/services/clinical_service.py": 18,
    "app/services/ehr_service.py": 17,
}


def _model_tables() -> dict[str, str]:
    """ORM class name -> table name, by AST."""
    mapping: dict[str, str] = {}
    for path in APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
            for stmt in cls.body:
                if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Constant):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == "__tablename__":
                            mapping[cls.name] = stmt.value.value
    return mapping


def _passthrough_writes() -> list[tuple[str, str, str, bool]]:
    """(module, function, model, server_set_tenant_and_actor) for each splat."""
    models = _model_tables()
    found: list[tuple[str, str, str, bool]] = []
    for path in APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        module = str(path.relative_to(BACKEND))
        for fn in (
            n for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ):
            params = {a.arg for a in fn.args.args}
            # Server-setting takes two forms here: an explicit keyword on the
            # call, and a `data["key"] = value` mutation before the splat. Miss
            # the second and the guard cries wolf on paths that are already safe.
            mutated: set[str] = set()
            for node in ast.walk(fn):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if (
                            isinstance(target, ast.Subscript)
                            and isinstance(target.value, ast.Name)
                            and target.value.id in params
                            and isinstance(target.slice, ast.Constant)
                        ):
                            mutated.add(target.slice.value)
            for node in ast.walk(fn):
                if not isinstance(node, ast.Call) or not node.keywords:
                    continue
                splatted = any(
                    kw.arg is None
                    and isinstance(kw.value, ast.Name)
                    and kw.value.id in params
                    for kw in node.keywords
                )
                model = getattr(node.func, "id", None)
                if splatted and model in models:
                    named = {kw.arg for kw in node.keywords if kw.arg}
                    found.append(
                        (module, fn.name, model, bool((named | mutated) & _SERVER_SET))
                    )
    return found


def test_the_scan_still_finds_the_passthrough_surface() -> None:
    """Guard the guard: finding nothing would make the precondition vacuous."""
    writes = _passthrough_writes()
    assert len(writes) >= 90, (
        f"only {len(writes)} passthrough constructions found; the scan has drifted"
    )


def test_no_unguarded_passthrough_reaches_a_built_table() -> None:
    """The precondition, and the reason this file exists.

    An unguarded path is `Model(**data)` with no server-set tenant or actor, so
    the request body decides every column including `lab_id`. Today every such
    path targets a table no migration creates, which is the only reason the
    pattern is latent.

    If a table appears under one of these, the fix is not to delete this test.
    It is to give that create path a request model and server-set tenancy first.
    Either order works; only the omission fails.
    """
    built = set(json.loads(EVIDENCE.read_text(encoding="utf-8")))
    models = _model_tables()
    live = sorted({
        (models[model], module, fn)
        for module, fn, model, guarded in _passthrough_writes()
        if not guarded and models.get(model) in built
    })
    assert live == [], (
        "these tables are built AND written by an unvalidated passthrough with "
        "no server-set tenant or actor, so the request body decides lab_id. "
        f"Give the create path a request model before building the table: {live}"
    )


def test_the_unguarded_ledger_does_not_grow() -> None:
    """New unguarded create paths are new latent mass-assignment."""
    counts = collections.Counter(
        module for module, _, _, guarded in _passthrough_writes() if not guarded
    )
    appeared = sorted(set(counts) - set(DECLARED_UNGUARDED_PASSTHROUGH))
    assert appeared == [], (
        "new modules construct ORM models from an unvalidated parameter with "
        f"nothing server-set: {appeared}"
    )
    widened = {
        m: (declared, counts.get(m, 0))
        for m, declared in DECLARED_UNGUARDED_PASSTHROUGH.items()
        if counts.get(m, 0) > declared
    }
    assert widened == {}, (
        f"unguarded passthrough writes were added (declared -> now): {widened}"
    )


def test_the_guarded_pattern_still_sets_tenant_and_actor() -> None:
    """The 28 defensible sites are the template the other 75 should follow.

    If this reaches zero, the pattern that makes a passthrough survivable has
    been removed and the ledger above is describing a different codebase.
    """
    guarded = [w for w in _passthrough_writes() if w[3]]
    assert len(guarded) >= 20, (
        "the server-set tenant/actor passthrough pattern has largely "
        f"disappeared; only {len(guarded)} sites remain"
    )
