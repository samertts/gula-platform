"""Give the Pharmacy inventory and dispensing entities canonical identity (P0-2 M4).

M4 completes what M1-M3 began. The physical schema was already right: every
Pharmacy primary key is ``INTEGER`` and the relational graph between batches,
prescriptions, stock and dispensing is fully constrained. What was wrong was the
ORM, which described a Generation B schema that does not exist — and three
columns M3 deliberately left alone because their targets had no canonical
application model yet.

This revision makes two kinds of change.

**Public identities.** Five entities are addressed by identifier in the public
API — ``/batches/{batch_id}``, ``/prescriptions/{rx_id}``,
``/prescriptions/{rx_id}/items/{item_id}``, ``/dispense-queue/{queue_id}`` and
``/inventory/transfers/{transfer_id}``. Their internal ``INTEGER`` key must
never be that identifier (CANONICAL_DRUG_CONTRACT §3), so each gains an
immutable UUID4 of its own, named after ``pharmacy_drug_catalog.drug_id`` and
the platform's other public identifiers. The business codes those entities
already carry — ``batch_number``, ``prescription_number``, ``queue_number``,
``transfer_number`` — stay mutable business data and are never keys (§4).

**P0-2-SUBBLOCKER-A Group B.** The three references M3 could not resolve:

* ``pharmacy_sale_lines.batch_id`` → ``pharmacy_drug_batches.id``
* ``pharmacy_sale_lines.prescription_id`` → ``pharmacy_prescriptions.id``
* ``pharmacy_drug_substitution_requests.prescription_id`` → ``pharmacy_prescriptions.id``

Their targets were always integer-keyed; what was missing was a canonical
``DrugBatch`` and ``Prescription`` in the application to point at. M4 supplies
those, so the columns become ``INTEGER`` and finally carry the foreign keys
PostgreSQL could not create while they were ``VARCHAR(26)``.

Fail-closed, exactly as the M3 revision. A ``VARCHAR(26)`` ULID has no
deterministic integer meaning, so no identifier data is ever cast: the
migration refuses to run in either direction unless the tables whose columns it
retypes are empty, and reports the per-table counts instead. Adding a public
identity is not destructive and is not gated — it backfills through
``gen_random_uuid()`` and is safe on populated tables.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql

revision: str = "20260911_0001"
down_revision: str | None = "20260910_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SALE_LINES = "pharmacy_sale_lines"
_REQUESTS = "pharmacy_drug_substitution_requests"

# table -> public UUID column
_PUBLIC_IDS: dict[str, str] = {
    "pharmacy_drug_batches": "batch_id",
    "pharmacy_prescriptions": "prescription_id",
    "pharmacy_prescription_items": "prescription_item_id",
    "pharmacy_dispense_queue": "queue_id",
    "pharmacy_inventory_transfers": "transfer_id",
}

# P0-2-SUBBLOCKER-A Group B.
# (table, column, referred table, ondelete, nullable)
_GROUP_B: tuple[tuple[str, str, str, str, bool], ...] = (
    (_SALE_LINES, "batch_id", "pharmacy_drug_batches", "RESTRICT", False),
    (_SALE_LINES, "prescription_id", "pharmacy_prescriptions", "SET NULL", True),
    (_REQUESTS, "prescription_id", "pharmacy_prescriptions", "SET NULL", True),
)

_FK_NAMES: dict[tuple[str, str], str] = {
    (_SALE_LINES, "batch_id"): "fk_pharmacy_sale_lines_batch",
    (_SALE_LINES, "prescription_id"): "fk_pharmacy_sale_lines_prescription",
    (_REQUESTS, "prescription_id"): "fk_pharmacy_substitution_request_prescription",
}

# Only the tables whose identifier columns are retyped need the emptiness
# precondition. The referenced tables are not rewritten by this revision.
_RETYPED_TABLES = (_SALE_LINES, _REQUESTS)


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
    return all(_table_exists(t) for t in (*_PUBLIC_IDS, *_RETYPED_TABLES))


def _require_empty(direction: str) -> None:
    """Refuse to retype identifier columns unless the owning tables are empty."""
    bind = op.get_bind()
    populated = {}
    for table in _RETYPED_TABLES:
        count = bind.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
        if count:
            populated[table] = count
    if populated:
        detail = ", ".join(f"{t}={n}" for t, n in sorted(populated.items()))
        raise RuntimeError(
            f"P0-2 M4 {direction} preflight failed: converting the Group B batch and "
            f"prescription references requires {' and '.join(_RETYPED_TABLES)} to be empty, "
            f"but found rows ({detail}). No schema or data was changed. A VARCHAR(26) ULID "
            f"has no deterministic integer meaning, so these rows must be exported and "
            f"re-created deliberately, never cast."
        )


def _add_public_identity(table: str, column: str) -> None:
    index = f"ix_{table}_{column}"
    unique = f"uq_{table}_{column}"
    if not _has_column(table, column):
        op.add_column(table, sa.Column(column, postgresql.UUID(as_uuid=True), nullable=True))
    # Backfill only rows without an identity, so a re-run never regenerates one
    # that has already been published.
    op.execute(f"UPDATE {table} SET {column} = gen_random_uuid() WHERE {column} IS NULL")
    remaining = op.get_bind().execute(
        text(f"SELECT count(*) FROM {table} WHERE {column} IS NULL")
    ).scalar_one()
    if remaining:
        raise RuntimeError(
            f"P0-2 M4 preflight failed: {remaining} row(s) in {table} still have a NULL "
            f"{column} after backfill. Aborting before applying NOT NULL; nothing was changed."
        )
    op.alter_column(table, column, existing_type=postgresql.UUID(as_uuid=True), nullable=False)
    if not _unique_exists(table, unique):
        op.create_unique_constraint(unique, table, [column])
    if not _index_exists(table, index):
        op.create_index(index, table, [column])


def _drop_public_identity(table: str, column: str) -> None:
    index = f"ix_{table}_{column}"
    unique = f"uq_{table}_{column}"
    if _index_exists(table, index):
        op.drop_index(index, table_name=table)
    if _unique_exists(table, unique):
        op.drop_constraint(unique, table, type_="unique")
    if _has_column(table, column):
        op.drop_column(table, column)


def upgrade() -> None:
    if not _installed() or not _pg():
        return

    _require_empty("upgrade")

    # 1. Group B: retype, then constrain.
    for table, column, referred, ondelete, nullable in _GROUP_B:
        if not _column_type(table, column).upper().startswith("INTEGER"):
            op.alter_column(
                table,
                column,
                existing_type=sa.String(26),
                type_=sa.Integer(),
                existing_nullable=nullable,
                postgresql_using=f"{column}::integer",
            )
        name = _FK_NAMES[(table, column)]
        if not _fk_exists(table, name):
            op.create_foreign_key(name, table, referred, [column], ["id"], ondelete=ondelete)

    # 2. Public identities. Deliberately after the Group B work: a failure here
    #    should not leave a half-converted foreign key behind.
    for table, column in _PUBLIC_IDS.items():
        _add_public_identity(table, column)


def downgrade() -> None:
    if not _installed() or not _pg():
        return

    _require_empty("downgrade")

    for table, column in _PUBLIC_IDS.items():
        _drop_public_identity(table, column)

    for table, column, _referred, _ondelete, nullable in _GROUP_B:
        name = _FK_NAMES[(table, column)]
        if _fk_exists(table, name):
            op.drop_constraint(name, table, type_="foreignkey")
        if _column_type(table, column).upper().startswith("INTEGER"):
            op.alter_column(
                table,
                column,
                existing_type=sa.Integer(),
                type_=sa.String(26),
                existing_nullable=nullable,
                postgresql_using=f"{column}::varchar(26)",
            )
