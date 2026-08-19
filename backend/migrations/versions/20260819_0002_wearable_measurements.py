"""Add tenant-scoped canonical wearable measurements.

Revision ID: 20260819_0002
Revises: 20260819_0001
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260819_0002"
down_revision = "20260819_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "wearable_measurements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("metric_code", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("quality_status", sa.String(length=24), nullable=False, server_default="unknown"),
        sa.Column("source_event_id", sa.String(length=160), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=True),
        sa.Column("simulation_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["device_id"], ["integrated_devices.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lab_id", "source", "source_event_id", name="uq_wearable_measurements_event"),
    )
    op.create_index(
        "ix_wearable_measurements_patient_metric_time",
        "wearable_measurements",
        ["lab_id", "patient_id", "metric_code", "measured_at"],
    )
    op.create_index(
        "ix_wearable_measurements_device_time",
        "wearable_measurements",
        ["lab_id", "device_id", "measured_at"],
    )
    op.create_index(
        "ix_wearable_measurements_lab_received",
        "wearable_measurements",
        ["lab_id", "received_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_wearable_measurements_lab_received", table_name="wearable_measurements")
    op.drop_index("ix_wearable_measurements_device_time", table_name="wearable_measurements")
    op.drop_index("ix_wearable_measurements_patient_metric_time", table_name="wearable_measurements")
    op.drop_table("wearable_measurements")
