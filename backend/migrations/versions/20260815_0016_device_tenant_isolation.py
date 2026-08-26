"""Scope integrated device identifiers to their laboratory tenant.

Revision ID: 20260815_0016
Revises: 20260815_0015
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260815_0016"
down_revision = "20260815_0015"
branch_labels = None
depends_on = None


def _constraint_names() -> set[str]:
    bind = op.get_bind()
    return {
        item["name"]
        for item in sa.inspect(bind).get_unique_constraints("integrated_devices")
        if item.get("name")
    }


def upgrade() -> None:
    bind = op.get_bind()
    constraints = _constraint_names()
    has_old = "uq_integrated_devices_uid" in constraints
    has_new = "uq_integrated_devices_lab_uid" in constraints
    if bind.dialect.name == "sqlite":
        if has_old or not has_new:
            with op.batch_alter_table("integrated_devices", recreate="always") as batch_op:
                if has_old:
                    batch_op.drop_constraint("uq_integrated_devices_uid", type_="unique")
                if not has_new:
                    batch_op.create_unique_constraint(
                        "uq_integrated_devices_lab_uid",
                        ["lab_id", "device_uid"],
                    )
    else:
        if has_old:
            op.drop_constraint("uq_integrated_devices_uid", "integrated_devices", type_="unique")
        if not has_new:
            op.create_unique_constraint(
                "uq_integrated_devices_lab_uid",
                "integrated_devices",
                ["lab_id", "device_uid"],
            )


def downgrade() -> None:
    bind = op.get_bind()
    constraints = _constraint_names()
    has_old = "uq_integrated_devices_uid" in constraints
    has_new = "uq_integrated_devices_lab_uid" in constraints
    if bind.dialect.name == "sqlite":
        if has_new or not has_old:
            with op.batch_alter_table("integrated_devices", recreate="always") as batch_op:
                if has_new:
                    batch_op.drop_constraint("uq_integrated_devices_lab_uid", type_="unique")
                if not has_old:
                    batch_op.create_unique_constraint("uq_integrated_devices_uid", ["device_uid"])
    else:
        if has_new:
            op.drop_constraint("uq_integrated_devices_lab_uid", "integrated_devices", type_="unique")
        if not has_old:
            op.create_unique_constraint("uq_integrated_devices_uid", "integrated_devices", ["device_uid"])
