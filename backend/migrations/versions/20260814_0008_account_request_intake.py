"""Add review-gated account request intake.

Revision ID: 20260814_0008
Revises: 20260814_0007
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260814_0008"
down_revision = "20260814_0007"
branch_labels = None
depends_on = None

_TABLE = "niam_account_creation_requests"


def upgrade() -> None:
    op.create_table(
        _TABLE,
        sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("request_uuid", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending_review"),
        sa.Column("requested_account_type", sa.String(length=20), nullable=False, server_default="human"),
        sa.Column("contact_email_encrypted", sa.String(length=1024), nullable=True),
        sa.Column("contact_email_lookup", sa.String(length=64), nullable=True),
        sa.Column("contact_phone_encrypted", sa.String(length=1024), nullable=True),
        sa.Column("contact_phone_lookup", sa.String(length=64), nullable=True),
        sa.Column("display_name_encrypted", sa.String(length=1024), nullable=True),
        sa.Column("idempotency_key_hash", sa.String(length=64), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("source_ip_hash", sa.String(length=64), nullable=True),
        sa.Column("reviewed_by_account_id", sa.String(length=26), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason_encrypted", sa.String(length=1024), nullable=True),
        sa.Column("account_id", sa.String(length=26), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["reviewed_by_account_id"], ["niam_accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["account_id"], ["niam_accounts.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("request_uuid", name="uq_niam_account_request_uuid"),
        sa.UniqueConstraint("idempotency_key_hash", name="uq_niam_account_request_idempotency"),
    )
    op.create_index("ix_niam_account_request_status", _TABLE, ["status"])
    op.create_index("ix_niam_account_request_email_lookup", _TABLE, ["contact_email_lookup"])
    op.create_index("ix_niam_account_request_phone_lookup", _TABLE, ["contact_phone_lookup"])
    op.create_index("ix_niam_account_request_source_ip_hash", _TABLE, ["source_ip_hash"])
    op.create_index("ix_niam_account_request_reviewed_by", _TABLE, ["reviewed_by_account_id"])
    op.create_index("ix_niam_account_request_account_id", _TABLE, ["account_id"])


def downgrade() -> None:
    op.drop_index("ix_niam_account_request_account_id", table_name=_TABLE)
    op.drop_index("ix_niam_account_request_reviewed_by", table_name=_TABLE)
    op.drop_index("ix_niam_account_request_source_ip_hash", table_name=_TABLE)
    op.drop_index("ix_niam_account_request_phone_lookup", table_name=_TABLE)
    op.drop_index("ix_niam_account_request_email_lookup", table_name=_TABLE)
    op.drop_index("ix_niam_account_request_status", table_name=_TABLE)
    op.drop_table(_TABLE)
