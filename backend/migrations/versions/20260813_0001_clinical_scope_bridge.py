"""Add a reviewed, explicit legacy laboratory to facility scope bridge.

Revision ID: 20260813_0001
Revises: 20260812_0003
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260813_0001"
down_revision = "20260812_0003"
branch_labels = None
depends_on = None


_TABLE = "clinical_lab_facility_bindings"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _TABLE in inspector.get_table_names():
        return

    op.create_table(
        _TABLE,
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column(
            "legacy_lab_id",
            sa.Integer(),
            sa.ForeignKey("labs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "facility_resource_id",
            sa.Integer(),
            sa.ForeignKey("facilities.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("mapping_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("legacy_lab_id", "facility_resource_id", name="uq_clinical_lab_facility_binding"),
    )
    op.create_index("ix_clinical_lab_facility_bindings_legacy_lab_id", _TABLE, ["legacy_lab_id"])
    op.create_index("ix_clinical_lab_facility_bindings_facility_resource_id", _TABLE, ["facility_resource_id"])
    op.create_index("ix_clinical_lab_facility_bindings_status", _TABLE, ["status"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _TABLE not in inspector.get_table_names():
        return
    op.drop_index("ix_clinical_lab_facility_bindings_status", table_name=_TABLE)
    op.drop_index("ix_clinical_lab_facility_bindings_facility_resource_id", table_name=_TABLE)
    op.drop_index("ix_clinical_lab_facility_bindings_legacy_lab_id", table_name=_TABLE)
    op.drop_table(_TABLE)

