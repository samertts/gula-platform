"""Add durable receipts for safety-critical clinical commands.

Revision ID: 20260820_0006
Revises: 20260819_0004
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260820_0006"
down_revision = "20260819_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinical_command_receipts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("operation", sa.String(length=96), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="claimed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["lab_users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "lab_id", "actor_user_id", "operation", "idempotency_key",
            name="uq_clinical_command_actor_key",
        ),
    )
    op.create_index(
        "ix_clinical_command_receipt_resource",
        "clinical_command_receipts",
        ["lab_id", "resource_type", "resource_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_clinical_command_receipt_resource", table_name="clinical_command_receipts")
    op.drop_table("clinical_command_receipts")
