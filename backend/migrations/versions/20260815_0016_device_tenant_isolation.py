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


def _switch_unique_constraint(old_name: str, new_name: str, new_columns: list[str]) -> None:
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("integrated_devices", recreate="always") as batch_op:
            batch_op.drop_constraint(old_name, type_="unique")
            batch_op.create_unique_constraint(new_name, new_columns)
    else:
        op.drop_constraint(old_name, "integrated_devices", type_="unique")
        op.create_unique_constraint(new_name, "integrated_devices", new_columns)


def upgrade() -> None:
    _switch_unique_constraint(
        "uq_integrated_devices_uid",
        "uq_integrated_devices_lab_uid",
        ["lab_id", "device_uid"],
    )


def downgrade() -> None:
    _switch_unique_constraint(
        "uq_integrated_devices_lab_uid",
        "uq_integrated_devices_uid",
        ["device_uid"],
    )
