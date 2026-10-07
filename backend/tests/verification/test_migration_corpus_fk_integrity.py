"""A migration may not name a table or a type the corpus cannot provide.

IA-054/IA-056. ``alembic upgrade head`` on a clean PostgreSQL 16 database exits
1 on this branch and on ``origin/main``. Measured, not inferred::

    claude/autonomous-run-1 (203c85aa)  98 migrations in, then
        psycopg2.errors.DatatypeMismatch: foreign key constraint
        "pharmacy_drug_substitution_rules_original_drug_catalog_id_fkey"
        cannot be implemented
        DETAIL: Key columns "original_drug_catalog_id" and "id" are of
        incompatible types: character varying and integer.

    claude/independent-audit-1 (74340273)  98 migrations in, then
        psycopg2.errors.UndefinedTable:
        relation "hospital_operation_theaters" does not exist

Both runs left the same unusable partial schema: 32 tables, ``alembic_version``
stamped ``20260505_0005``, which is not a head. CI agrees -- the Migration Check
job is ``failure`` on main's head 46158e90 and on the five runs before it.

WHY THE EXISTING GUARDS CANNOT SEE THIS.

``test_hard_error_type_drift.py`` compares each ORM column against the physical
column it maps to, and pins the 162 cross-family disagreements that NR-062's
identity decision has to resolve. It is a statement about the ORM versus the
database. It has nothing to say about a migration that declares a foreign key
against a *table another migration created*, because neither side of that
comparison is an ORM column. ``test_migration_corpus_completeness.py`` and
``test_migration_graph_integrity.py`` check the revision graph, not column
types. So the corpus can contradict itself and every guard stays green.

This guard closes exactly that gap, over both declaration shapes --
``sa.Column(..., sa.ForeignKey("t.c"))`` and
``sa.ForeignKeyConstraint(["c"], ["t.c"])``. The second shape is why the first
pass of this measurement reported zero missing targets and had to be redone;
``20260820_0004`` uses it.

SUBSET FOR TARGETS, ZERO FOR TYPES -- and the asymmetry is deliberate.

The two missing target tables are a real decision, not sloppiness.
``hospital_operation_theaters`` and ``national_facilities`` are both
ORM-mapped and neither is created by any of the 102 migrations; supplying them
is a schema change, which CLAUDE.md puts behind human approval, and
``national_facilities`` is entangled with NR-006's ownership retirement. So they
are pinned as a subset: repairing one passes and is reported, introducing a
third fails.

The type check demands zero because on this branch it *is* zero -- 048e2725
settled the direction (integer is canonical where a ULID table references an
integer-keyed legacy table) and brought the corpus to 0 of 638 foreign keys
mismatched. Nothing needs deciding to keep it there, so a regression must fail
rather than be absorbed into a pin.
"""
from __future__ import annotations

import ast
import collections
import pathlib

import pytest

VERSIONS = pathlib.Path(__file__).resolve().parents[2] / "migrations" / "versions"

#: FK target tables no migration creates. Pinned, not demanded-zero: supplying
#: either is a schema change behind human approval. Repairing one passes.
KNOWN_MISSING_TARGETS = frozenset({
    "hospital_operation_theaters",   # 20260820_0004, ORM app/hospital/models/__init__.py:172
})

#: Type families PostgreSQL refuses to compare across a foreign key.
FAMILY = {
    "Integer": "int", "BigInteger": "int", "SmallInteger": "int",
    "String": "str", "Text": "str", "Unicode": "str",
    "UnicodeText": "str", "CHAR": "str",
    "UUID": "uuid", "Uuid": "uuid",
}


def _callee(node: ast.AST) -> str | None:
    call = node.func if isinstance(node, ast.Call) else node
    if isinstance(call, ast.Attribute):
        return call.attr
    if isinstance(call, ast.Name):
        return call.id
    return None


