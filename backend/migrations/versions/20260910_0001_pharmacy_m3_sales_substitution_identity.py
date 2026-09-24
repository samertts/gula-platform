"""Reconcile Pharmacy Sales/Substitution identity to the canonical model (P0-2 M3).

P0-2-SUBBLOCKER-A, whole-entity reconciliation (M3-0 §8, Option 2).

``pharmacy_sales``, ``pharmacy_sale_lines``, ``pharmacy_drug_substitution_rules``
and ``pharmacy_drug_substitution_requests`` were created in the Generation B
worldview, where every pharmacy entity has a ``String(26)`` ``_ulid()`` key.
Every other physical Pharmacy table keys on ``INTEGER``. That mismatch is why
three of these tables name integer-keyed targets through ``VARCHAR(26)`` columns
carrying no foreign key at all: PostgreSQL cannot create a ``varchar`` foreign
key onto an ``integer`` primary key, so the constraint was simply left out.

This revision converts the four entities as units rather than patching the
foreign-key columns in isolation:

* the internal primary key becomes ``INTEGER`` with a sequence, matching every
  other Pharmacy table and the identity model frozen in
  ``docs/pharmacy-platform/CANONICAL_DRUG_CONTRACT.md`` §3;
* each entity gains its own immutable public UUID4 identifier, because the
  internal key must never be an entity's public identity (§3, §11 ``PUBLIC_ID``).
  The names follow ``pharmacy_drug_catalog.drug_id`` and the platform's other
  public UUID identifiers;
* the three P0-2-SUBBLOCKER-A **Group A** catalog references become ``INTEGER``
  and finally get the foreign keys the database could never hold;
* the four ``String(26)`` foreign keys between these tables become ``INTEGER``
  and keep their constraints;
* ``sale_lines.batch_id``, ``sale_lines.prescription_id`` and
  ``requests.prescription_id`` — **Group B** — are deliberately left alone.
  Their physical targets are integer-keyed, but ``DrugBatch`` and
  ``Prescription`` are still Generation B in the application, so no canonical
  batch/prescription identity exists to point at. Inventing one is M4's job.

Fail-closed (NR-003 pattern). A ``VARCHAR(26)`` ULID has no deterministic
integer meaning, so this migration never casts identifier *data*: it refuses to
run at all unless all four tables are empty, and reports the exact per-table
counts instead. Emptiness is the migration's own precondition, not an assumption
inherited from the verification environment. It is a realistic one: while these
tables carried ORM-only ``fhir_id``/``fhir_resource_type`` columns, every ORM
INSERT failed with ``UndefinedColumn`` before a row could be created, so the
application cannot have populated them.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql

revision: str = "20260910_0001"
down_revision: str | None = "20260909_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SALES = "pharmacy_sales"
_SALE_LINES = "pharmacy_sale_lines"
_RULES = "pharmacy_drug_substitution_rules"
_REQUESTS = "pharmacy_drug_substitution_requests"

_TABLES = (_SALES, _SALE_LINES, _RULES, _REQUESTS)

# table -> public UUID column
_PUBLIC_IDS: dict[str, str] = {
    _SALES: "sale_id",
    _SALE_LINES: "sale_line_id",
    _RULES: "substitution_rule_id",
    _REQUESTS: "substitution_request_id",
}

# The four String(26) foreign keys between these tables, plus the three Group A
# catalog references. (table, column, referred table, referred column, ondelete)
_INTEGER_REFERENCES: tuple[tuple[str, str, str, str, str], ...] = (
    (_SALE_LINES, "sale_id", _SALES, "id", "CASCADE"),
    (_SALE_LINES, "drug_catalog_id", "pharmacy_drug_catalog", "id", "RESTRICT"),
    (_REQUESTS, "rule_id", _RULES, "id", "RESTRICT"),
    (_REQUESTS, "consumed_sale_id", _SALES, "id", "SET NULL"),
    (_REQUESTS, "original_drug_catalog_id", "pharmacy_drug_catalog", "id", "RESTRICT"),
    (_REQUESTS, "alternative_drug_catalog_id", "pharmacy_drug_catalog", "id", "RESTRICT"),
)

# Explicit constraint names. PostgreSQL truncates auto-generated names at 63
# characters, which several of these would hit; naming them keeps upgrade and
# downgrade able to find what they created.
_FK_NAMES: dict[tuple[str, str], str] = {
    (_SALE_LINES, "sale_id"): "fk_pharmacy_sale_lines_sale",
    (_SALE_LINES, "drug_catalog_id"): "fk_pharmacy_sale_lines_drug_catalog",
    (_REQUESTS, "rule_id"): "fk_pharmacy_substitution_request_rule",
    (_REQUESTS, "consumed_sale_id"): "fk_pharmacy_substitution_request_sale",
    (_REQUESTS, "original_drug_catalog_id"): "fk_pharmacy_substitution_request_original_drug",
    (_REQUESTS, "alternative_drug_catalog_id"): "fk_pharmacy_substitution_request_alternative_drug",
}

# Constraint names PostgreSQL generated when the tables were created. Dropped on
# upgrade and restored on downgrade.
_LEGACY_FK_NAMES: dict[tuple[str, str], str] = {
    (_SALE_LINES, "sale_id"): "pharmacy_sale_lines_sale_id_fkey",
    (_REQUESTS, "rule_id"): "pharmacy_drug_substitution_requests_rule_id_fkey",
    (_REQUESTS, "consumed_sale_id"): "pharmacy_drug_substitution_requests_consumed_sale_id_fkey",
}

_NULLABLE_REFERENCES = frozenset({(_REQUESTS, "consumed_sale_id")})


def _pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _has_column(table: str, column: str) -> bool:
    return any(c["name"] == column for c in inspect(op.get_bind()).get_columns(table))


def _column_type(table: str, column: str) -> str:
    for c in inspect(op.get_bind()).get_columns(table):
        if c["name"] == column:
            return str(c["type"])
    raise KeyError(f"{table}.{column} does not exist")


def _index_exists(table: str, name: str) -> bool:
    return any(i["name"] == name for i in inspect(op.get_bind()).get_indexes(table))


def _unique_exists(table: str, name: str) -> bool:
    return any(c["name"] == name for c in inspect(op.get_bind()).get_unique_constraints(table))


def _fk_exists(table: str, name: str) -> bool:
    return any(fk["name"] == name for fk in inspect(op.get_bind()).get_foreign_keys(table))


def _installed() -> bool:
    return all(_table_exists(t) for t in _TABLES)


def _require_empty(direction: str) -> None:
    """Refuse to convert identifiers unless every affected table is empty.

    A ``VARCHAR(26)`` ULID and an ``INTEGER`` key have no deterministic mapping
    in either direction. Rather than cast, truncate or drop anything, this
    aborts the transaction and reports what it found.
    """
    bind = op.get_bind()
    populated = {}
    for table in _TABLES:
        count = bind.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
        if count:
            populated[table] = count
    if populated:
        detail = ", ".join(f"{t}={n}" for t, n in sorted(populated.items()))
        raise RuntimeError(
            f"P0-2 M3 {direction} preflight failed: identifier conversion requires the "
            f"Sales/Substitution tables to be empty, but found rows ({detail}). No schema "
            f"or data was changed. A VARCHAR(26) ULID has no deterministic integer meaning, "
            f"so these rows must be exported and re-created deliberately, never cast."
        )


def _to_integer_key(table: str) -> None:
    """Convert ``table.id`` from VARCHAR(26) to a sequence-backed INTEGER key."""
    if _column_type(table, "id").upper().startswith("INTEGER"):
        return
    sequence = f"{table}_id_seq"
    op.alter_column(
        table,
        "id",
        existing_type=sa.String(26),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using="id::integer",
    )
    # Match the SERIAL shape every other Pharmacy table uses, rather than an
    # identity column, so reflection and Alembic autogenerate stay consistent.
    op.execute(f"CREATE SEQUENCE IF NOT EXISTS {sequence} OWNED BY {table}.id")
    op.execute(f"ALTER TABLE {table} ALTER COLUMN id SET DEFAULT nextval('{sequence}')")


def _to_string_key(table: str) -> None:
    """Reverse of :func:`_to_integer_key`."""
    if _column_type(table, "id").upper().startswith("VARCHAR"):
        return
    sequence = f"{table}_id_seq"
    op.execute(f"ALTER TABLE {table} ALTER COLUMN id DROP DEFAULT")
    op.execute(f"DROP SEQUENCE IF EXISTS {sequence}")
    op.alter_column(
        table,
        "id",
        existing_type=sa.Integer(),
        type_=sa.String(26),
        existing_nullable=False,
        postgresql_using="id::varchar(26)",
    )


def upgrade() -> None:
    if not _installed():
        # The pharmacy POS/substitution platform is not present here.
        return
    if not _pg():
        # The conversion is expressed in PostgreSQL DDL (USING clauses,
        # sequences). Every environment that has these tables is PostgreSQL.
        return

    _require_empty("upgrade")

    # 1. Release the String(26) foreign keys before retyping either side.
    for (table, _column), name in _LEGACY_FK_NAMES.items():
        if _fk_exists(table, name):
            op.drop_constraint(name, table, type_="foreignkey")
    for (table, _column), name in _FK_NAMES.items():
        if _fk_exists(table, name):
            op.drop_constraint(name, table, type_="foreignkey")

    # 2. Canonicalise each entity's own key.
    for table in _TABLES:
        _to_integer_key(table)

    # 3. Canonicalise the outbound references, Group A included.
    for table, column, _referred, _referred_col, _ondelete in _INTEGER_REFERENCES:
        if _column_type(table, column).upper().startswith("INTEGER"):
            continue
        op.alter_column(
            table,
            column,
            existing_type=sa.String(26),
            type_=sa.Integer(),
            existing_nullable=(table, column) in _NULLABLE_REFERENCES,
            postgresql_using=f"{column}::integer",
        )

    # 4. Re-establish real, enforced foreign keys — including the three Group A
    #    catalog references, which have never had one.
    for table, column, referred, referred_col, ondelete in _INTEGER_REFERENCES:
        name = _FK_NAMES[(table, column)]
        if not _fk_exists(table, name):
            op.create_foreign_key(name, table, referred, [column], [referred_col], ondelete=ondelete)

    # 5. Give each entity its immutable public identity.
    for table, column in _PUBLIC_IDS.items():
        index = f"ix_{table}_{column}"
        unique = f"uq_{table}_{column}"
        if not _has_column(table, column):
            op.add_column(table, sa.Column(column, postgresql.UUID(as_uuid=True), nullable=True))
        # Backfill only rows without an identity, so a re-run never regenerates
        # one that has already been published. (The tables are empty here by
        # precondition; the guard is what makes the step safe to repeat.)
        op.execute(f"UPDATE {table} SET {column} = gen_random_uuid() WHERE {column} IS NULL")
        remaining = op.get_bind().execute(
            text(f"SELECT count(*) FROM {table} WHERE {column} IS NULL")
        ).scalar_one()
        if remaining:
            raise RuntimeError(
                f"P0-2 M3 preflight failed: {remaining} row(s) in {table} still have a NULL "
                f"{column} after backfill. Aborting before applying NOT NULL; nothing was changed."
            )
        op.alter_column(
            table, column, existing_type=postgresql.UUID(as_uuid=True), nullable=False
        )
        if not _unique_exists(table, unique):
            op.create_unique_constraint(unique, table, [column])
        if not _index_exists(table, index):
            op.create_index(index, table, [column])


def downgrade() -> None:
    if not _installed() or not _pg():
        return

    _require_empty("downgrade")

    for table, column in _PUBLIC_IDS.items():
        index = f"ix_{table}_{column}"
        unique = f"uq_{table}_{column}"
        if _index_exists(table, index):
            op.drop_index(index, table_name=table)
        if _unique_exists(table, unique):
            op.drop_constraint(unique, table, type_="unique")
        if _has_column(table, column):
            op.drop_column(table, column)

    for (table, _column), name in _FK_NAMES.items():
        if _fk_exists(table, name):
            op.drop_constraint(name, table, type_="foreignkey")

    for table, column, _referred, _referred_col, _ondelete in _INTEGER_REFERENCES:
        if _column_type(table, column).upper().startswith("VARCHAR"):
            continue
        op.alter_column(
            table,
            column,
            existing_type=sa.Integer(),
            type_=sa.String(26),
            existing_nullable=(table, column) in _NULLABLE_REFERENCES,
            postgresql_using=f"{column}::varchar(26)",
        )

    for table in _TABLES:
        _to_string_key(table)

    # Restore only the constraints that existed before this revision. The three
    # Group A catalog foreign keys are not restored: they never existed, and
    # PostgreSQL cannot create a varchar foreign key onto an integer key.
    for (table, column), name in _LEGACY_FK_NAMES.items():
        referred, referred_col, ondelete = next(
            (r, rc, od)
            for t, c, r, rc, od in _INTEGER_REFERENCES
            if (t, c) == (table, column)
        )
        if not _fk_exists(table, name):
            op.create_foreign_key(name, table, referred, [column], [referred_col], ondelete=ondelete)
