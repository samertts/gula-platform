"""Make the Pharmacy stock uniqueness constraint mean what it says.

P0-2-M4-GAP-STOCK-NULL-STORE.

``uq_pharmacy_stock`` has covered ``(lab_id, drug_id, batch_id, store_id)``
since the platform migration, and the intent is plain: one stock row per drug
batch per dispensing point per laboratory. SQL does not deliver that intent.
``batch_id`` and ``store_id`` are both nullable, and a unique constraint treats
every NULL as distinct, so the guarantee silently evaporated for exactly the
rows that need it most.

Those rows are not an edge case, they are the default. Receiving a batch opens
its stock row through ``PharmacyService.create_batch`` with **no location at
all** — neither store nor warehouse — because a dispensing point is assigned
later, if ever. Every freshly received batch therefore sat outside the
constraint.

The fix is the one PostgreSQL provides for precisely this: ``NULLS NOT
DISTINCT`` (PostgreSQL 15+; every deployment target in this repository is 16 or
17). It expresses the intent already written into the constraint, and it does
so without either of the alternatives:

* making ``store_id`` NOT NULL would break batch receipt, the primary inventory
  entry point, and is disproven by the write path above;
* a partial unique index would need one index per nullable combination and
  would leave the plain constraint still lying about what it guarantees.

Fail-closed. Tightening a uniqueness rule can only fail on data that already
violates it, so this counts the offending groups first and aborts with their
identities rather than letting PostgreSQL reject the index with a single opaque
row. Nothing is merged, deduplicated or deleted: which of two real stock rows
is the true one is a question for whoever owns the data, not for a migration.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect, text

revision: str = "20260912_0001"
down_revision: str | None = "20260911_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "pharmacy_stock_levels"
_CONSTRAINT = "uq_pharmacy_stock"
_COLUMNS = ("lab_id", "drug_id", "batch_id", "store_id")


def _pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _constraint_exists(table: str, name: str) -> bool:
    return any(c["name"] == name for c in inspect(op.get_bind()).get_unique_constraints(table))


def _server_supports_nulls_not_distinct() -> bool:
    # NULLS NOT DISTINCT landed in PostgreSQL 15.
    version = op.get_bind().execute(text("SHOW server_version_num")).scalar_one()
    return int(version) >= 150000


def _refuse_on_duplicates() -> None:
    """Abort, naming the duplicates, rather than let the constraint fail opaquely."""
    columns = ", ".join(_COLUMNS)
    duplicates = op.get_bind().execute(
        text(
            f"SELECT {columns}, count(*) AS n FROM {_TABLE} "
            f"WHERE NOT is_deleted GROUP BY {columns} HAVING count(*) > 1 LIMIT 20"
        )
    ).fetchall()
    if not duplicates:
        return
    detail = "; ".join(
        "(" + ", ".join(f"{c}={r._mapping[c]!r}" for c in _COLUMNS) + f") x{r._mapping['n']}"
        for r in duplicates
    )
    raise RuntimeError(
        f"P0-2-M4-GAP-STOCK-NULL-STORE preflight failed: {len(duplicates)} group(s) in {_TABLE} "
        f"already violate the intended uniqueness of ({columns}) once NULLs are compared as "
        f"equal: {detail}. No schema or data was changed. These rows must be reconciled "
        f"deliberately — deciding which of two real stock rows is authoritative is a data "
        f"question, not a migration's to answer."
    )


def upgrade() -> None:
    if not _table_exists(_TABLE) or not _pg():
        return
    if not _server_supports_nulls_not_distinct():
        raise RuntimeError(
            "P0-2-M4-GAP-STOCK-NULL-STORE requires PostgreSQL 15 or newer for "
            "UNIQUE NULLS NOT DISTINCT; this server is older."
        )

    _refuse_on_duplicates()

    if _constraint_exists(_TABLE, _CONSTRAINT):
        op.drop_constraint(_CONSTRAINT, _TABLE, type_="unique")
    op.execute(
        f"ALTER TABLE {_TABLE} ADD CONSTRAINT {_CONSTRAINT} "
        f"UNIQUE NULLS NOT DISTINCT ({', '.join(_COLUMNS)})"
    )


def downgrade() -> None:
    if not _table_exists(_TABLE) or not _pg():
        return
    # Back to the SQL default, where each NULL is its own value. This direction
    # only ever loosens the rule, so it cannot fail on data.
    if _constraint_exists(_TABLE, _CONSTRAINT):
        op.drop_constraint(_CONSTRAINT, _TABLE, type_="unique")
    op.create_unique_constraint(_CONSTRAINT, _TABLE, list(_COLUMNS))
