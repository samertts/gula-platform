"""add independent verification to critical care infusions

Revision ID: 20260820_0008
Revises: 20260820_0007
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260820_0008"
down_revision = "20260820_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "critical_care_infusions",
        sa.Column("verified_by", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "critical_care_infusions",
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("critical_care_infusions", "verified_at")
    op.drop_column("critical_care_infusions", "verified_by")
