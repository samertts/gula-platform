"""NR-088 — raw SQL over `patients` that no tenant filter constrains.

Security Invariant #1 says every patient-data query filters by
`lab_id = current_user.lab_id`. Every guard that checks it works from ORM
metadata, and NR-081 established that none of them can see a table name inside
a string literal. So this asks the question directly, of the SQL itself.

Of the 335 `.execute(...)` call sites in `app/`, eight read `patients`. Two
constrain `lab_id` and are correct. **Six do not**, across two packages — one
of which the application serves:

* `app/national/search_platform/` — four sites; `lab_id` does not appear
  anywhere in the module. Three pass a **bare Python string**, which in
  SQLAlchemy 2.0 is not executable at all::

      ObjectNotExecutableError: Not an executable object: "SELECT id FROM patients ..."

  The fourth, `get_facets`, is properly wrapped in `text()` and therefore
  **is** executable. It fails only on a column name::

      SELECT COUNT(*) FROM patients
       WHERE to_tsvector('simple', name || ' ' || COALESCE(phone,'')
                                        || ' ' || COALESCE(national_id,'')) @@ ...
      ProgrammingError: column "name" does not exist

  Substituting the column the table actually has makes it run::

      full_name -> EXECUTES, COUNT = 0

  That is a cross-lab count, and its predicate matches on `national_id`. One
  column rename separates `GET /facets` from a working untenanted search over
  national identifiers, on a table whose `national_id` the canonical mapper
  deliberately does not expose (NR-087).

* `app/insurance/services/coverage_engine.py` — two sites, both bare strings.
  This package serves **no** routes and nothing outside it imports it, so it is
  NR-087's class rather than this one; `factory.py` registers
  `app/routes/insurance.py`, a different module that merely shares the name.
  `SELECT date_of_birth FROM patients WHERE id = :pid` names a column that does
  not exist (the table has `birth_date`), but
  `SELECT gender FROM patients WHERE id = :pid` **is valid SQL**. It is inert
  for one reason only: the bare string. The fix for `ObjectNotExecutableError`
  is to wrap it in `text()` — a one-token change, made on sight — and that
  change alone turns it into a cross-lab read keyed on a caller-supplied id.

Reachability was measured by walking the *started* application recursively.
FastAPI stores an included router as an opaque `_IncludedRouter`, so a single
pass over `app.routes` sees 123 entries against a served surface of **2102** --
`tests/orm_resolution.py::every_route` exists for exactly that reason, and a
first pass here that skipped it reported zero routes for every package.

**So the ledger is not "these are broken".** It is *these are unsafe, and the
thing keeping them inert is not tenant isolation*. Both barriers — a bare
string and a wrong column name — are the kind a developer removes while fixing
something else, without ever being told a tenant filter was the missing part.

The invariant below is therefore about *executability*, not about the count:
SQL that reads `patients` and can actually reach PostgreSQL must constrain
`lab_id`. The ledgers may shrink and may never grow, and an entry that gains a
tenant filter must be removed rather than left behind.
"""

from __future__ import annotations

import ast
import re

from tests.orm_resolution import APP, BACKEND, parse

#: `FROM patients`, `INTO patients`, `UPDATE patients`, `JOIN patients`.
PATIENT_SQL = re.compile(r"\b(?:from|into|update|join)\s+patients\b", re.I)

#: Modules with raw SQL reading `patients` under no tenant filter, and how many
#: such sites each has. Measured; may shrink, may never grow.
DECLARED_UNTENANTED: dict[str, int] = {
    "app/insurance/services/coverage_engine.py": 2,
    "app/national/search_platform/application/interfaces.py": 4,
}

#: The subset of the above that SQLAlchemy can actually execute, so only the
#: schema stands between them and a live cross-tenant read. This is the one
#: that matters: wrapping a ledgered bare string in `text()` without adding a
#: tenant filter moves a site into this set and fails the gate.
DECLARED_EXECUTABLE_UNTENANTED: dict[str, int] = {
    "app/national/search_platform/application/interfaces.py": 1,
}

#: Floors sit just under the true measured population (335 execute sites, 8 of
#: them over `patients`), so an instrument that stops seeing the application
#: fails instead of agreeing with every ledger — the NR-079 mode.
MINIMUM_EXECUTE_SITES = 318
MINIMUM_PATIENT_SQL_SITES = 7


def _string_bindings(tree: ast.AST) -> dict[str, str]:
    """`name -> value` for every `x = "..."` binding in the module.

    The search platform builds its statements as local variables rather than
    inline, so a scan that only reads literal arguments sees three of its four
    sites and calls the module half-safe.
    """
    bindings: dict[str, str] = {}
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    bindings[target.id] = node.value.value
    return bindings


