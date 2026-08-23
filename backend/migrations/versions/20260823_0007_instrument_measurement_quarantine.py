"""Add quarantined instrument measurements.

Revision ID: 20260823_0007
Revises: 20260823_0006
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260823_0007"
down_revision = "20260823_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "instrument_measurements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("device_inbox_message_id", sa.Integer(), nullable=False),
        sa.Column("sample_id", sa.Integer(), nullable=False),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("test_code", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("value_text", sa.String(length=200), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="quarantined"),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_code", sa.String(length=64), nullable=True),
        sa.Column("safe_metadata", sa.JSON(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint(
            "status IN ('quarantined', 'pending_review', 'rejected', 'accepted')",
            name="ck_instrument_measurement_status",
        ),
        sa.CheckConstraint("sequence_index >= 0", name="ck_instrument_measurement_sequence"),
        sa.CheckConstraint(
            "(value IS NOT NULL AND value_text IS NULL) OR (value IS NULL AND value_text IS NOT NULL)",
            name="ck_instrument_measurement_single_value",
        ),
        sa.ForeignKeyConstraint(
            ["device_inbox_message_id"], ["device_inbox_messages.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["lab_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sample_id"], ["samples.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "device_inbox_message_id",
            "sequence_index",
            name="uq_instrument_measurement_inbox_sequence",
        ),
    )
    op.create_index(
        "ix_instrument_measurement_lab_status",
        "instrument_measurements",
        ["lab_id", "status", "received_at"],
    )
    op.create_index(
        "ix_instrument_measurement_sample",
        "instrument_measurements",
        ["sample_id", "received_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_instrument_measurement_sample", table_name="instrument_measurements")
    op.drop_index("ix_instrument_measurement_lab_status", table_name="instrument_measurements")
    op.drop_table("instrument_measurements")
