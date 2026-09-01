"""Persistent Blood Bank return and discard records.

Revision ID: 20260901_0002
Revises: 20260901_0001
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = "20260901_0002"
down_revision = "20260901_0001"
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    tables = _tables()
    common = [
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(100)),
    ]
    if "blood_bank_returns" not in tables:
        op.create_table("blood_bank_returns", *common,
            sa.Column("unit_id", sa.String(100), nullable=False),
            sa.Column("reservation_id", sa.String(100)),
            sa.Column("issue_id", sa.String(100)),
            sa.Column("patient_id", sa.String(100)),
            sa.Column("facility_id", sa.String(100), nullable=False),
            sa.Column("status", sa.String(40), nullable=False, server_default="return_requested"),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("integrity", sa.String(40)),
            sa.Column("inspected_by", sa.String(100)),
            sa.Column("inspected_at", sa.DateTime(timezone=True)),
            sa.Column("outcome", sa.String(40)),
        )
    if "blood_bank_discards" not in tables:
        op.create_table("blood_bank_discards", *common,
            sa.Column("unit_id", sa.String(100), nullable=False),
            sa.Column("issue_id", sa.String(100)),
            sa.Column("patient_id", sa.String(100)),
            sa.Column("facility_id", sa.String(100), nullable=False),
            sa.Column("category", sa.String(60), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("discarded_by", sa.String(100), nullable=False),
            sa.Column("discarded_at", sa.DateTime(timezone=True), nullable=False),
        )
    for table, cols in {"blood_bank_returns": ["lab_id", "unit_id", "facility_id", "status"], "blood_bank_discards": ["lab_id", "unit_id", "facility_id", "category"]}.items():
        for col in cols:
            op.create_index(f"ix_{table}_{col}", table, [col], if_not_exists=True)


def downgrade() -> None:
    tables = _tables()
    for table in ("blood_bank_discards", "blood_bank_returns"):
        if table in tables:
            op.drop_table(table)
