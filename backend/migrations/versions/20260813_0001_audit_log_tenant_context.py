"""Add tenant context to the tamper-evident audit log.

Revision ID: 20260813_0001
Revises: 20260812_0005
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260813_0001"
down_revision = "20260812_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("audit_logs") as batch_op:
        batch_op.add_column(sa.Column("lab_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_audit_logs_lab_id", ["lab_id"])


def downgrade() -> None:
    with op.batch_alter_table("audit_logs") as batch_op:
        batch_op.drop_index("ix_audit_logs_lab_id")
        batch_op.drop_column("lab_id")
