"""NR-081 — schema access that no other instrument in this suite can see.

Every schema guard here works from ORM metadata: `built_tables()` derives from
migrations, `test_alembic_metadata_registry.py` compares registered `MetaData`
against PostgreSQL, `test_autogenerate_is_safe.py` diffs mappers against the
database, and the NR-063/NR-067 scans resolve ORM class names to tables.

All of them are blind to two constructs:

* ``sqlalchemy.table("patients", column("national_id"), ...)`` -- the lightweight
  Core construct, which has **no MetaData at all**. It names a real table, it
  can be selected from and inserted into, and no metadata-based instrument will
  ever see it.
* raw SQL handed to ``text()`` or ``.execute()``. The table name is a substring
  inside a string literal.

Found while tracing why `patients.national_id` is physical, indexed four ways,
and mapped by no model (NR-080). `app/reference/infrastructure/repositories.py`
reads and writes it -- through a `table()` construct, with raw
``INSERT INTO patients``, returning `national_id` in its response shape.

`app/reference` is, measured against the running application:

    routes it serves ........................ 0
    modules outside it that import it ....... 0

So it is unreachable, and this is recorded rather than repaired: it is a
complete parallel implementation of patient reference data with its own domain
model, its own repository and its own tests, and deleting a subsystem is an
ownership decision. What matters here is that **it writes three canonical
clinical tables** -- `patients`, `lab_orders`, `lab_results` -- by a route none
of the schema tooling can follow. If it were ever registered, there would be a
second write authority for the clinical subject with different invariants, and
no existing guard would notice.

**A measurement correction, recorded because the wrong number nearly shipped.**
A first pass matched ``INSERT INTO|UPDATE|DELETE FROM`` against every string
literal in `app/` and reported **8** modules. One was
`app/core/bootstrap/permissions.py`, which contains no SQL whatsoever: the regex
matched the human-readable permission label ``"Update Patients"``. Counting only
strings actually handed to ``text()`` or ``.execute()`` gives **7**. The 8 is not
recorded anywhere as a finding, because it is not true.

Six of the seven are legitimate and stay: the three AI modules write their own
tables, `idempotency_keys` has no ORM by design, `outbox_events` needs raw SQL
for its locking, and `startup_guard` seeds `lab_users` before the app is up.
Legitimacy is not the invariant here -- **visibility** is. The ledgers exist so
that a new one has to be declared rather than discovered.

The ledgers may shrink. They may never grow.
"""

from __future__ import annotations

import ast
import collections
import re

from tests.orm_resolution import APP, BACKEND, built_tables, parse

#: Modules declaring a Core `table()` naming a table the migrations build.
DECLARED_CORE_TABLE_ACCESS = {
    "app/reference/infrastructure/repositories.py": {"patients"},
}

#: Modules executing raw INSERT/UPDATE/DELETE against a table the migrations
#: build. Six are their own domain's storage; the seventh is the shadow.
DECLARED_RAW_DML_ACCESS = {
    "app/ai/governance.py": {"ai_evaluations", "ai_model_registry"},
    "app/ai/memory.py": {"ai_conversation_messages", "ai_conversations"},
    "app/ai/vector_store.py": {"ai_embeddings"},
    "app/core/idempotency.py": {"idempotency_keys"},
    "app/core/startup_guard.py": {"lab_users"},
    "app/reference/infrastructure/repositories.py": {
        "lab_orders", "lab_results", "patients",
    },
    "app/services/outbox_service.py": {"outbox_events"},
}

#: Tables whose write authority is a clinical-safety question rather than a
#: storage detail. A new raw writer of one of these is a finding on sight.
CANONICAL_CLINICAL_TABLES = frozenset({
    "patients", "lab_orders", "lab_results", "samples", "audit_logs",
})

#: The one module allowed to reach a canonical clinical table this way, and only
#: because nothing can call it. If `app/reference` is ever registered, the
#: entry must be justified as a second write authority or removed.
DECLARED_UNREACHABLE_CLINICAL_WRITERS = frozenset({
    "app/reference/infrastructure/repositories.py",
})

_DML = re.compile(
    r"\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+\"?([a-z_][a-z0-9_]*)\"?\b", re.I,
)

#: Callables whose string argument is actually executed. Matching raw literals
#: anywhere instead reported a module with no SQL in it at all.
_EXECUTORS = frozenset({"text", "execute", "executemany", "exec_driver_sql"})


def _executed_sql(tree: ast.Module):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = (
            node.func.id if isinstance(node.func, ast.Name)
            else node.func.attr if isinstance(node.func, ast.Attribute)
            else ""
        )
        if name not in _EXECUTORS:
            continue
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                yield arg.value
            elif isinstance(arg, ast.JoinedStr):
                yield "".join(
                    part.value for part in arg.values
                    if isinstance(part, ast.Constant) and isinstance(part.value, str)
                )


