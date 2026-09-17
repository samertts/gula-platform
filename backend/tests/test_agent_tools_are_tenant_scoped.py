"""Every agent tool that reads clinical data must constrain it to one lab.

`POST /api/ai/v2/agents/execute` is registered in `app/factory.py` and served.
A caller submits a free-text task; `AgentRuntime._plan_tools` sends that task to
an external model (`app.gateways.google_ai.generate_chat`), parses the JSON it
returns, and `execute_plan` dispatches whatever tool and parameters it names.
So the *arguments* to a clinical read -- including `patient_id` -- originate in
a model's reading of user text.

The runtime is right about this. `execute_tool` calls

    tool.fn(**kwargs, lab_id=context.lab_id, user_id=context.user_id)

so the authenticated tenant is injected into every tool and the model cannot
supply its own (passing `lab_id` in `params` raises TypeError for a repeated
keyword, and the call fails). The tenant boundary is the runtime's, not the
model's, which is the right place for it.

Two of the three clinical tools took that `lab_id` into `**kwargs` and never
used it. `_get_recent_results` and `_analyze_lab_pattern` selected from
`lab_results JOIN lab_orders` on `lo.patient_id` alone, while `_lookup_patient`
in the same file filtered `(lab_id = :lab OR :lab IS NULL)` -- scoped, but
fail-open if the tenant were ever absent.

None of this was reachable, and the reason is worth recording because it is not
a control. All three tools name columns the database does not have. Executed
against PostgreSQL 16 at head with two labs:

    lookup_patient       RAISES  column "name" does not exist
    get_recent_results   RAISES  column lr.result_date does not exist
    analyze_lab_pattern  RAISES  column lr.result_date does not exist

`patients` has `full_name`, not `name`; `lab_results` has `created_at`, not
`result_date`. Each tool catches the exception and returns `{"error": ...}`, so
callers get an error string and no data. The clinical agent-tool surface is
non-functional, and that -- not the authorization model -- is what was keeping
it safe.

Which makes the obvious repair a trap. Correcting only the column names, with
the same WHERE clause, was executed too: a lab-901 session asking for patient
7002 (lab 902) got back `['SECRET-LAB-B']`. Adding `lo.lab_id` returns `[]` for
that request and still returns `['SECRET-LAB-A']` for the session's own patient.

So the tenant constraint was added now, while it changes nothing observable, and
the column names were deliberately left alone: making a clinical AI tool
functional is a product decision, not a repair. These tests hold the half that
is safe to hold -- the boundary is in place whenever someone completes the rest.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest

RUNTIME = pathlib.Path(__file__).resolve().parents[1] / "app" / "ai" / "agent_runtime.py"

#: Tables whose rows belong to exactly one lab. `lab_results` is here even
#: though it has no `lab_id` column of its own: it is tenanted transitively
#: through `lab_orders`, so a query reading it must constrain the order.
TENANT_TABLES = ("patients", "lab_orders", "lab_results", "samples", "lab_users")

#: Columns these tools name that the database does not have, measured against
#: PostgreSQL 16 at head 20260915_0003. Listed so that repairing them is a
#: deliberate act with this file's docstring in view, not a tidy-up.
DECLARED_SCHEMA_MISMATCHES = {
    "patients.name": "patients has full_name",
    "lab_results.result_date": "lab_results has created_at",
}


def _registered_tools(tree: ast.Module):
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and getattr(dec.func, "id", "") == "register_tool":
                name = dec.args[0].value if dec.args else node.name
                yield name, node


def _sql_of(node) -> list[str]:
    return [
        call.args[0].value
        for call in ast.walk(node)
        if isinstance(call, ast.Call)
        and getattr(call.func, "id", "") == "text"
        and call.args
        and isinstance(call.args[0], ast.Constant)
        and isinstance(call.args[0].value, str)
    ]


@pytest.fixture(scope="module")
def source() -> str:
    return RUNTIME.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def tree(source) -> ast.Module:
    return ast.parse(source)


def test_every_clinical_agent_tool_constrains_its_read_to_one_lab(tree) -> None:
    """The invariant, on the surface a model can steer.

    `execute_tool` hands every tool `context.lab_id`. A tool that reads a
    tenant-owned table and does not put it in the WHERE clause is accepting a
    `patient_id` chosen by an external model's reading of user text, with
    nothing to say which lab that patient belongs to.
    """
    unscoped = []
    for name, node in _registered_tools(tree):
        statements = _sql_of(node)
        touching = [
            s for s in statements
            if any(re.search(rf"\b{t}\b", s) for t in TENANT_TABLES)
        ]
        for statement in touching:
            if not re.search(r"\blab_id\s*=\s*:", statement):
                unscoped.append((name, " ".join(statement.split())[:90]))

    assert unscoped == [], (
        f"an agent tool reads clinical data without a lab_id constraint: {unscoped}. "
        "The runtime already supplies context.lab_id to every tool; put it in the "
        "WHERE clause. lab_results has no lab_id of its own -- constrain "
        "lab_orders.lab_id on the join instead."
    )


def test_no_clinical_agent_tool_treats_an_absent_tenant_as_a_wildcard(tree) -> None:
    """Fail-closed, not fail-open.

    `(lab_id = :lab OR :lab IS NULL)` reads as "if we do not know the tenant,
    return every tenant". An absent lab_id means something upstream is wrong,
    and the safe answer to that is no clinical rows at all.
    """
    wildcards = []
    for name, node in _registered_tools(tree):
        for statement in _sql_of(node):
            if not any(re.search(rf"\b{t}\b", statement) for t in TENANT_TABLES):
                continue
            if re.search(r"OR\s+:?\w*lab\w*\s+IS\s+NULL", statement, re.I):
                wildcards.append((name, " ".join(statement.split())[:90]))

    assert wildcards == [], (
        f"an agent tool treats a missing tenant as 'any tenant': {wildcards}. "
        "Bind lab_id unconditionally so an absent tenant matches no rows."
    )


def test_the_runtime_still_supplies_the_tenant_rather_than_the_model(source) -> None:
    """Guards the mechanism the two tests above depend on.

    If `execute_tool` stopped injecting `context.lab_id`, every tool would fall
    back to whatever the external model put in `params` -- which is the model
    deciding a tenant boundary, and is what §27 of the operating brief forbids.
    """
    assert "lab_id=context.lab_id" in source, (
        "execute_tool no longer injects the authenticated lab_id into tool "
        "calls. The tenant would then come from the planning model's JSON."
    )


def test_the_schema_mismatches_are_still_present_or_the_ledger_is_updated(source) -> None:
    """The rot check, and the reason this file's docstring must be read.

    These tools do not work. If someone corrects the column names, the tests
    above have already put the tenant constraint in place -- but the ledger here
    would be describing a file that has changed, and whether a clinical AI tool
    should now be functional is a decision somebody has to make on purpose.
    """
    still_wrong = [
        column for column in DECLARED_SCHEMA_MISMATCHES
        if re.search(rf"\b{re.escape(column.split('.')[1])}\b", source)
    ]
    resolved = sorted(set(DECLARED_SCHEMA_MISMATCHES) - set(still_wrong))
    assert resolved == [], (
        f"these declared schema mismatches are gone: {resolved}. The tools may "
        "now return clinical data where they previously returned an error "
        "string. The tenant constraint is already enforced by the tests above, "
        "so this is safe -- but update DECLARED_SCHEMA_MISMATCHES and confirm "
        "that making this AI surface functional was intended."
    )

# ── the gate (NR-096, §32-C) ─────────────────────────────────────────────────


def test_every_clinical_tool_checks_the_gate_before_touching_the_database(tree) -> None:
    """§32-C's answer, held in place.

    The assessment said do not activate: tenant isolation and authorization are
    ready, but there is no audit of any tool invocation, the planning model
    receives the caller's free text and conversation history, there is no
    deterministic layer before the model, and ai_evaluations is written without
    a lab_id. None of that is fixed by correcting the column names -- which is
    all that stood between this surface and being live.

    So the gate must be the FIRST thing each tool does. A check placed after
    `next(get_db())` would still open a session, and one placed inside the
    `try` would still run the query.
    """
    ungated = []
    for name, node in _registered_tools(tree):
        if not any(
            re.search(rf"\b{t}\b", statement)
            for statement in _sql_of(node)
            for t in TENANT_TABLES
        ):
            continue  # not a clinical tool
        body = node.body
        first = body[1] if body and isinstance(body[0], ast.Expr) else (body[0] if body else None)
        guarded = (
            isinstance(first, ast.If)
            and "_clinical_tools_enabled" in ast.dump(first.test)
        )
        if not guarded:
            ungated.append(name)

    assert ungated == [], (
        f"these clinical agent tools do not check the gate first: {ungated}. "
        "The check must precede next(get_db()); otherwise a disabled surface "
        "still opens a session and runs its query."
    )


def test_the_gate_defaults_to_off() -> None:
    """A clinical AI surface is off unless a deployment says otherwise."""
    from app import config

    assert config.ENABLE_AI_CLINICAL_AGENT_TOOLS is False, (
        "ENABLE_AI_CLINICAL_AGENT_TOOLS no longer defaults to False. §32-C's "
        "assessment has not been satisfied: there is still no audit of tool "
        "invocations and the planning model still receives free text."
    )


def test_no_tool_returns_a_raw_exception_to_the_caller(source) -> None:
    """The failure path disclosed the schema.

    `return {"error": str(exc)}` is how "column lr.result_date does not exist"
    became an API response -- which is also how the mismatch was found, but a
    caller should not be the one finding it.
    """
    leaks = re.findall(r'"error":\s*str\(exc\)', source)
    assert leaks == [], (
        f"{len(leaks)} tool(s) return str(exc) to the caller. Log the detail "
        "and return a message that names no column, table or query."
    )
