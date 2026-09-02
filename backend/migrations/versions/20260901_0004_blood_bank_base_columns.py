"""Align Phase 2 Blood Bank tables with shared BaseEntity columns.

Revision ID: 20260901_0004
Revises: 20260901_0003
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = "20260901_0004"
down_revision = "20260901_0003"
branch_labels = None
depends_on = None


def _columns(table: str) -> set[str]:
    return {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    for table in ("blood_bank_patient_samples", "blood_bank_reservations", "blood_bank_reactions", "blood_bank_traceability_events", "blood_bank_returns", "blood_bank_discards"):
        if table not in tables:
            continue
        columns = _columns(table)
        if "fhir_id" not in columns:
            op.add_column(table, sa.Column("fhir_id", sa.String(64), nullable=True))
            op.create_index(f"ix_{table}_fhir_id", table, ["fhir_id"], if_not_exists=True)
        if "fhir_resource_type" not in columns:
            op.add_column(table, sa.Column("fhir_resource_type", sa.String(32), nullable=True))


def downgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    for table in ("blood_bank_discards", "blood_bank_returns", "blood_bank_traceability_events", "blood_bank_reactions", "blood_bank_reservations", "blood_bank_patient_samples"):
        if table not in tables:
            continue
        columns = _columns(table)
        if "fhir_resource_type" in columns:
            op.drop_column(table, "fhir_resource_type")
        if "fhir_id" in columns:
            op.drop_column(table, "fhir_id")
