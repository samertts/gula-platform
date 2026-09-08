"""Add durable receipts for safety-critical clinical commands.

Revision ID: 20260908_0002
Revises: 20260901_0004

This migration originally declared revision id 20260819_0003, which was already
used by 20260819_0003_research_entities.  Alembic resolved that id to the research
migration, so this one was unreachable and never ran on any database.  It is
re-identified here and chained into the Blood Bank lineage ahead of the head
merge, so it applies to fresh and existing databases alike.  The schema operations are unchanged.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260908_0002"
down_revision = "20260901_0004"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def upgrade() -> None:
    if _has_table("clinical_command_receipts"):
        # An operator may have created the table by hand while this migration was
        # unreachable; adopt it rather than failing the upgrade.
        return
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
    if not _has_table("clinical_command_receipts"):
        return
    op.drop_index("ix_clinical_command_receipt_resource", table_name="clinical_command_receipts")
    op.drop_table("clinical_command_receipts")
