"""Add trusted device identities and quarantined ingress inbox.

Revision ID: 20260823_0006
Revises: 20260820_0005
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260823_0006"
down_revision = "20260820_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trusted_device_identities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("device_uid", sa.String(length=96), nullable=False),
        sa.Column("integrated_device_id", sa.Integer(), nullable=True),
        sa.Column("gateway_id", sa.Integer(), nullable=True),
        sa.Column("certificate_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("hmac_secret_ref", sa.String(length=255), nullable=True),
        sa.Column("protocol", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("safe_metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'active', 'suspended', 'revoked', 'retired')",
            name="ck_trusted_device_identity_status",
        ),
        sa.ForeignKeyConstraint(["approved_by"], ["lab_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["gateway_id"], ["device_gateways.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["integrated_device_id"], ["integrated_devices.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lab_id", "device_uid", name="uq_trusted_device_identity_lab_uid"),
        sa.UniqueConstraint("certificate_fingerprint", name="uq_trusted_device_identity_cert"),
    )
    op.create_index(
        "ix_trusted_device_identity_lab_status",
        "trusted_device_identities",
        ["lab_id", "status"],
    )

    op.create_table(
        "device_inbox_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("device_identity_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.String(length=160), nullable=False),
        sa.Column("nonce_digest", sa.String(length=64), nullable=False),
        sa.Column("payload_digest", sa.String(length=64), nullable=False),
        sa.Column("protocol", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="quarantined"),
        sa.Column("correlation_id", sa.String(length=96), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("safe_metadata", sa.JSON(), nullable=True),
        sa.CheckConstraint(
            "status IN ('received', 'duplicate', 'quarantined', 'rejected')",
            name="ck_device_inbox_status",
        ),
        sa.ForeignKeyConstraint(
            ["device_identity_id"], ["trusted_device_identities.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "lab_id",
            "device_identity_id",
            "message_id",
            name="uq_device_inbox_lab_device_message",
        ),
        sa.UniqueConstraint(
            "device_identity_id",
            "nonce_digest",
            name="uq_device_inbox_device_nonce",
        ),
    )
    op.create_index(
        "ix_device_inbox_lab_status_received",
        "device_inbox_messages",
        ["lab_id", "status", "received_at"],
    )
    op.create_index(
        "ix_device_inbox_device_occurred",
        "device_inbox_messages",
        ["device_identity_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_device_inbox_device_occurred", table_name="device_inbox_messages")
    op.drop_index("ix_device_inbox_lab_status_received", table_name="device_inbox_messages")
    op.drop_table("device_inbox_messages")
    op.drop_index("ix_trusted_device_identity_lab_status", table_name="trusted_device_identities")
    op.drop_table("trusted_device_identities")
