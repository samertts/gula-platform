"""Financial control plane for maker-checker approvals.

Revision ID: 20260814_0010
Revises: 20260814_0009
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260814_0010"
down_revision = "20260814_0009"
branch_labels = None
depends_on = None


_STATUS_CHECK = "status IN ('REQUESTED', 'APPROVED', 'REJECTED', 'APPLIED', 'EXPIRED')"


def upgrade() -> None:
    op.create_table(
        "pay_financial_control_requests",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("control_type", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=128), nullable=False),
        sa.Column("requested_action", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="REQUESTED"),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("reason", sa.String(length=1024), nullable=False),
        sa.Column("rejection_reason", sa.String(length=1024), nullable=True),
        sa.Column("requested_by", sa.Integer(), nullable=False),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("applied_by", sa.Integer(), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("evidence_hash", sa.String(length=128), nullable=True),
        sa.Column("safe_metadata", sa.JSON(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("institution_id", "idempotency_key", name="uq_pay_control_institution_idempotency"),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_pay_control_status"),
    )
    op.create_index(
        "ix_pay_control_institution_id",
        "pay_financial_control_requests",
        ["institution_id"],
    )
    op.create_index(
        "ix_pay_control_institution_status",
        "pay_financial_control_requests",
        ["institution_id", "status"],
    )
    op.create_index(
        "ix_pay_control_resource",
        "pay_financial_control_requests",
        ["resource_type", "resource_id"],
    )
    op.create_index(
        "ix_pay_control_requested_by",
        "pay_financial_control_requests",
        ["requested_by"],
    )
    op.create_index(
        "ix_pay_control_request_id",
        "pay_financial_control_requests",
        ["request_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_pay_control_request_id", table_name="pay_financial_control_requests")
    op.drop_index("ix_pay_control_requested_by", table_name="pay_financial_control_requests")
    op.drop_index("ix_pay_control_resource", table_name="pay_financial_control_requests")
    op.drop_index("ix_pay_control_institution_status", table_name="pay_financial_control_requests")
    op.drop_index("ix_pay_control_institution_id", table_name="pay_financial_control_requests")
    op.drop_table("pay_financial_control_requests")
