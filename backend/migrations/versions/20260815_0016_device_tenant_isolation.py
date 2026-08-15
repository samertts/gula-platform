"""Scope integrated device identifiers to their laboratory tenant.

Revision ID: 20260815_0016
Revises: 20260815_0015
"""
from __future__ import annotations

from alembic import op

revision = "20260815_0016"
down_revision = "20260815_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_integrated_devices_uid",
        "integrated_devices",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_integrated_devices_lab_uid",
        "integrated_devices",
        ["lab_id", "device_uid"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_integrated_devices_lab_uid",
        "integrated_devices",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_integrated_devices_uid",
        "integrated_devices",
        ["device_uid"],
    )
