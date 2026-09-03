"""add_performance_indexes_to_lab_orders

Revision ID: 507ea11c820a
Revises: 20260815_0022
Create Date: 2026-08-17 19:38:53.541740
"""
from typing import Union
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


revision: str = "507ea11c820a"
down_revision: str | None = "20260815_0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _index_exists(conn, index_name: str) -> bool:
    inspector = Inspector.from_engine(conn)
    return any(index["name"] == index_name for table in inspector.get_table_names() for index in inspector.get_indexes(table))


def upgrade() -> None:
    # This name is also owned by 20260503_0001. Reuse it rather than issuing
    # a second CREATE INDEX with the same PostgreSQL relation name.
    conn = op.get_bind()
    if not _index_exists(conn, "ix_lab_orders_lab_status_created"):
        op.create_index(
            "ix_lab_orders_lab_status_created",
            "lab_orders",
            ["lab_id", "status", "created_at"],
            unique=False,
        )
    if not _index_exists(conn, "ix_lab_orders_doctor_status"):
        op.create_index(
            "ix_lab_orders_doctor_status",
            "lab_orders",
            ["doctor_user_id", "status"],
            unique=False,
        )


def downgrade() -> None:
    conn = op.get_bind()
    # The lab/status index is owned by 20260503_0001 and must survive this
    # revision's downgrade. Only remove the index introduced here.
    if _index_exists(conn, "ix_lab_orders_doctor_status"):
        op.drop_index("ix_lab_orders_doctor_status", table_name="lab_orders")
