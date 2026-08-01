"""Widen patient health_id/gender columns (GULA- + 16 hex = 21 chars)

Revision ID: 20260802_0001
Revises: 20260723_0002
Create Date: 2026-08-02

The platform generates health_ids as `GULA-{token_hex(8).upper()}` (21 chars),
which exceeds the original varchar(20) columns, and stores gender as
`male`/`female` which exceeds varchar(1). Widen both — backwards compatible
(existing 20-char ids and 1-char codes remain valid).
"""

from alembic import op
import sqlalchemy as sa

revision = "20260802_0001"
down_revision = "20260723_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("patients", "health_id", type_=sa.String(32), existing_type=sa.String(20))
    op.alter_column(
        "canonical_patients", "health_id", type_=sa.String(32), existing_type=sa.String(20)
    )
    op.alter_column("patients", "gender", type_=sa.String(10), existing_type=sa.String(1))
    op.alter_column(
        "canonical_patients", "gender", type_=sa.String(10), existing_type=sa.String(1)
    )
    op.alter_column("citizens", "gender", type_=sa.String(10), existing_type=sa.String(1))


def downgrade() -> None:
    op.alter_column("patients", "health_id", type_=sa.String(20), existing_type=sa.String(32))
    op.alter_column(
        "canonical_patients", "health_id", type_=sa.String(20), existing_type=sa.String(32)
    )
    op.alter_column("patients", "gender", type_=sa.String(1), existing_type=sa.String(10))
    op.alter_column(
        "canonical_patients", "gender", type_=sa.String(1), existing_type=sa.String(10)
    )
    op.alter_column("citizens", "gender", type_=sa.String(1), existing_type=sa.String(10))
