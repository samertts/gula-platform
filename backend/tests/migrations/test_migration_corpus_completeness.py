"""Static guards on the migration corpus itself.

These run in every lane — no database, no network — because the defects they
catch are properties of the migration files, and finding them by executing a
five-minute ``upgrade head`` discovers exactly one blocker per run.

Two properties are asserted.

**Every foreign-key target must be created by some migration.** ``20260820_0004``
creates ``hospital_surgical_safety_checklists`` with foreign keys into
``hospitals``, ``hospital_departments`` and ``hospital_operation_theaters`` — and
no migration in the corpus creates any of the thirteen tables of the hospital
domain. The revision therefore aborts inside itself on every migration-built
database, exactly as ``20260815_0023`` did before NR-003 was repaired, and it
sits directly in front of ``20260820_0005``, the revision that adds the ICU
independent-verification columns.

**Every revision must be idempotent**, which the repository's migration policy
states as MANDATORY. A revision that re-runs cleanly can be recovered by
re-running; one that cannot forces a database-level repair when a partial
upgrade has to be resumed.

Both assertions are ratchets against a recorded baseline rather than bare
zero-tolerance rules. There are 102 revisions with real history behind them;
a rule that failed on all of it would be switched off within a week, and a
switched-off gate catches nothing. The ratchets fail on anything *new*.
"""

from __future__ import annotations

import ast
import collections
import pathlib
import re

VERSIONS = pathlib.Path(__file__).resolve().parents[2] / "migrations" / "versions"

# ---------------------------------------------------------------------------
# Foreign-key targets with no creator
# ---------------------------------------------------------------------------

# Measured on 2026-09-25. AST analysis reports three targets with no literal
# ``create_table`` call naming them. Two are false positives confirmed against a
# live migration-built database: ``niam_admin_units`` and ``national_facilities``
# are created through a helper that passes the table name as a *variable*
# (``op.create_table(name, *columns, *constraints)``), which no static reader can
# resolve, and both exist physically. Physical introspection is the arbiter, and
# it leaves exactly one genuine case.
KNOWN_INDIRECTLY_CREATED = {"niam_admin_units", "national_facilities"}

# NR-028. Absent from every migration-built database checked: a 20260908_0002
# build (391 tables), a 20260819_0003 build (410 tables) and a failed
# ``upgrade head`` (32 tables). Created by no migration; declared by
# ``app.hospital.models.OperationTheater`` in the ORM.
KNOWN_UNCREATED_FK_TARGETS = {"hospital_operation_theaters"}


def _string(node: ast.AST) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _corpus() -> list[tuple[str, ast.Module, str]]:
    out = []
    for path in sorted(VERSIONS.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        out.append((path.name, ast.parse(text), text))
    return out


def _created_and_referenced() -> tuple[set[str], dict[str, set[str]]]:
    created: set[str] = set()
    referenced: dict[str, set[str]] = collections.defaultdict(set)
    for name, tree, _text in _corpus():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            called = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if called == "create_table" and node.args:
                table = _string(node.args[0])
                if table:
                    created.add(table)
            elif called == "ForeignKey" and node.args:
                target = _string(node.args[0])
                if target and "." in target:
                    referenced[target.split(".")[0]].add(name)
            elif called == "ForeignKeyConstraint" and len(node.args) >= 2:
                refs = node.args[1]
                if isinstance(refs, (ast.List, ast.Tuple)):
                    for element in refs.elts:
                        target = _string(element)
                        if target and "." in target:
                            referenced[target.split(".")[0]].add(name)
    return created, dict(referenced)


def test_no_new_foreign_key_target_lacks_a_creating_migration() -> None:
    """A revision must not reference a table the corpus never creates.

    Such a revision cannot succeed on any migration-built database, and because
    the abort happens inside it, nothing ordered after it runs either — so one
    unsatisfiable foreign key strands every later revision, including unrelated
    clinical ones.
    """
    created, referenced = _created_and_referenced()
    uncreated = {t: sorted(f) for t, f in referenced.items() if t not in created}
    unexpected = {
        t: f for t, f in uncreated.items()
        if t not in KNOWN_INDIRECTLY_CREATED and t not in KNOWN_UNCREATED_FK_TARGETS
    }
    assert unexpected == {}, (
        "these foreign-key targets are created by no migration, so the "
        f"referencing revisions cannot apply: {unexpected}"
    )


def test_the_recorded_uncreated_target_is_still_exactly_the_known_one() -> None:
    """Pin NR-028 precisely, so a repair fails here as loudly as a regression.

    When the hospital domain gains migrations this test fails, and the baseline
    above has to be emptied deliberately — which is the moment to re-run
    ``upgrade head`` and confirm the chain is actually clear.
    """
    created, referenced = _created_and_referenced()
    uncreated = {t for t in referenced if t not in created}
    assert uncreated - KNOWN_INDIRECTLY_CREATED == KNOWN_UNCREATED_FK_TARGETS


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

_GUARD = re.compile(
    r"_table_exists|_index_exists|_has_column|_column_exists|_constraint_exists"
    r"|IF NOT EXISTS|IF EXISTS|checkfirst|has_table"
)
_SCHEMA_OP = re.compile(r"op\.(create_table|add_column|create_index|create_unique_constraint)\(")

# Measured on 2026-09-25: of 101 revisions, 37 perform a schema operation with no
# recognisable guard. The number is the ratchet; the list is not pinned here
# because it is pre-existing debt with real history, and enumerating 37 filenames
# in a test would produce a file nobody re-reads. Set to the measured value, not
# a comfortable margin above it — a ratchet with slack in it is not a ratchet.
UNGUARDED_BASELINE = 37

# NR-029. These two matter more than their count suggests: they are the last two
# revisions before head on the ICU branch, so a partial upgrade that stops
# between them cannot be resumed by re-running — it needs a database-level
# repair. ``20260820_0004`` was observed failing with DuplicateTable on a
# re-attempt for exactly this reason.
NAMED_UNGUARDED = {
    "20260820_0004_surgical_safety_checklists.py",
    "20260820_0005_icu_infusion_independent_verification.py",
}


def _unguarded() -> set[str]:
    out = set()
    for name, _tree, text in _corpus():
        body = text.split("def upgrade", 1)[-1]
        if _SCHEMA_OP.search(body) and not _GUARD.search(body):
            out.add(name)
    return out


def test_unguarded_migration_count_does_not_grow() -> None:
    """New revisions must be idempotent; the existing backlog is held, not hidden."""
    unguarded = _unguarded()
    assert len(unguarded) <= UNGUARDED_BASELINE, (
        f"unguarded revisions rose from {UNGUARDED_BASELINE} to {len(unguarded)}; "
        f"new offenders are among: {sorted(unguarded)}"
    )


def test_the_two_icu_blocking_revisions_are_still_the_recorded_unguarded_pair() -> None:
    """Pin NR-029 on the two revisions where it has a proven consequence."""
    unguarded = _unguarded()
    assert unguarded >= NAMED_UNGUARDED, (
        "one of the two ICU-path revisions gained a guard — good; update "
        f"NAMED_UNGUARDED and re-check the resume path. Still unguarded: {sorted(NAMED_UNGUARDED & unguarded)}"
    )
