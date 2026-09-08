"""add_performance_indexes_to_lab_orders

Revision ID: 507ea11c820a
Revises: 20260815_0022
Create Date: 2026-08-17 19:38:53.541740
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '507ea11c820a'
down_revision: Union[str, None] = '20260815_0022'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _index_exists(name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(index["name"] == name for index in inspector.get_indexes("lab_orders"))


def upgrade() -> None:
    # ix_lab_orders_lab_status_created is also created, guarded, by the ancestor
    # revision 20260503_0001, so it already exists on any database that reaches
    # this point.  Guard both creates so the migration is idempotent, as the
    # repository migration policy requires.
    # Composite index for the main dashboard query: (lab_id, status, created_at)
    if not _index_exists("ix_lab_orders_lab_status_created"):
        op.create_index(
            "ix_lab_orders_lab_status_created",
            "lab_orders",
            ["lab_id", "status", "created_at"],
            unique=False,
        )
    # Index for filtering orders by doctor and status
    if not _index_exists("ix_lab_orders_doctor_status"):
        op.create_index(
            "ix_lab_orders_doctor_status",
            "lab_orders",
            ["doctor_user_id", "status"],
            unique=False,
        )


def downgrade() -> None:
    # Leave ix_lab_orders_lab_status_created in place: it is owned by the earlier
    # revision 20260503_0001, which drops it in its own downgrade.
    if _index_exists("ix_lab_orders_doctor_status"):
        op.drop_index("ix_lab_orders_doctor_status", table_name="lab_orders")
