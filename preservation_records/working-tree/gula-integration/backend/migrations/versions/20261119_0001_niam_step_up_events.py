"""NIAM step-up authentication evidence (owner-approved 5-minute window)

Revision ID: 20261119_0001
Revises: 20261118_0001

Creates ``niam_step_up_events`` — server-side evidence of a completed MFA
event for an administrator's own NIAM account and session. No existing table
or column is altered and no data is modified.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261119_0001"
down_revision: str | None = "20261118_0001"


def _has_table(name: str) -> bool:
    conn = op.get_bind()
    return conn.dialect.has_table(conn, name)


def upgrade() -> None:
    if _has_table("niam_step_up_events"):
        return
    op.create_table(
        "niam_step_up_events",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("uuid", sa.String(36), nullable=False),
        sa.Column("event_id", sa.String(26), nullable=False),
        sa.Column("account_id", sa.String(26), nullable=False),
        sa.Column("session_id", sa.String(26), nullable=False),
        sa.Column("session_jti", sa.String(128), nullable=False),
        sa.Column("mfa_method", sa.String(30), nullable=False),
        sa.Column("code_fingerprint", sa.String(64), nullable=False),
        sa.Column("factor_fingerprint", sa.String(64), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.String(120), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["niam_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["niam_sessions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("uuid", name="uq_niam_step_up_events_uuid"),
        sa.UniqueConstraint("event_id", name="uq_niam_step_up_events_event_id"),
        # Database-level replay guard: an observed one-time code can never be
        # persisted twice for the same account, even under concurrent requests.
        sa.UniqueConstraint(
            "account_id", "code_fingerprint", name="uq_niam_step_up_account_code"
        ),
    )
    for column in ("uuid", "event_id", "account_id", "session_id", "session_jti", "code_fingerprint", "verified_at"):
        op.create_index(
            f"ix_niam_step_up_events_{column}",
            "niam_step_up_events",
            [column],
            unique=False,
        )


def downgrade() -> None:
    if not _has_table("niam_step_up_events"):
        return
    for column in ("uuid", "event_id", "account_id", "session_id", "session_jti", "code_fingerprint", "verified_at"):
        op.drop_index(f"ix_niam_step_up_events_{column}", table_name="niam_step_up_events")
    op.drop_table("niam_step_up_events")
