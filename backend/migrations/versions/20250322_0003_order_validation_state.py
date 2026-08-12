"""Order validation state machine columns.

Adds workflow columns to lab_orders:
  - validated_by   INT FK lab_users.id  — who validated/locked the order
  - validated_at   TIMESTAMPTZ          — when it was validated
  - locked_at      TIMESTAMPTZ          — when it was hard-locked (immutable)

After validation the order becomes immutable: results cannot be edited or deleted.
All adds are idempotent (_has_column check) so re-running is safe.

Revision ID: 20250322_0003
Revises    : 20250322_0002
Create Date: 2025-03-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "20250322_0003"
down_revision = "20250322_0002"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    return column in [c["name"] for c in inspect(bind).get_columns(table)]


def upgrade():
    if not _has_column("lab_orders", "validated_by"):
        op.add_column(
            "lab_orders",
            sa.Column("validated_by", sa.Integer, sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
        )
        op.create_index("ix_lab_orders_validated_by", "lab_orders", ["validated_by"])

    if not _has_column("lab_orders", "validated_at"):
        op.add_column(
            "lab_orders",
            sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _has_column("lab_orders", "locked_at"):
        op.add_column(
            "lab_orders",
            sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        )

    # Extend status check — existing "pending/completed/cancelled" plus new workflow states
    # PostgreSQL: add a partial index to speed up "pending" queries on the dashboard
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    if dialect_name == "postgresql":
        res = bind.execute(text(
            "SELECT 1 FROM pg_indexes WHERE tablename='lab_orders' AND indexname='ix_lab_orders_status_pending'"
        )).fetchone()
        if not res:
            bind.execute(text(
                "CREATE INDEX ix_lab_orders_status_pending ON lab_orders (lab_id, created_at DESC) WHERE status = 'pending'"
            ))
    else:
        try:
            bind.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_lab_orders_status_pending ON lab_orders (lab_id, created_at DESC)"
            ))
        except Exception:
            pass


def downgrade():
    op.drop_index("ix_lab_orders_validated_by", table_name="lab_orders")
    op.drop_column("lab_orders", "validated_by")
    op.drop_column("lab_orders", "validated_at")
    op.drop_column("lab_orders", "locked_at")
    op.execute("DROP INDEX IF EXISTS ix_lab_orders_status_pending")
