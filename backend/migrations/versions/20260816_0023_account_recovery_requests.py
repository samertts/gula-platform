"""Add server-owned account recovery lifecycle records.

Revision ID: 20260816_0023
Revises: 20260815_0022
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
revision: str = "20260816_0023"
down_revision: str | None = "20260815_0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "account_recovery_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("request_id", sa.String(length=36), nullable=False),
        sa.Column("correlation_id", sa.String(length=36), nullable=False),
        sa.Column("account_kind", sa.String(length=16), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=True),
        sa.Column("operation", sa.String(length=40), nullable=False),
        sa.Column("state", sa.String(length=24), nullable=False, server_default="requested"),
        sa.Column("assurance_level", sa.String(length=16), nullable=False, server_default="medium"),
        sa.Column("risk_code", sa.String(length=64), nullable=False, server_default="standard_recovery"),
        sa.Column("reason_code", sa.String(length=64), nullable=True),
        sa.Column("token_digest", sa.String(length=64), nullable=True),
        sa.Column("idempotency_key_digest", sa.String(length=64), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recovered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("requested_ip", sa.String(length=45), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id", name="uq_account_recovery_request_id"),
        sa.UniqueConstraint("token_digest", name="uq_account_recovery_token_digest"),
        sa.UniqueConstraint("idempotency_key_digest", name="uq_account_recovery_idempotency_digest"),
    )
    op.create_index(
        "ix_account_recovery_account_state",
        "account_recovery_requests",
        ["account_kind", "account_id", "operation", "state"],
    )
    op.create_index(
        "ix_account_recovery_correlation",
        "account_recovery_requests",
        ["correlation_id", "created_at"],
    )
    op.create_index(
        "ix_account_recovery_expiry_state",
        "account_recovery_requests",
        ["state", "token_expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_account_recovery_expiry_state", table_name="account_recovery_requests")
    op.drop_index("ix_account_recovery_correlation", table_name="account_recovery_requests")
    op.drop_index("ix_account_recovery_account_state", table_name="account_recovery_requests")
    op.drop_table("account_recovery_requests")
