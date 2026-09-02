"""Align Blood Bank Phase 2 tables with the shared AuditMixin.

Revision ID: 20260901_0003
Revises: 20260901_0002
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = "20260901_0003"
down_revision = "20260901_0002"
branch_labels = None
depends_on = None


def _columns(table: str) -> set[str]:
    return {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    for table in ("blood_bank_patient_samples", "blood_bank_reservations", "blood_bank_reactions", "blood_bank_traceability_events", "blood_bank_returns", "blood_bank_discards"):
        if table in sa.inspect(op.get_bind()).get_table_names() and "updated_by" not in _columns(table):
            op.add_column(table, sa.Column("updated_by", sa.Integer(), nullable=True))
            op.create_index(f"ix_{table}_updated_by", table, ["updated_by"], if_not_exists=True)


def downgrade() -> None:
    for table in ("blood_bank_discards", "blood_bank_returns", "blood_bank_traceability_events", "blood_bank_reactions", "blood_bank_reservations", "blood_bank_patient_samples"):
        if table in sa.inspect(op.get_bind()).get_table_names() and "updated_by" in _columns(table):
            op.drop_column(table, "updated_by")