def _scan() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    built = built_tables()
    core: dict[str, set[str]] = collections.defaultdict(set)
    raw: dict[str, set[str]] = collections.defaultdict(set)
    for path in APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        tree = parse(path)
        if tree is None:
            continue
        module = str(path.relative_to(BACKEND))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and (
                    (isinstance(node.func, ast.Name) and node.func.id == "table")
                    or (isinstance(node.func, ast.Attribute) and node.func.attr == "table")
                )
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and node.args[0].value in built
            ):
                core[module].add(node.args[0].value)
        for statement in _executed_sql(tree):
            for match in _DML.finditer(statement):
                name = match.group(1).lower()
                if name in built:
                    raw[module].add(name)
    return dict(core), dict(raw)


def test_the_scan_still_finds_executed_sql() -> None:
    """Guard the guard against the population, not against the finding.

    A floor on "how many raw writers did you find" is met by a scan that finds
    nothing. This asserts the scan still sees the body of executed SQL it is
    reading the ledgers out of.

    The floor is 70 against a measured 77, not a round number picked in advance:
    NR-079's floor asked for 60 registered route modules while the instrument
    was missing 63, and passed comfortably for years. A guard-the-guard is only
    worth its distance from the truth, so this one is set just under it.
    """
    total = 0
    for path in APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        tree = parse(path)
        if tree is None:
            continue
        total += sum(1 for _ in _executed_sql(tree))
    assert total >= 70, (
        f"only {total} executed SQL strings found across app/; the scan has "
        "drifted and both ledgers below would be understated"
    )


def test_no_new_module_reaches_a_built_table_through_a_core_table_construct() -> None:
    """`sqlalchemy.table()` has no MetaData, so nothing else here can see it."""
    core, _ = _scan()
    appeared = sorted(set(core) - set(DECLARED_CORE_TABLE_ACCESS))
    assert appeared == [], (
        "these modules name a migration-built table through a Core `table()` "
        "construct, which carries no MetaData and is therefore invisible to "
        f"every schema guard in this suite: {appeared}"
    )
    widened = {
        module: sorted(tables - DECLARED_CORE_TABLE_ACCESS[module])
        for module, tables in core.items()
        if module in DECLARED_CORE_TABLE_ACCESS
        and tables - DECLARED_CORE_TABLE_ACCESS[module]
    }
    assert widened == {}, f"new tables reached through `table()`: {widened}"


def test_no_new_module_executes_raw_dml_against_a_built_table() -> None:
    """Raw SQL is legitimate; raw SQL nobody declared is a blind spot."""
    _, raw = _scan()
    appeared = sorted(set(raw) - set(DECLARED_RAW_DML_ACCESS))
    assert appeared == [], (
        "these modules execute raw INSERT/UPDATE/DELETE against a "
        "migration-built table without being declared. Raw SQL is allowed; "
        f"being invisible to the schema guards is not: {appeared}"
    )
    widened = {
        module: sorted(tables - DECLARED_RAW_DML_ACCESS[module])
        for module, tables in raw.items()
        if module in DECLARED_RAW_DML_ACCESS
        and tables - DECLARED_RAW_DML_ACCESS[module]
    }
    assert widened == {}, (
        f"declared raw writers reached new tables (module -> new tables): {widened}"
    )


def test_only_unreachable_modules_write_a_canonical_clinical_table_this_way() -> None:
    """The clinical half, which is the reason this file exists.

    `patients`, `lab_orders`, `lab_results`, `samples` and `audit_logs` have one
    write authority each by design. A module writing one of them through raw SQL
    is a second authority with its own invariants, and no ORM-based guard can
    see it. Today exactly one module does, and it is served by no route and
    imported by no module -- which is the only reason it is tolerable.
    """
    _, raw = _scan()
    clinical_writers = {
        module for module, tables in raw.items()
        if tables & CANONICAL_CLINICAL_TABLES
    }
    undeclared = sorted(clinical_writers - DECLARED_UNREACHABLE_CLINICAL_WRITERS)
    assert undeclared == [], (
        "these modules write a canonical clinical table through raw SQL: "
        f"{undeclared}. Each is a second write authority for a table whose "
        "invariants live in the ORM and the services around it"
    )


def test_the_schema_access_ledgers_do_not_rot() -> None:
    """An entry that stopped accessing the table must leave the ledger."""
    core, raw = _scan()
    stale_core = sorted(set(DECLARED_CORE_TABLE_ACCESS) - set(core))
    stale_raw = sorted(set(DECLARED_RAW_DML_ACCESS) - set(raw))
    assert stale_core == [] and stale_raw == [], (
        "these modules no longer reach a built table the invisible way; remove "
        f"them so the ratchet keeps its grip: core={stale_core} raw={stale_raw}"
    )
