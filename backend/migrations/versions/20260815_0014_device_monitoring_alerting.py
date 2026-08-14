"""Add device gateway monitoring metrics and alert state.

Revision ID: 20260815_0014
Revises: 20260815_0013
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260815_0014"
down_revision = "20260815_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "device_gateway_metric_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("gateway_ref", sa.String(length=160), nullable=False),
        sa.Column("gateway_status", sa.String(length=24), nullable=False, server_default="healthy"),
        sa.Column("gateway_version", sa.String(length=48), nullable=True),
        sa.Column("outbox_pending_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("outbox_oldest_age_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("outbox_retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("outbox_dead_letter_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("disk_used_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("disk_free_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("worker_last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("worker_lag_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("transport_latency_ms", sa.Float(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("simulation_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("safe_metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_device_gateway_metrics_lab_captured", "device_gateway_metric_snapshots", ["lab_id", "captured_at"])
    op.create_index("ix_device_gateway_metrics_gateway_captured", "device_gateway_metric_snapshots", ["gateway_ref", "captured_at"])
    op.create_index("ix_device_gateway_metrics_outbox_age", "device_gateway_metric_snapshots", ["lab_id", "outbox_oldest_age_seconds"])

    op.create_table(
        "device_gateway_alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("gateway_ref", sa.String(length=160), nullable=False),
        sa.Column("alert_key", sa.String(length=96), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default="warning"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="open"),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("metric_key", sa.String(length=80), nullable=False),
        sa.Column("current_value", sa.Float(), nullable=True),
        sa.Column("threshold_value", sa.Float(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by", sa.Integer(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("correlation_id", sa.String(length=96), nullable=False),
        sa.Column("simulation_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("safe_metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["acknowledged_by"], ["lab_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_device_gateway_alerts_lab_status", "device_gateway_alerts", ["lab_id", "status", "last_seen_at"])
    op.create_index("ix_device_gateway_alerts_gateway", "device_gateway_alerts", ["gateway_ref", "last_seen_at"])
    op.create_index("ix_device_gateway_alerts_severity", "device_gateway_alerts", ["lab_id", "severity", "status"])
    op.create_index(op.f("ix_device_gateway_alerts_correlation_id"), "device_gateway_alerts", ["correlation_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_device_gateway_alerts_correlation_id"), table_name="device_gateway_alerts")
    op.drop_index("ix_device_gateway_alerts_severity", table_name="device_gateway_alerts")
    op.drop_index("ix_device_gateway_alerts_gateway", table_name="device_gateway_alerts")
    op.drop_index("ix_device_gateway_alerts_lab_status", table_name="device_gateway_alerts")
    op.drop_table("device_gateway_alerts")
    op.drop_index("ix_device_gateway_metrics_outbox_age", table_name="device_gateway_metric_snapshots")
    op.drop_index("ix_device_gateway_metrics_gateway_captured", table_name="device_gateway_metric_snapshots")
    op.drop_index("ix_device_gateway_metrics_lab_captured", table_name="device_gateway_metric_snapshots")
    op.drop_table("device_gateway_metric_snapshots")
