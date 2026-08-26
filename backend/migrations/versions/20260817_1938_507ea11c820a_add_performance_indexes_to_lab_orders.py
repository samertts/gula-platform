"""add_performance_indexes_to_lab_orders

Revision ID: 507ea11c820a
Revises: 20260815_0022
Create Date: 2026-08-17 19:38:53.541740
"""
from typing import Union
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa


revision: str = "507ea11c820a"
down_revision: str | None = "20260815_0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _index_exists(index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return index_name in {item["name"] for item in inspector.get_indexes("lab_orders")}


def upgrade() -> None:
    # The dashboard index is created by 20260503_0001 with the same stable
    # name. Recreating it here caused fresh SQLite upgrades to fail and could
    # also create duplicate work on PostgreSQL. Keep that earlier index as the
    # canonical implementation and add only the index unique to this revision.
    if not _index_exists("ix_lab_orders_lab_status_created"):
        op.create_index(
            "ix_lab_orders_lab_status_created",
            "lab_orders",
            ["lab_id", "status", "created_at"],
            unique=False,
        )

    # Index for filtering orders by doctor and status.
    if not _index_exists("ix_lab_orders_doctor_status"):
        op.create_index(
            "ix_lab_orders_doctor_status",
            "lab_orders",
            ["doctor_user_id", "status"],
            unique=False,
        )


def downgrade() -> None:
    # The dashboard index belongs to the earlier 20260503_0001 revision and
    # must remain in place when this revision is downgraded.
    if _index_exists("ix_lab_orders_doctor_status"):
        op.drop_index("ix_lab_orders_doctor_status", table_name="lab_orders")
