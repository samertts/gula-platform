"""Create the canonical clinical diagnostic report aggregate.

Revision ID: 20260822_0002
Revises: 20260822_0001
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260822_0002"
down_revision: str = "20260822_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "clinical_diagnostic_reports"


def _table_exists() -> bool:
    return _TABLE in {table.name for table in sa.inspect(op.get_bind()).get_table_names()}


def upgrade() -> None:
    if _table_exists():
        return
    op.create_table(
        _TABLE,
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.String(length=80), nullable=False),
        sa.Column("patient_id", sa.String(length=80), nullable=False),
        sa.Column("encounter_id", sa.String(length=80), nullable=True),
        sa.Column("report_code", sa.String(length=80), nullable=True),
        sa.Column("report_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="PRELIMINARY"),
        sa.Column("conclusion", sa.Text(), nullable=True),
        sa.Column("result_refs", sa.JSON(), nullable=False),
        sa.Column("source_metadata", sa.JSON(), nullable=True),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("facility_id", sa.String(length=80), nullable=False),
        sa.Column("department_id", sa.String(length=80), nullable=True),
        sa.Column("workspace_id", sa.String(length=80), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("legacy_lab_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_by", sa.String(length=80), nullable=True),
        sa.Column("amended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("amendment_reason", sa.String(length=1000), nullable=True),
        sa.Column("correlation_id", sa.String(length=36), nullable=True),
        sa.Column("created_by", sa.String(length=80), nullable=False),
        sa.Column("updated_by", sa.String(length=80), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("source_type", "source_id", name="uq_clinical_diag_report_source"),
    )
    for name, columns in {
        "ix_clinical_diag_report_source_type": ["source_type"],
        "ix_clinical_diag_report_source_id": ["source_id"],
        "ix_clinical_diag_report_patient": ["patient_id"],
        "ix_clinical_diag_report_scope": ["organization_id", "facility_id", "workspace_id"],
        "ix_clinical_diag_report_status": ["status"],
    }.items():
        op.create_index(name, _TABLE, columns, unique=False)


def downgrade() -> None:
    # Additive-only policy: no destructive downgrade in production.
    return None
