"""Add idempotency fields for audited citizen relationship workflow.

Revision ID: 20260812_0001
Revises: 20260811_0002
Create Date: 2026-08-12

This migration is additive and does not create, activate, backfill, or revoke
any citizen relationships.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260812_0001"
down_revision: Union[str, None] = "20260811_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "niam_citizen_relationships",
        sa.Column("idempotency_key_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "niam_citizen_relationships",
        sa.Column("request_fingerprint", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_niam_citizen_relationships_idempotency_key_hash",
        "niam_citizen_relationships",
        ["idempotency_key_hash"],
        unique=True,
    )
    op.create_index(
        "ix_niam_citizen_relationships_request_fingerprint",
        "niam_citizen_relationships",
        ["request_fingerprint"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_niam_citizen_relationships_request_fingerprint",
        table_name="niam_citizen_relationships",
    )
    op.drop_index(
        "ix_niam_citizen_relationships_idempotency_key_hash",
        table_name="niam_citizen_relationships",
    )
    op.drop_column("niam_citizen_relationships", "request_fingerprint")
    op.drop_column("niam_citizen_relationships", "idempotency_key_hash")