def _sql_of(arg: ast.expr, bindings: dict[str, str]) -> tuple[str | None, bool]:
    """The SQL an `execute()` argument carries, and whether it can execute.

    A bare `str` is *not* executable in SQLAlchemy 2.0 — it raises
    `ObjectNotExecutableError` before any SQL is sent — so the distinction is
    the whole point of this file rather than a detail.
    """
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value, False
    if isinstance(arg, ast.Name) and arg.id in bindings:
        return bindings[arg.id], False
    if isinstance(arg, ast.Call) and getattr(arg.func, "id", None) == "text" and arg.args:
        inner = arg.args[0]
        if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
            return inner.value, True
        if isinstance(inner, ast.Name) and inner.id in bindings:
            return bindings[inner.id], True
    return None, False


def _scan() -> dict[str, object]:
    execute_sites = 0
    patient_sites: list[tuple[str, int, bool, bool]] = []
    for path in sorted(APP.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = parse(path)
        if tree is None:
            continue
        module = str(path.relative_to(BACKEND))
        bindings = _string_bindings(tree)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "execute"
                    and node.args):
                continue
            execute_sites += 1
            sql, executable = _sql_of(node.args[0], bindings)
            if sql and PATIENT_SQL.search(sql):
                patient_sites.append(
                    (module, node.lineno, executable, "lab_id" in sql.lower()),
                )
    return {"execute_sites": execute_sites, "patient_sites": patient_sites}


def _untenanted(executable_only: bool = False) -> dict[str, int]:
    counts: dict[str, int] = {}
    for module, _line, executable, tenanted in _scan()["patient_sites"]:  # type: ignore[union-attr]
        if tenanted or (executable_only and not executable):
            continue
        counts[module] = counts.get(module, 0) + 1
    return counts


def test_the_scan_still_sees_the_application() -> None:
    """Guard the guard, against the population rather than against the finding."""
    result = _scan()
    assert result["execute_sites"] >= MINIMUM_EXECUTE_SITES, (
        f"only {result['execute_sites']} execute() sites found; the scan has drifted "
        "and the ledgers below would be measured against nothing"
    )
    assert len(result["patient_sites"]) >= MINIMUM_PATIENT_SQL_SITES, (  # type: ignore[arg-type]
        f"only {len(result['patient_sites'])} raw-SQL reads of patients found; "  # type: ignore[arg-type]
        "the scan no longer recognises the statements it exists to classify"
    )


def test_no_new_raw_patient_sql_skips_tenant_isolation() -> None:
    """The ratchet. Security Invariant #1 over SQL no ORM guard can see."""
    found = _untenanted()
    grown = sorted(
        f"{module} ({count} > {DECLARED_UNTENANTED.get(module, 0)})"
        for module, count in found.items()
        if count > DECLARED_UNTENANTED.get(module, 0)
    )
    assert grown == [], (
        "raw SQL reads patients here with no lab_id constraint, so it is not "
        "limited to the caller's lab. Add the tenant filter rather than the "
        f"module to the ledger: {grown}"
    )


def test_no_new_executable_untenanted_patient_sql() -> None:
    """The one that matters, and the one a partial fix trips.

    A bare string cannot execute in SQLAlchemy 2.0. Wrapping it in `text()` is
    the obvious repair for `ObjectNotExecutableError` and says nothing about
    tenancy -- so that repair, alone, is what turns one of these into a live
    cross-lab read. It moves a site into this set, and this fails.
    """
    found = _untenanted(executable_only=True)
    grown = sorted(
        f"{module} ({count} > {DECLARED_EXECUTABLE_UNTENANTED.get(module, 0)})"
        for module, count in found.items()
        if count > DECLARED_EXECUTABLE_UNTENANTED.get(module, 0)
    )
    assert grown == [], (
        "this SQL reads patients, carries no lab_id constraint, and can now "
        "reach PostgreSQL. Only the schema is stopping it. Add the tenant "
        f"filter in the same change that made it executable: {grown}"
    )


def test_the_untenanted_ledger_does_not_rot() -> None:
    """A module that gained its tenant filter must leave the ledger."""
    found = _untenanted()
    resolved = sorted(module for module in DECLARED_UNTENANTED if module not in found)
    assert resolved == [], (
        "these modules no longer read patients without a lab_id constraint; "
        "remove them from the ledger so the ratchet keeps its grip: "
        f"{resolved}"
    )
