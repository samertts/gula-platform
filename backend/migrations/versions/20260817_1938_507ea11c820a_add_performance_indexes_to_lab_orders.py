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


def upgrade() -> None:
    # Composite index for the main dashboard query: (lab_id, status, created_at)
    op.create_index(
        "ix_lab_orders_lab_status_created",
        "lab_orders",
        ["lab_id", "status", "created_at"],
        unique=False,
    )
    # Index for filtering orders by doctor and status
    op.create_index(
        "ix_lab_orders_doctor_status",
        "lab_orders",
        ["doctor_user_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_lab_orders_lab_status_created", table_name="lab_orders")
    op.drop_index("ix_lab_orders_doctor_status", table_name="lab_orders")
