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
    bind = op.get_bind()
    validated_by_exists = _has_column("lab_orders", "validated_by")
    if not validated_by_exists:
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("lab_orders", recreate="always") as batch_op:
                batch_op.add_column(sa.Column("validated_by", sa.Integer(), nullable=True))
                batch_op.create_foreign_key(
                    "fk_lab_orders_validated_by",
                    "lab_users",
                    ["validated_by"],
                    ["id"],
                    ondelete="SET NULL",
                )
        else:
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
        bind.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_lab_orders_status_pending ON lab_orders (lab_id, created_at DESC)"
        ))


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = ("validated_by", "validated_at", "locked_at")
    column_names = {column["name"] for column in inspector.get_columns("lab_orders")}
    index_names = {index["name"] for index in inspector.get_indexes("lab_orders")}
    if "ix_lab_orders_validated_by" in index_names:
        op.drop_index("ix_lab_orders_validated_by", table_name="lab_orders")

    if bind.dialect.name == "sqlite":
        foreign_keys = inspector.get_foreign_keys("lab_orders")
        if any(column in column_names for column in columns):
            with op.batch_alter_table("lab_orders", recreate="always") as batch_op:
                for foreign_key in foreign_keys:
                    constrained = foreign_key.get("constrained_columns") or ()
                    if "validated_by" in constrained and foreign_key.get("name"):
                        batch_op.drop_constraint(foreign_key["name"], type_="foreignkey")
                for column in columns:
                    if column in column_names:
                        batch_op.drop_column(column)
    else:
        for column in columns:
            if column in column_names:
                op.drop_column("lab_orders", column)
    op.execute("DROP INDEX IF EXISTS ix_lab_orders_status_pending")
