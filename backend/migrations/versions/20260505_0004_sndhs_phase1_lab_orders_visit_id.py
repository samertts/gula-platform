"""SNDHS-lite Phase 1 — Step D: add ``lab_orders.visit_id`` (NULLable, no FK).

Adds a UUID column linking every lab order to a visit. The FK and the
backfill happen in later steps so this migration cannot block writes.

Why no FK yet
-------------
- Adding a NOT VALID FK still requires an ACCESS EXCLUSIVE lock long
  enough to add the constraint metadata; under heavy traffic that may
  be unsafe even though it's brief.
- We want to add the FK only after the backfill completes — that way
  the FK can be added with ``NOT VALID`` and then ``VALIDATE`` without
  any window of inconsistency.

This step is purely metadata and safe at any time.

Revision ID : 20260505_0004
Revises     : 20260505_0003
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql


revision = "20260505_0004"
down_revision = "20260505_0003"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    return any(c["name"] == column for c in inspect(op.get_bind()).get_columns(table))


def _pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _index_exists(name: str) -> bool:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return name in {ix["name"] for ix in inspect(bind).get_indexes("lab_orders")}
    row = bind.execute(
        text("SELECT 1 FROM pg_indexes WHERE schemaname = current_schema() AND indexname = :n"),
        {"n": name},
    ).first()
    return row is not None


def upgrade() -> None:
    if not _has_column("lab_orders", "visit_id"):
        op.add_column(
            "lab_orders",
            sa.Column(
                "visit_id",
                postgresql.UUID(as_uuid=True) if _pg() else sa.String(36),
                nullable=True,
            ),
        )

    if _pg():
        if not _index_exists("ix_lab_orders_visit_id"):
            with op.get_context().autocommit_block():
                op.execute(
                    text(
                        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_lab_orders_visit_id "
                        "ON lab_orders (visit_id)"
                    )
                )
    else:
        if not _index_exists("ix_lab_orders_visit_id"):
            op.create_index("ix_lab_orders_visit_id", "lab_orders", ["visit_id"])


def downgrade() -> None:
    if _pg():
        if _index_exists("ix_lab_orders_visit_id"):
            with op.get_context().autocommit_block():
                op.execute(text("DROP INDEX CONCURRENTLY IF EXISTS ix_lab_orders_visit_id"))
    else:
        if _index_exists("ix_lab_orders_visit_id"):
            op.drop_index("ix_lab_orders_visit_id", table_name="lab_orders")

    if _has_column("lab_orders", "visit_id"):
        op.drop_column("lab_orders", "visit_id")
