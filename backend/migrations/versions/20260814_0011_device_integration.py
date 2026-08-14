"""Device integration catalog, safe event log, and simulated print jobs.

Revision ID: 20260814_0011
Revises: 20260814_0010
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260814_0011"
down_revision = "20260814_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integrated_devices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_uid", sa.String(length=96), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=48), nullable=False, server_default="other"),
        sa.Column("vendor", sa.String(length=120), nullable=True),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("serial_number", sa.String(length=120), nullable=True),
        sa.Column("protocol", sa.String(length=32), nullable=False, server_default="None"),
        sa.Column("transport", sa.String(length=24), nullable=False, server_default="None"),
        sa.Column("endpoint", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("simulation_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("maintenance_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("capabilities", sa.JSON(), nullable=True),
        sa.Column("printer_profile", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("device_uid", name="uq_integrated_devices_uid"),
        sa.CheckConstraint(
            "status IN ('connected', 'disconnected', 'error', 'maintenance', 'pending')",
            name="ck_integrated_devices_status",
        ),
    )
    op.create_index("ix_integrated_devices_lab_status", "integrated_devices", ["lab_id", "status"])
    op.create_index("ix_integrated_devices_lab_category", "integrated_devices", ["lab_id", "category"])
    op.create_index("ix_integrated_devices_last_seen", "integrated_devices", ["last_seen_at"])

    op.create_table(
        "device_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("integrated_devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False, server_default="system"),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default="info"),
        sa.Column("message_type", sa.String(length=64), nullable=True),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("correlation_id", sa.String(length=96), nullable=True),
        sa.Column("safe_metadata", sa.JSON(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_device_events_lab_occurred", "device_events", ["lab_id", "occurred_at"])
    op.create_index("ix_device_events_device_occurred", "device_events", ["device_id", "occurred_at"])
    op.create_index("ix_device_events_severity", "device_events", ["lab_id", "severity", "occurred_at"])
    op.create_index("ix_device_events_correlation_id", "device_events", ["correlation_id"])

    op.create_table(
        "device_print_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("integrated_devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("printer_language", sa.String(length=16), nullable=False, server_default="PDF"),
        sa.Column("label_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="queued"),
        sa.Column("simulation_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("safe_metadata", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('queued', 'simulated_success', 'failed')",
            name="ck_device_print_jobs_status",
        ),
    )
    op.create_index("ix_device_print_jobs_lab_created", "device_print_jobs", ["lab_id", "created_at"])
    op.create_index("ix_device_print_jobs_device_status", "device_print_jobs", ["device_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_device_print_jobs_device_status", table_name="device_print_jobs")
    op.drop_index("ix_device_print_jobs_lab_created", table_name="device_print_jobs")
    op.drop_table("device_print_jobs")

    op.drop_index("ix_device_events_correlation_id", table_name="device_events")
    op.drop_index("ix_device_events_severity", table_name="device_events")
    op.drop_index("ix_device_events_device_occurred", table_name="device_events")
    op.drop_index("ix_device_events_lab_occurred", table_name="device_events")
    op.drop_table("device_events")

    op.drop_index("ix_integrated_devices_last_seen", table_name="integrated_devices")
    op.drop_index("ix_integrated_devices_lab_category", table_name="integrated_devices")
    op.drop_index("ix_integrated_devices_lab_status", table_name="integrated_devices")
    op.drop_table("integrated_devices")
