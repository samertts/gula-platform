"""Widen patient health_id/gender columns (GULA- + 16 hex = 21 chars)

Revision ID: 20260802_0001
Revises: 20260723_0002
Create Date: 2026-08-02

The platform generates health_ids as `GULA-{token_hex(8).upper()}` (21 chars),
which exceeds the original varchar(20) columns, and stores gender as
`male`/`female` which exceeds varchar(1). Widen both — backwards compatible
(existing 20-char ids and 1-char codes remain valid).

Also brings the legacy `organizations` table (created by an early migration
with only id/name/org_type/is_active) up to the full model contract
(org_id, name_en/ar, parent_org_id, contact_*), so the national bootstrap
(ministry/directorate seeding) can run on pre-existing databases.
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

    op.execute("ALTER TABLE organizations ALTER COLUMN name DROP NOT NULL")
    for col in ("org_id", "name_en", "name_ar", "parent_org_id"):
        op.execute(
            f"ALTER TABLE organizations ADD COLUMN IF NOT EXISTS {col} {_col_type(col)}"
        )
    for col in ("contact_email", "contact_phone", "address", "created_at", "updated_at"):
        op.execute(
            f"ALTER TABLE organizations ADD COLUMN IF NOT EXISTS {col} {_col_type(col)}"
        )

    op.execute("ALTER TABLE facilities ALTER COLUMN name DROP NOT NULL")
    op.execute("ALTER TABLE facilities ADD COLUMN IF NOT EXISTS facility_id varchar(100)")
    op.execute("ALTER TABLE facilities ADD COLUMN IF NOT EXISTS name_en varchar(200)")
    op.execute("ALTER TABLE facilities ADD COLUMN IF NOT EXISTS name_ar varchar(200)")
    op.execute("ALTER TABLE facilities ADD COLUMN IF NOT EXISTS created_at timestamptz")


def _col_type(col: str) -> str:
    return {
        "org_id": "varchar(100)",
        "name_en": "varchar(200)",
        "name_ar": "varchar(200)",
        "parent_org_id": "varchar(100)",
        "contact_email": "varchar(200)",
        "contact_phone": "varchar(30)",
        "address": "text",
        "created_at": "timestamptz",
        "updated_at": "timestamptz",
    }[col]


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
