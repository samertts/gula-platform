"""Create tenant-scoped FHIR resource registry.

Revision ID: 20260815_0019
Revises: 20260815_0018
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260815_0019"
down_revision = "20260815_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fhir_resource_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=128), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("profile", sa.String(length=255), nullable=True),
        sa.Column("subject_reference", sa.String(length=255), nullable=True),
        sa.Column("resource", sa.JSON(), nullable=False),
        sa.Column("source_system", sa.String(length=120), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["lab_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "lab_id",
            "resource_type",
            "resource_id",
            "version",
            name="uq_fhir_resource_lab_type_id_version",
        ),
    )
    op.create_index(
        "ix_fhir_resource_lab_type",
        "fhir_resource_records",
        ["lab_id", "resource_type"],
        unique=False,
    )
    op.create_index(
        "ix_fhir_resource_lab_subject",
        "fhir_resource_records",
        ["lab_id", "subject_reference"],
        unique=False,
    )
    op.create_index(
        "ix_fhir_resource_lab_created",
        "fhir_resource_records",
        ["lab_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_fhir_resource_lab_created", table_name="fhir_resource_records")
    op.drop_index("ix_fhir_resource_lab_subject", table_name="fhir_resource_records")
    op.drop_index("ix_fhir_resource_lab_type", table_name="fhir_resource_records")
    op.drop_table("fhir_resource_records")
