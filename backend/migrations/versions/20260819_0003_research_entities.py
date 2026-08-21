"""Add tenant-scoped clinical research entities.

Revision ID: 20260819_0003
Revises: 20260819_0002
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260819_0003"
down_revision = "20260819_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinical_research_registries",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("fhir_id", sa.String(length=64), nullable=True),
        sa.Column("fhir_resource_type", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("registry_type", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("condition", sa.String(length=256), nullable=True),
        sa.Column("inclusion_criteria", sa.Text(), nullable=True),
        sa.Column("steward", sa.String(length=256), nullable=True),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_research_registry_lab_type",
        "clinical_research_registries",
        ["lab_id", "registry_type"],
    )
    op.create_index(
        "ix_research_registry_lab_deleted",
        "clinical_research_registries",
        ["lab_id", "is_deleted"],
    )
    op.create_index(
        "ix_clinical_research_registries_lab_id",
        "clinical_research_registries",
        ["lab_id"],
    )

    op.create_table(
        "clinical_research_cohorts",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("fhir_id", sa.String(length=64), nullable=True),
        sa.Column("fhir_resource_type", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("inclusion_criteria", sa.Text(), nullable=True),
        sa.Column("registry_id", sa.String(length=26), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["registry_id"],
            ["clinical_research_registries.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_research_cohort_lab_active",
        "clinical_research_cohorts",
        ["lab_id", "is_active"],
    )
    op.create_index(
        "ix_research_cohort_lab_deleted",
        "clinical_research_cohorts",
        ["lab_id", "is_deleted"],
    )
    op.create_index(
        "ix_clinical_research_cohorts_lab_id",
        "clinical_research_cohorts",
        ["lab_id"],
    )
    op.create_index(
        "ix_clinical_research_cohorts_registry_id",
        "clinical_research_cohorts",
        ["registry_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_clinical_research_cohorts_registry_id",
        table_name="clinical_research_cohorts",
    )
    op.drop_index(
        "ix_clinical_research_cohorts_lab_id",
        table_name="clinical_research_cohorts",
    )
    op.drop_index(
        "ix_research_cohort_lab_deleted",
        table_name="clinical_research_cohorts",
    )
    op.drop_index(
        "ix_research_cohort_lab_active",
        table_name="clinical_research_cohorts",
    )
    op.drop_table("clinical_research_cohorts")

    op.drop_index(
        "ix_clinical_research_registries_lab_id",
        table_name="clinical_research_registries",
    )
    op.drop_index(
        "ix_research_registry_lab_deleted",
        table_name="clinical_research_registries",
    )
    op.drop_index(
        "ix_research_registry_lab_type",
        table_name="clinical_research_registries",
    )
    op.drop_table("clinical_research_registries")
