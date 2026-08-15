"""Add tenant-scoped device gateway registry.

Revision ID: 20260815_0018
Revises: 20260815_0017
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260815_0018"
down_revision = "20260815_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "device_gateways",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("gateway_ref", sa.String(length=160), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("mode", sa.String(length=24), nullable=False, server_default="simulated"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("gateway_version", sa.String(length=48), nullable=True),
        sa.Column("contract_version", sa.String(length=24), nullable=False, server_default="v1"),
        sa.Column("capabilities_safe", sa.JSON(), nullable=True),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("simulation_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lab_id", "gateway_ref", name="uq_device_gateways_lab_ref"),
    )
    op.create_index("ix_device_gateways_lab_status", "device_gateways", ["lab_id", "status"])
    op.create_index("ix_device_gateways_heartbeat", "device_gateways", ["lab_id", "last_heartbeat_at"])


def downgrade() -> None:
    op.drop_index("ix_device_gateways_heartbeat", table_name="device_gateways")
    op.drop_index("ix_device_gateways_lab_status", table_name="device_gateways")
    op.drop_table("device_gateways")
