"""NR-087 — `app/reference` is a second write authority over the three core tables.

`app/reference` is a complete parallel persistence stack — domain models,
services, repositories and three routers — that issues **raw SQL** against
`patients`, `lab_orders` and `lab_results` through `app.database.get_db`, which
is the production session. It is not a fixture and not a separate store.

Nothing mounts it, so nothing has ever executed one of its statements. That is
the only reason it is harmless, and NR-086 is what makes the point sharp: raw
SQL **bypasses** the `NoReferencedTableError` barrier that stops ORM writes
reaching a table whose foreign keys live in another `MetaData`. So this module
is not protected by the thing that protects the ORM write paths. Two other
things protect it, and both are one commit from being undone:

1. it is never mounted, and
2. its SQL names columns the schema does not have.

Executed against PostgreSQL 16 at head `20260915_0003`, each in its own
rolled-back transaction::

    INSERT INTO patients    -> column "name" of relation "patients" does not exist
    INSERT INTO lab_orders  -> column "test_type" of relation "lab_orders" does not exist
    INSERT INTO lab_results -> column "analyte" of relation "lab_results" does not exist

and not as a typo: only 4 of 9, 4 of 9 and 4 of 13 of the named columns exist.
The `SELECT`s name the same absent columns, so the module is dead in both
directions.

**Why this file exists rather than a note in the register.** The natural repair
for someone who finds these files is to reconcile the column names, because
that is what the error messages ask for. Doing only that would produce an
unaudited parallel writer that stores **plaintext national IDs**:
`repositories.py` binds the raw national ID straight into `patients.national_id`,
which has no trigger and no column default, while the canonical path HMACs it
into `national_id_hash` (`app/routes/register.py`) and `app/models/patient.py`
does not map `national_id` at all. None of its `save()` paths writes an audit
row either.

So the ledger below records the columns that are **still** absent from the
canonical mapper. It may shrink, but a reader who shrinks it has begun
activating this module and must answer the national-ID and audit-log questions
first. Retiring the package instead is the recommended disposition, and this
file goes quiet on its own when that happens: every test below passes trivially
once `app/reference` is gone.

A prior decision stopped one step short of that. `test_side_door_hardening.py`
requires `require_permission("system:admin")` on all three routers — they were
hardened *in place* against accidental activation rather than removed. This
file guards the other half: that nothing starts importing them.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from tests.orm_resolution import APP, BACKEND, parse

#: The package under disposition, relative to `backend/`.
PACKAGE = "app/reference"

#: Columns named by `app/reference`'s raw SQL that the canonical mapper does not
#: define. Measured against the live registry, and every one of them was also
#: confirmed absent from PostgreSQL at migration head.
#:
#: `national_id` is deliberately NOT here: it exists physically and is simply
#: unmapped by the canonical model, which is the national-ID story rather than a
#: schema mismatch.
DECLARED_ABSENT: dict[str, tuple[str, ...]] = {
    "patients": ("name", "date_of_birth", "address", "updated_at"),
    "lab_orders": ("test_type", "priority", "notes", "updated_at", "performed_by"),
    "lab_results": (
        "analyte", "min_value", "max_value", "min_critical", "max_critical",
        "is_critical", "flagged", "notes", "performed_by",
    ),
}


def _package_present() -> bool:
    return (BACKEND / PACKAGE).is_dir()


def _is_reference(module: str) -> bool:
    return module == "app.reference" or module.startswith("app.reference.")


def _absolute_module(relative: pathlib.Path, node: ast.ImportFrom) -> str | None:
    """Resolve an `ImportFrom` to the absolute module it names.

    The first version of this got the relative case wrong, and the guard caught
    it on its own first run: `from .reference import router` inside
    `app/national/api/routes/__init__.py` names
    `app.national.api.routes.reference`, which is national reference *data* and
    has nothing to do with `app/reference`. Counting it was a false positive of
    exactly the kind §18 warns about, so the level arithmetic is done properly
    here rather than approximated.

    A module `app/a/b/c.py` and a package `app/a/b/__init__.py` both have
    `('app', 'a', 'b')` as their package, which is `relative.parts[:-1]` in both
    cases. Level 1 resolves against that package, level 2 against its parent,
    and so on.
    """
    module = node.module or ""
    if node.level == 0:
        return module
    package = relative.parts[:-1]
    if node.level > len(package):
        return None  # climbs above backend/; names nothing in this tree
    base = package[: len(package) - (node.level - 1)]
    return ".".join([*base, module]) if module else ".".join(base)


def _importers_outside_the_package() -> dict[str, list[str]]:
    """Modules under `app/` that import `app.reference`, excluding itself.

    Both spellings resolve: the absolute `from app.reference... import X` and the
    relative `from ..reference... import X`, which is how a sibling package
    inside `app/` would reach it.
    """
    found: dict[str, list[str]] = {}
    for path in APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(BACKEND)
        if str(relative).startswith(PACKAGE):
            continue
        tree = parse(path)
        if tree is None:
            continue
        hits: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                hits += [alias.name for alias in node.names if _is_reference(alias.name)]
            elif isinstance(node, ast.ImportFrom):
                resolved = _absolute_module(relative, node)
                if resolved is not None and _is_reference(resolved):
                    hits.append(resolved)
        if hits:
            found[str(relative)] = sorted(set(hits))
    return found


def test_the_import_scan_still_sees_the_application() -> None:
    """Guard the guard, against the population rather than against the finding.

    A floor on "zero importers" is satisfied by a scan that parses nothing at
    all. This asserts the scan still walks a substantial module population, so
    the ratchet below is measured against something.
    """
    modules = 0
    imports = 0
    for path in APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        tree = parse(path)
        if tree is None:
            continue
        modules += 1
        imports += sum(
            1 for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))
        )
    assert modules >= 1500, f"only {modules} modules parsed; the scan has drifted"
    assert imports >= 10000, f"only {imports} import statements seen; the scan has drifted"


def test_nothing_outside_the_package_imports_app_reference() -> None:
    """The ratchet. An import is the first step of mounting it.

    `app/reference` has no dynamic activation path -- the only `__import__`
    calls in `backend/app` are `__import__("datetime")` and `__import__("uuid")`,
    and there is no plugin loader or entry-point machinery that could reach it.
    So a static import is how this package becomes reachable, and it is the
    thing to catch.
    """
    if not _package_present():
        pytest.skip(f"{PACKAGE} has been retired, which is NR-087's recommended disposition")
    importers = _importers_outside_the_package()
    assert importers == {}, (
        f"{PACKAGE} is a parallel raw-SQL write authority over patients, lab_orders "
        "and lab_results, and it is now imported by application code. Before mounting "
        "it, read NR-087: it stores a plaintext national ID where the canonical path "
        f"stores an HMAC, and none of its save() paths writes an audit row: {importers}"
    )


@pytest.mark.parametrize("table", sorted(DECLARED_ABSENT))
def test_the_reference_sql_has_not_been_quietly_reconciled(table: str) -> None:
    """These columns must still be absent from the canonical mapper.

    Not a demand that the code stay broken -- a demand that it not be *half*
    fixed. Reconciling the column names is the change the error messages invite,
    and on its own it converts three dead endpoints into a live unaudited writer
    of plaintext national IDs. If this fails, the reconciliation has started, and
    the national-ID and audit-log questions are now due.
    """
    if not _package_present():
        pytest.skip(f"{PACKAGE} has been retired, which is NR-087's recommended disposition")

    from tests.test_alembic_metadata_registry import _load_registry

    mapped: set[str] = set()
    for _label, metadata in _load_registry():
        if table in metadata.tables:
            mapped |= set(metadata.tables[table].columns.keys())
    assert mapped, f"{table} is mapped by no registered metadata; the registry has drifted"

    reconciled = sorted(set(DECLARED_ABSENT[table]) & mapped)
    assert reconciled == [], (
        f"{table}: columns named by {PACKAGE}'s raw SQL are now defined by the canonical "
        "mapper, so the two schemas are being reconciled. That is the half-fix NR-087 "
        "exists to catch -- answer the plaintext-national-ID and audit-log questions "
        f"before going further: {reconciled}"
    )
