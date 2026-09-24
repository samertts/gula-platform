"""NR-069 — "is this table built?" must be answered by the migrations.

Every ratchet in this suite rests on one predicate: does a migration create this
table? NR-063, NR-065, NR-066 and NR-067 all reduce to it. So it is worth stating
how it was wrong.

`docs/architecture/evidence-created-tables.json` was assembled by matching
`op.create_table("literal", ...)`. Three tables are not created that way.
`20260814_0002_organization_structure.py` routes its creates through

    def _create_if_missing(name, columns, constraints):
        if name in sa.inspect(bind).get_table_names():
            return
        op.create_table(name, *columns, *constraints)

where the literal sits at the **call site**, not at the create. So
`niam_admin_units`, `niam_organization_representatives` and
`niam_organization_ownerships` were recorded as unbuilt while the chain does
build them -- and `niam_admin_units` is the target of
`niam_role_assignments.unit_id`, one of the five canonical authorization scopes.

The error ran in the direction that overstates the problem: rows against those
three were counted as reads and writes against nothing. Re-measured after the
repair, **no published ledger moved** -- reachable unbuilt reads stayed at 418
across 20 route modules and unbuilt writes at 268 -- because nothing on those
paths touches the three. That is the honest outcome: a real defect in the
evidence base with no effect on the conclusions drawn from it. It is recorded
because the next one might not be so harmless.

The repair is structural rather than a corrected snapshot. `built_tables()` now
derives from the migration chain and resolves all three forms the chain uses:
a literal, a module-level constant, and a local helper that forwards one of its
own parameters. The snapshot is kept for consumers outside this suite and is
asserted equal here, so it cannot drift again without failing.

When the two disagree, **the migrations are right and the snapshot is stale.**
Regenerate it; never edit the derivation to match the file.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from tests.orm_resolution import (
    MIGRATIONS,
    _created_in,
    built_tables,
    declared_built_tables,
)

#: The three the literal-only scan missed, and the migration that creates them.
#: Named rather than counted: a rot check that only compared totals would pass
#: while the set drifted.
HELPER_CREATED = {
    "niam_admin_units",
    "niam_organization_representatives",
    "niam_organization_ownerships",
}
HELPER_MIGRATION = "20260814_0002_organization_structure.py"


def test_the_derivation_still_sees_the_migration_chain() -> None:
    """Guard the guard: an empty derivation would mark every table unbuilt."""
    assert len(built_tables()) >= 400, (
        f"only {len(built_tables())} built tables derived from "
        f"{MIGRATIONS}; the scan has drifted and every ledger keyed on "
        "'is this built?' would flip to its most alarming reading"
    )


def test_the_snapshot_matches_the_migration_chain() -> None:
    """The snapshot is a cache of the chain, and a cache may not disagree."""
    derived, declared = built_tables(), declared_built_tables()
    missing = sorted(derived - declared)
    phantom = sorted(declared - derived)
    assert missing == [], (
        "the migration chain creates these tables and the checked-in snapshot "
        "does not list them, so every guard reading the snapshot treats them as "
        f"absent. Regenerate the snapshot from the chain: {missing}"
    )
    assert phantom == [], (
        "the snapshot claims these tables are built but no migration creates "
        f"them, so guards would wave through reads that raise UndefinedTable: {phantom}"
    )


def test_tables_created_through_a_helper_are_still_resolved() -> None:
    """The specific defect, as a regression rather than a memory.

    A literal-only scan passes `test_the_snapshot_matches_the_migration_chain`
    trivially once the snapshot is regenerated to match it -- both sides would
    be wrong together. This asserts the three by name against the chain.
    """
    created = _created_in(MIGRATIONS / HELPER_MIGRATION)
    missing = sorted(HELPER_CREATED - created)
    assert missing == [], (
        f"{HELPER_MIGRATION} creates these through `_create_if_missing`, where "
        "the table name is a function parameter rather than a literal at the "
        "`op.create_table` call. The derivation no longer resolves that form, "
        f"so they are being reported as unbuilt again: {missing}"
    )
    assert built_tables() >= HELPER_CREATED, (
        "resolved inside the migration but absent from the derived set"
    )


def test_the_helper_form_still_exists_to_be_resolved() -> None:
    """If the chain stops using the helper, this guard is protecting nothing.

    That is not a failure -- it is a signal to delete this file rather than keep
    a test whose subject is gone. Asserted so the choice is deliberate.
    """
    tree = ast.parse((MIGRATIONS / HELPER_MIGRATION).read_text(encoding="utf-8"))
    forwarded = False
    for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
        params = [a.arg for a in fn.args.args]
        for call in ast.walk(fn):
            if (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr == "create_table"
                and call.args
                and isinstance(call.args[0], ast.Name)
                and call.args[0].id in params
            ):
                forwarded = True
    assert forwarded, (
        f"{HELPER_MIGRATION} no longer passes a parameter to op.create_table. "
        "The form this guard exists for is gone; either the chain changed or "
        "the migration was edited, which the migration policy forbids"
    )


# ── The extractor, tested against patterns rather than against this repository ──
#
# Everything above asserts against the real migration chain, which is necessary
# and not sufficient: those tests pass if the chain and the extractor are wrong
# together, and they break when a migration is edited for unrelated reasons.
#
# These cases pin the extractor's contract on synthetic input. Each is a form
# that appears, or could appear, in an Alembic migration. The helper case is the
# one that caused NR-069; the rest are here so that fixing it did not narrow the
# extractor to that single shape.

_LITERAL_SRC = "\n".join([
    "from alembic import op",
    "import sqlalchemy as sa",
    "",
    "def upgrade() -> None:",
    "    op.create_table('plain_one', sa.Column('id', sa.Integer, primary_key=True))",
    "    op.create_table('plain_two', sa.Column('id', sa.Integer, primary_key=True))",
])

_CONSTANT_SRC = "\n".join([
    "from alembic import op",
    "import sqlalchemy as sa",
    "",
    "_TABLE = 'constant_named'",
    "_OTHER = 'constant_second'",
    "",
    "def upgrade() -> None:",
    "    op.create_table(_TABLE, sa.Column('id', sa.Integer, primary_key=True))",
    "    op.create_table(_OTHER, sa.Column('id', sa.Integer, primary_key=True))",
])

_HELPER_SRC = "\n".join([
    "from alembic import op",
    "import sqlalchemy as sa",
    "",
    "def _create_if_missing(name, columns, constraints):",
    "    bind = op.get_bind()",
    "    if name in sa.inspect(bind).get_table_names():",
    "        return",
    "    op.create_table(name, *columns, *constraints)",
    "",
    "def upgrade() -> None:",
    "    _create_if_missing('helper_made', [sa.Column('id', sa.Integer)], [])",
    "    _create_if_missing('helper_made_two', [sa.Column('id', sa.Integer)], [])",
    "    op.create_index('ix_helper_made', 'helper_made', ['id'])",
])

_HELPER_SECOND_ARG_SRC = "\n".join([
    "from alembic import op",
    "import sqlalchemy as sa",
    "",
    "def _make(columns, name):",
    "    op.create_table(name, *columns)",
    "",
    "def upgrade() -> None:",
    "    _make([sa.Column('id', sa.Integer)], 'second_position')",
])

_CONDITIONAL_SRC = "\n".join([
    "from alembic import op",
    "import sqlalchemy as sa",
    "",
    "def _has(table):",
    "    return table in sa.inspect(op.get_bind()).get_table_names()",
    "",
    "def upgrade() -> None:",
    "    if not _has('conditional_table'):",
    "        op.create_table('conditional_table', sa.Column('id', sa.Integer))",
])

_REFERENCE_ONLY_SRC = "\n".join([
    "from alembic import op",
    "import sqlalchemy as sa",
    "",
    "def upgrade() -> None:",
    "    op.create_table(",
    "        'child_table',",
    "        sa.Column('id', sa.Integer, primary_key=True),",
    "        sa.Column('parent_id', sa.Integer),",
    "        sa.ForeignKeyConstraint(['parent_id'], ['never_created_parent.id']),",
    "    )",
    "    op.create_index('ix_child_parent', 'child_table', ['parent_id'])",
    "    op.add_column('some_other_table', sa.Column('x', sa.Integer))",
])

_ALTER_ONLY_SRC = "\n".join([
    "from alembic import op",
    "import sqlalchemy as sa",
    "",
    "def upgrade() -> None:",
    "    op.add_column('existing', sa.Column('flag', sa.Boolean()))",
    "    op.drop_column('existing', 'old')",
    "    op.execute('UPDATE existing SET flag = true')",
])

_CASES = {
    "literal": (_LITERAL_SRC, {"plain_one", "plain_two"}),
    "module_constant": (_CONSTANT_SRC, {"constant_named", "constant_second"}),
    "helper_first_arg": (_HELPER_SRC, {"helper_made", "helper_made_two"}),
    "helper_second_arg": (_HELPER_SECOND_ARG_SRC, {"second_position"}),
    "conditional": (_CONDITIONAL_SRC, {"conditional_table"}),
    "reference_only": (_REFERENCE_ONLY_SRC, {"child_table"}),
    "alter_only": (_ALTER_ONLY_SRC, set()),
}


@pytest.mark.parametrize("case", sorted(_CASES))
def test_the_extractor_resolves_each_creation_form(
    case: str, tmp_path: pathlib.Path,
) -> None:
    """One synthetic migration per creation form, asserted exactly.

    Exact equality matters in both directions. `reference_only` is the case that
    proves it: a foreign key naming `never_created_parent`, an index, and an
    `add_column` on `some_other_table` must NOT make any of those look built.
    That is the opposite of the NR-069 error and the more dangerous direction,
    because under-reporting the unbuilt surface waves through reads that raise
    UndefinedTable at runtime.

    `alter_only` pins the empty case, so a data migration contributes nothing.
    """
    source, expected = _CASES[case]
    migration = tmp_path / f"20990101_0001_{case}.py"
    migration.write_text(source, encoding="utf-8")
    assert _created_in(migration) == expected, (
        f"the {case} creation form no longer resolves as expected"
    )


def test_the_extractor_survives_a_migration_it_cannot_parse(
    tmp_path: pathlib.Path,
) -> None:
    """A syntax error must yield nothing, not raise.

    The derivation runs over every file in `migrations/versions`. If one
    unparseable file aborted the scan, `built_tables()` would return a partial
    set and every ledger would over-report the unbuilt surface -- silently,
    because a partial answer still looks like a plausible number.
    """
    migration = tmp_path / "20990101_0002_broken.py"
    migration.write_text("def upgrade(:\n    pass\n", encoding="utf-8")
    assert _created_in(migration) == set()