def _str_const(node: ast.AST, consts: dict[str, str] | None = None) -> str | None:
    """A table name, whether written inline or held in a module constant.

    The constant form is a real false negative this guard had: the first
    version matched only ast.Constant, so
    ``op.create_table(_NATIONAL_FACILITIES, ...)`` in 20260813_0004 was
    invisible and national_facilities was reported as a table no migration
    creates. It is created, immediately before the foreign key that needs it.
    Nine create_table sites in the corpus take a non-literal first argument.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if consts is not None and isinstance(node, ast.Name):
        return consts.get(node.id)
    return None


def _module_constants(tree: ast.Module) -> dict[str, str]:
    """Module-level ``NAME = "string"`` assignments."""
    found: dict[str, str] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found[target.id] = node.value.value
    return found


@pytest.fixture(scope="module")
def corpus():
    """Parse every migration once: tables created, columns typed, FKs declared."""
    created: set[str] = set()
    declared: dict[str, dict[str, tuple[str, str, int]]] = collections.defaultdict(dict)
    fks: list[tuple[str, str, str | None, str, str, int]] = []

    files = sorted(VERSIONS.glob("*.py"))
    assert files, f"no migrations found under {VERSIONS}"

    for path in files:
        source = path.read_text(errors="replace")
        tree = ast.parse(source)
        consts = _module_constants(tree)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            kind = _callee(node)

            if kind in ("create_table", "_create_if_missing") and node.args:
                table = _str_const(node.args[0], consts)
                if table is None:
                    continue
                created.add(table)
                # columns may be positional, or inside a list for the helper form
                candidates = list(node.args[1:])
                for arg in node.args[1:]:
                    if isinstance(arg, (ast.List, ast.Tuple)):
                        candidates.extend(arg.elts)
                for arg in candidates:
                    if not (isinstance(arg, ast.Call) and _callee(arg) == "Column"):
                        continue
                    if not arg.args:
                        continue
                    col = _str_const(arg.args[0])
                    if col is None:
                        continue
                    col_type = None
                    for extra in arg.args[1:]:
                        name = _callee(extra)
                        if name and name != "ForeignKey" and col_type is None:
                            col_type = name
                    if col_type:
                        declared[table].setdefault(col, (col_type, path.name, arg.lineno))

            if kind == "ForeignKey" and node.args:
                target = _str_const(node.args[0])
                if target and "." in target:
                    fks.append(("", "", None, target, path.name, node.lineno))

            if kind == "ForeignKeyConstraint" and len(node.args) >= 2:
                targets = node.args[1]
                if isinstance(targets, (ast.List, ast.Tuple)):
                    for element in targets.elts:
                        target = _str_const(element)
                        if target and "." in target:
                            fks.append(("", "", None, target, path.name, node.lineno))

    # second pass: inline FKs need their own column's declared type, which the
    # first pass recorded, so resolve them against `declared`
    typed_fks: list[tuple[str, str, str, str, str, int]] = []
    for path in files:
        tree = ast.parse(path.read_text(errors="replace"))
        consts = _module_constants(tree)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and _callee(node) in ("create_table", "_create_if_missing")):
                continue
            if not node.args:
                continue
            table = _str_const(node.args[0], consts)
            if table is None:
                continue
            candidates = list(node.args[1:])
            for arg in node.args[1:]:
                if isinstance(arg, (ast.List, ast.Tuple)):
                    candidates.extend(arg.elts)
            for arg in candidates:
                if not (isinstance(arg, ast.Call) and _callee(arg) == "Column" and arg.args):
                    continue
                col = _str_const(arg.args[0])
                col_type, target = None, None
                for extra in arg.args[1:]:
                    name = _callee(extra)
                    if name == "ForeignKey" and isinstance(extra, ast.Call) and extra.args:
                        target = _str_const(extra.args[0])
                    elif name and name != "ForeignKey" and col_type is None:
                        col_type = name
                if col and col_type and target and "." in target:
                    typed_fks.append((table, col, col_type, target, path.name, arg.lineno))

    return {
        "files": files,
        "created": created,
        "declared": declared,
        "fk_targets": fks,
        "typed_fks": typed_fks,
    }


def test_the_measurement_actually_covers_the_corpus(corpus):
    """A parser that silently stopped finding things would make this guard inert."""
    assert len(corpus["files"]) >= 100, len(corpus["files"])
    assert len(corpus["created"]) >= 400, len(corpus["created"])
    assert len(corpus["typed_fks"]) >= 600, len(corpus["typed_fks"])
    assert any(
        target.startswith("hospital_operation_theaters")
        for _, _, _, target, _, _ in corpus["fk_targets"]
    ), "the ForeignKeyConstraint shape is not being parsed -- the gap this guard exists for"


def test_no_migration_names_an_fk_target_the_corpus_never_creates(corpus):
    missing: dict[str, list[tuple[str, int]]] = collections.defaultdict(list)
    for _, _, _, target, filename, line in corpus["fk_targets"]:
        table = target.rsplit(".", 1)[0]
        if table not in corpus["created"]:
            missing[table].append((filename, line))

    new = set(missing) - KNOWN_MISSING_TARGETS
    assert not new, (
        "a migration names a foreign-key target no migration creates, which aborts "
        "`alembic upgrade head` on a clean database: "
        + "; ".join(f"{t} at {missing[t][0][0]}:{missing[t][0][1]}" for t in sorted(new))
    )


def test_the_pin_is_reported_rather_than_left_stale(corpus):
    """Repairing a pinned table passes; this says so instead of failing."""
    present = {t for t in KNOWN_MISSING_TARGETS if t in corpus["created"]}
    if present:
        print(
            "\nKNOWN_MISSING_TARGETS now created by a migration (shrink the pin): "
            + ", ".join(sorted(present))
        )


def test_every_foreign_key_type_matches_the_column_it_points_at(corpus):
    """Zero, not a pin: 048e2725 settled the direction and nothing needs deciding."""
    mismatches = []
    for table, col, col_type, target, filename, line in corpus["typed_fks"]:
        target_table, target_col = target.rsplit(".", 1)
        record = corpus["declared"].get(target_table, {}).get(target_col)
        if record is None:
            continue
        target_type, target_file, target_line = record
        if FAMILY.get(col_type, col_type) != FAMILY.get(target_type, target_type):
            mismatches.append(
                f"{table}.{col} is {col_type} at {filename}:{line} but "
                f"{target} is {target_type} at {target_file}:{target_line}"
            )

    assert not mismatches, (
        "a foreign key is declared in a type family PostgreSQL refuses to compare "
        "with its target, which aborts `alembic upgrade head`: " + "; ".join(mismatches)
    )


def test_a_table_created_through_a_module_constant_is_seen(corpus):
    """The false negative this guard shipped with, pinned so it cannot return.

    20260813_0004 creates national_facilities as
    ``op.create_table(_NATIONAL_FACILITIES, ...)``. A scanner that matches only
    string literals reports it missing -- which is exactly what the first
    version of this file did, and what the previous audit cycle published.
    """
    assert "national_facilities" in corpus["created"], (
        "module-constant table names are invisible again; the scan would "
        "report national_facilities as uncreated, which is false"
    )
    assert "clinical_ehr_facility_bindings" in corpus["created"]
    assert "niam_legacy_account_links" in corpus["created"]
