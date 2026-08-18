"""Add canonical identity verification records.

Revision ID: 20260814_0001
Revises: 20260813_0005
"""

from __future__ import annotations

from alembic import context, op
import sqlalchemy as sa


revision = "20260814_0001"
down_revision = "20260813_0005"
branch_labels = None
depends_on = None

_TABLE = "niam_verification_records"


def upgrade() -> None:
    if context.is_offline_mode():
        op.create_table(
            _TABLE,
            sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("account_id", sa.String(length=26), nullable=False),
            sa.Column("identity_id", sa.String(length=26), nullable=False),
            sa.Column("record_type", sa.String(length=30), nullable=False),
            sa.Column("method", sa.String(length=50), nullable=False),
            sa.Column("provider", sa.String(length=100), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="not_started"),
            sa.Column("assurance_level", sa.String(length=10), nullable=False, server_default="L0"),
            sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("provider_reference", sa.String(length=255), nullable=True),
            sa.Column("confidence", sa.Integer(), nullable=True),
            sa.Column("failure_reason_code", sa.String(length=100), nullable=True),
            sa.Column("verification_session_id", sa.String(length=64), nullable=True),
            sa.Column("verified_by", sa.String(length=100), nullable=True),
            sa.Column("professional_type", sa.String(length=60), nullable=True),
            sa.Column("professional_reference", sa.String(length=255), nullable=True),
            sa.Column("verified_attributes", sa.JSON(), nullable=True),
            sa.Column("attributes_purpose", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("uuid", name="uq_niam_verification_records_uuid"),
            sa.UniqueConstraint("verification_session_id", name="uq_niam_verification_records_session"),
        )
        for column in ("account_id", "identity_id", "record_type", "method", "provider", "status", "verification_session_id"):
            op.create_index(f"ix_niam_verification_records_{column}", _TABLE, [column])
        return
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _TABLE in inspector.get_table_names():
        return

    op.create_table(
        _TABLE,
        sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("account_id", sa.String(length=26), nullable=False),
        sa.Column("identity_id", sa.String(length=26), nullable=False),
        sa.Column("record_type", sa.String(length=30), nullable=False),
        sa.Column("method", sa.String(length=50), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="not_started"),
        sa.Column("assurance_level", sa.String(length=10), nullable=False, server_default="L0"),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider_reference", sa.String(length=255), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("failure_reason_code", sa.String(length=100), nullable=True),
        sa.Column("verification_session_id", sa.String(length=64), nullable=True),
        sa.Column("verified_by", sa.String(length=100), nullable=True),
        sa.Column("professional_type", sa.String(length=60), nullable=True),
        sa.Column("professional_reference", sa.String(length=255), nullable=True),
        sa.Column("verified_attributes", sa.JSON(), nullable=True),
        sa.Column("attributes_purpose", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["niam_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["identity_id"], ["niam_identities.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("uuid", name="uq_niam_verification_records_uuid"),
        sa.UniqueConstraint("verification_session_id", name="uq_niam_verification_records_session"),
    )
    for column in (
        "account_id",
        "identity_id",
        "record_type",
        "method",
        "provider",
        "status",
        "provider_reference",
        "professional_type",
    ):
        op.create_index(f"ix_niam_verification_records_{column}", _TABLE, [column])


def downgrade() -> None:
    if context.is_offline_mode():
        for column in ("verification_session_id", "status", "provider", "method", "record_type", "identity_id", "account_id"):
            op.drop_index(f"ix_niam_verification_records_{column}", table_name=_TABLE)
        op.drop_table(_TABLE)
        return
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _TABLE not in inspector.get_table_names():
        return
    for column in (
        "professional_type",
        "provider_reference",
        "status",
        "provider",
        "method",
        "record_type",
        "identity_id",
        "account_id",
    ):
        op.drop_index(f"ix_niam_verification_records_{column}", table_name=_TABLE)
    op.drop_table(_TABLE)
