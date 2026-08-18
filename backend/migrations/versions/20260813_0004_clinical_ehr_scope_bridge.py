"""Add the reviewed national-EHR-facility to NIAM-facility bridge.

Revision ID: 20260813_0004
Revises: 20260813_0003
"""

from __future__ import annotations

from alembic import context, op
import sqlalchemy as sa


revision = "20260813_0004"
down_revision = "20260813_0003"
branch_labels = None
depends_on = None

_TABLE = "clinical_ehr_facility_bindings"
_NATIONAL_FACILITIES = "national_facilities"


def upgrade() -> None:
    if context.is_offline_mode():
        op.create_table(
            _NATIONAL_FACILITIES,
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("facility_code", sa.String(length=100), nullable=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("facility_code", name="uq_national_facilities_facility_code"),
        )
        op.create_table(
            _TABLE,
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("national_facility_id", sa.String(length=26), nullable=False),
            sa.Column("facility_resource_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("mapping_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("decision_reason", sa.Text(), nullable=True),
            sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("national_facility_id", "facility_resource_id", name="uq_clinical_ehr_facility_binding"),
        )
        op.create_index("ix_clinical_ehr_facility_bindings_national_facility_id", _TABLE, ["national_facility_id"])
        op.create_index("ix_clinical_ehr_facility_bindings_facility_resource_id", _TABLE, ["facility_resource_id"])
        op.create_index("ix_clinical_ehr_facility_bindings_status", _TABLE, ["status"])
        return
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # The binding is a clinical authorization boundary and therefore retains a
    # real foreign key to a canonical national-facility record. This reference
    # table was absent from the historic migration chain on a fresh database.
    if _NATIONAL_FACILITIES not in inspector.get_table_names():
        op.create_table(
            _NATIONAL_FACILITIES,
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("facility_code", sa.String(length=100), nullable=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("facility_code", name="uq_national_facilities_facility_code"),
        )

    if _TABLE in inspector.get_table_names():
        return
    op.create_table(
        _TABLE,
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column(
            "national_facility_id",
            sa.String(length=26),
            sa.ForeignKey("national_facilities.id", ondelete="RESTRICT"),
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
        sa.UniqueConstraint("national_facility_id", "facility_resource_id", name="uq_clinical_ehr_facility_binding"),
    )
    op.create_index("ix_clinical_ehr_facility_bindings_national_facility_id", _TABLE, ["national_facility_id"])
    op.create_index("ix_clinical_ehr_facility_bindings_facility_resource_id", _TABLE, ["facility_resource_id"])
    op.create_index("ix_clinical_ehr_facility_bindings_status", _TABLE, ["status"])


def downgrade() -> None:
    if context.is_offline_mode():
        op.drop_index("ix_clinical_ehr_facility_bindings_status", table_name=_TABLE)
        op.drop_index("ix_clinical_ehr_facility_bindings_facility_resource_id", table_name=_TABLE)
        op.drop_index("ix_clinical_ehr_facility_bindings_national_facility_id", table_name=_TABLE)
        op.drop_table(_TABLE)
        op.drop_table(_NATIONAL_FACILITIES)
        return
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _TABLE not in inspector.get_table_names():
        return
    op.drop_index("ix_clinical_ehr_facility_bindings_status", table_name=_TABLE)
    op.drop_index("ix_clinical_ehr_facility_bindings_facility_resource_id", table_name=_TABLE)
    op.drop_index("ix_clinical_ehr_facility_bindings_national_facility_id", table_name=_TABLE)
    op.drop_table(_TABLE)
