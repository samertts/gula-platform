"""Create durable clinical document authority.

Revision ID: 20260818_0001
Revises: 20260816_0023
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260818_0001"
down_revision: str | None = "20260816_0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clinical_documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=80), nullable=False),
        sa.Column("encounter_id", sa.String(length=80), nullable=True),
        sa.Column("author_practitioner_id", sa.String(length=80), nullable=False),
        sa.Column("author_account_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("facility_id", sa.String(length=80), nullable=False),
        sa.Column("department_id", sa.String(length=80), nullable=True),
        sa.Column("workspace_id", sa.String(length=80), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("legacy_lab_id", sa.Integer(), nullable=True),
        sa.Column("document_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="DRAFT"),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("content_format", sa.String(length=20), nullable=False, server_default="structured"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signed_by", sa.String(length=80), nullable=True),
        sa.Column("signature_reference", sa.String(length=128), nullable=True),
        sa.Column("amendment_of", sa.String(length=36), nullable=True),
        sa.Column("amendment_reason", sa.String(length=500), nullable=True),
        sa.Column("correlation_id", sa.String(length=36), nullable=False),
        sa.Column("is_signed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'IN_REVIEW', 'SIGNED', 'AMENDED', 'VOIDED', 'CANCELLED')",
            name="ck_clinical_documents_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for name, columns in (
        ("ix_clinical_documents_patient", ["patient_id"]),
        ("ix_clinical_documents_encounter", ["encounter_id"]),
        ("ix_clinical_documents_author", ["author_practitioner_id"]),
        ("ix_clinical_documents_account", ["author_account_id"]),
        ("ix_clinical_documents_organization", ["organization_id"]),
        ("ix_clinical_documents_facility", ["facility_id"]),
        ("ix_clinical_documents_department", ["department_id"]),
        ("ix_clinical_documents_workspace", ["workspace_id"]),
        ("ix_clinical_documents_tenant", ["tenant_id"]),
        ("ix_clinical_documents_lab", ["legacy_lab_id"]),
        ("ix_clinical_documents_type", ["document_type"]),
        ("ix_clinical_documents_status", ["status", "is_signed", "is_deleted"]),
        ("ix_clinical_documents_amendment", ["amendment_of"]),
        ("ix_clinical_documents_correlation", ["correlation_id"]),
    ):
        op.create_index(name, "clinical_documents", columns)
    op.create_index(
        "ix_clinical_documents_scope_patient",
        "clinical_documents",
        ["tenant_id", "organization_id", "facility_id", "workspace_id", "patient_id"],
    )
    op.create_index(
        "ix_clinical_documents_encounter_version",
        "clinical_documents",
        ["encounter_id", "version"],
    )


def downgrade() -> None:
    op.drop_index("ix_clinical_documents_encounter_version", table_name="clinical_documents")
    op.drop_index("ix_clinical_documents_scope_patient", table_name="clinical_documents")
    for name in (
        "ix_clinical_documents_correlation",
        "ix_clinical_documents_amendment",
        "ix_clinical_documents_status",
        "ix_clinical_documents_type",
        "ix_clinical_documents_lab",
        "ix_clinical_documents_tenant",
        "ix_clinical_documents_workspace",
        "ix_clinical_documents_department",
        "ix_clinical_documents_facility",
        "ix_clinical_documents_organization",
        "ix_clinical_documents_account",
        "ix_clinical_documents_author",
        "ix_clinical_documents_encounter",
        "ix_clinical_documents_patient",
    ):
        op.drop_index(name, table_name="clinical_documents")
    op.drop_table("clinical_documents")
