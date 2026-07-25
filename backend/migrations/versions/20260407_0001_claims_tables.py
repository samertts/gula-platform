"""Add claims and claim_items tables for insurance/billing integration.

Revision ID: 20260407_0001
Revises    : 20260329_0012
Create Date: 2026-04-07

Tables created:
  1. claims       — top-level insurance claim per patient/order
  2. claim_items  — line items (tests) within a claim
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "20260407_0001"
down_revision = "20260329_0012"
branch_labels = None
depends_on = None


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return inspect(bind).has_table(name)


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    cols = [c["name"] for c in inspect(bind).get_columns(table)]
    return column in cols


def _index_exists(index: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    for table in inspector.get_table_names():
        idx_names = [i["name"] for i in inspector.get_indexes(table)]
        if index in idx_names:
            return True
    return False


# ─── Upgrade ─────────────────────────────────────────────────────────────────


def upgrade() -> None:

    # ── 1. claims ─────────────────────────────────────────────────────────────
    if not _has_table("claims"):
        op.create_table(
            "claims",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False
            ),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("patients.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "order_id",
                sa.Integer(),
                sa.ForeignKey("lab_orders.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
            sa.Column("total_amount", sa.Numeric(12, 2), nullable=True),
            sa.Column("currency", sa.String(10), nullable=False, server_default="IQD"),
            sa.Column("idempotency_key", sa.String(255), nullable=True, unique=True),
            sa.Column("external_ref", sa.String(255), nullable=True),
            sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_claims_lab_id", "claims", ["lab_id"])
        op.create_index("ix_claims_patient_id", "claims", ["patient_id"])
        op.create_index("ix_claims_order_id", "claims", ["order_id"])
        op.create_index("ix_claims_status", "claims", ["status"])

    # ── 2. claim_items ────────────────────────────────────────────────────────
    if not _has_table("claim_items"):
        op.create_table(
            "claim_items",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "claim_id",
                sa.Integer(),
                sa.ForeignKey("claims.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("test_code", sa.String(100), nullable=False),
            sa.Column("description", sa.String(500), nullable=True),
            sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        )
        op.create_index("ix_claim_items_claim_id", "claim_items", ["claim_id"])


# ─── Downgrade ────────────────────────────────────────────────────────────────


def downgrade() -> None:
    if _has_table("claim_items"):
        op.drop_table("claim_items")
    if _has_table("claims"):
        op.drop_table("claims")
