"""Add secret-free adapter registry and protocol profiles.

Revision ID: 20260815_0012
Revises: 20260814_0011
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260815_0012"
down_revision = "20260814_0011"
branch_labels = None
depends_on = None


_PROTOCOLS = "'HL7v2_MLLP', 'ASTM', 'DICOM', 'FHIR_Device', 'TCP_IP', 'USB_Serial', 'Bluetooth', 'WiFi', 'IPP', 'ZPL', 'IPL', 'PDF', 'None'"
_TRANSPORTS = "'MLLP', 'TCP', 'Serial', 'USB', 'Bluetooth', 'WiFi', 'HTTP', 'File', 'None'"


def upgrade() -> None:
    op.create_table(
        "device_connectors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("connector_uid", sa.String(length=96), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("integrated_devices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("protocol", sa.String(length=32), nullable=False),
        sa.Column("transport", sa.String(length=24), nullable=False),
        sa.Column("mode", sa.String(length=24), nullable=False, server_default="simulated"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("contract_version", sa.String(length=24), nullable=False, server_default="v1"),
        sa.Column("gateway_ref", sa.String(length=160), nullable=True),
        sa.Column("config_safe", sa.JSON(), nullable=True),
        sa.Column("capability_manifest", sa.JSON(), nullable=True),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("simulation_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("maintenance_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("lab_id", "connector_uid", name="uq_device_connectors_lab_uid"),
        sa.CheckConstraint(f"protocol IN ({_PROTOCOLS})", name="ck_device_connectors_protocol"),
        sa.CheckConstraint(f"transport IN ({_TRANSPORTS})", name="ck_device_connectors_transport"),
        sa.CheckConstraint(
            "mode IN ('simulated', 'gateway_pending', 'active', 'disabled')",
            name="ck_device_connectors_mode",
        ),
        sa.CheckConstraint(
            "status IN ('healthy', 'degraded', 'offline', 'error', 'maintenance', 'pending')",
            name="ck_device_connectors_status",
        ),
    )
    op.create_index("ix_device_connectors_lab_status", "device_connectors", ["lab_id", "status"])
    op.create_index("ix_device_connectors_lab_protocol", "device_connectors", ["lab_id", "protocol"])
    op.create_index("ix_device_connectors_heartbeat", "device_connectors", ["last_heartbeat_at"])

    op.create_table(
        "device_protocol_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_key", sa.String(length=120), nullable=False),
        sa.Column("protocol", sa.String(length=32), nullable=False),
        sa.Column("version", sa.String(length=24), nullable=False, server_default="v1"),
        sa.Column("message_type", sa.String(length=64), nullable=True),
        sa.Column("framing", sa.String(length=120), nullable=True),
        sa.Column("ack_strategy", sa.String(length=80), nullable=True),
        sa.Column("encoding", sa.String(length=40), nullable=True, server_default="UTF-8"),
        sa.Column("mapping_schema", sa.JSON(), nullable=True),
        sa.Column("validation_rules", sa.JSON(), nullable=True),
        sa.Column("simulator_key", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="draft"),
        sa.Column("simulation_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("lab_id", "profile_key", name="uq_device_protocol_profiles_lab_key"),
        sa.CheckConstraint(f"protocol IN ({_PROTOCOLS})", name="ck_device_protocol_profiles_protocol"),
        sa.CheckConstraint(
            "status IN ('draft', 'validated', 'retired')",
            name="ck_device_protocol_profiles_status",
        ),
    )
    op.create_index("ix_device_protocol_profiles_lab_protocol", "device_protocol_profiles", ["lab_id", "protocol"])
    op.create_index("ix_device_protocol_profiles_lab_status", "device_protocol_profiles", ["lab_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_device_protocol_profiles_lab_status", table_name="device_protocol_profiles")
    op.drop_index("ix_device_protocol_profiles_lab_protocol", table_name="device_protocol_profiles")
    op.drop_table("device_protocol_profiles")

    op.drop_index("ix_device_connectors_heartbeat", table_name="device_connectors")
    op.drop_index("ix_device_connectors_lab_protocol", table_name="device_connectors")
    op.drop_index("ix_device_connectors_lab_status", table_name="device_connectors")
    op.drop_table("device_connectors")
