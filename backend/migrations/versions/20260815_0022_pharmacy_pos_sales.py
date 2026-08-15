"""Add institution-scoped pharmacy POS sales.

Revision ID: 20260815_0022
Revises: 20260815_0021
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260815_0022"
down_revision: str | None = "20260815_0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _table_exists("pharmacy_sales"):
        op.create_table(
            "pharmacy_sales",
            sa.Column("id", sa.String(26), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("patient_id", sa.String(26), nullable=True),
            sa.Column("citizen_id", sa.String(26), nullable=True),
            sa.Column("billing_patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("encounter_id", sa.String(26), nullable=True),
            sa.Column("billing_invoice_id", sa.Integer(), sa.ForeignKey("billing_invoices.id", ondelete="SET NULL"), nullable=True),
            sa.Column("sale_number", sa.String(50), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="completed"),
            sa.Column("currency", sa.String(3), nullable=False, server_default="IQD"),
            sa.Column("subtotal", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("discount", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("total_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("cost_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("gross_profit", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("payment_status", sa.String(24), nullable=False, server_default="paid"),
            sa.Column("payment_method", sa.String(40), nullable=False, server_default="synthetic_settlement"),
            sa.Column("idempotency_key", sa.String(128), nullable=True),
            sa.Column("sold_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("lab_id", "sale_number", name="uq_pharmacy_sale_lab_number"),
            sa.UniqueConstraint("lab_id", "idempotency_key", name="uq_pharmacy_sale_lab_idempotency"),
            sa.CheckConstraint("subtotal >= 0", name="ck_pharmacy_sale_subtotal_non_negative"),
            sa.CheckConstraint("discount >= 0", name="ck_pharmacy_sale_discount_non_negative"),
            sa.CheckConstraint("total_amount >= 0", name="ck_pharmacy_sale_total_non_negative"),
            sa.CheckConstraint("cost_amount >= 0", name="ck_pharmacy_sale_cost_non_negative"),
        )
        op.create_index("ix_pharmacy_sales_lab_status", "pharmacy_sales", ["lab_id", "status"])
        op.create_index("ix_pharmacy_sales_lab_citizen", "pharmacy_sales", ["lab_id", "citizen_id"])
        op.create_index("ix_pharmacy_sales_lab_sold_at", "pharmacy_sales", ["lab_id", "sold_at"])

    if not _table_exists("pharmacy_sale_lines"):
        op.create_table(
            "pharmacy_sale_lines",
            sa.Column("id", sa.String(26), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("sale_id", sa.String(26), sa.ForeignKey("pharmacy_sales.id", ondelete="CASCADE"), nullable=False),
            sa.Column("drug_catalog_id", sa.String(26), nullable=False),
            sa.Column("batch_id", sa.String(26), nullable=False),
            sa.Column("prescription_id", sa.String(26), nullable=True),
            sa.Column("medication_dispense_id", sa.String(26), nullable=True),
            sa.Column("line_number", sa.Integer(), nullable=False),
            sa.Column("barcode", sa.String(64), nullable=True),
            sa.Column("medication_name", sa.String(300), nullable=False),
            sa.Column("medication_name_ar", sa.String(300), nullable=True),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("quantity_unit", sa.String(50), nullable=True),
            sa.Column("lot_number", sa.String(100), nullable=True),
            sa.Column("expiry_date", sa.Date(), nullable=True),
            sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
            sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("discount", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("line_total", sa.Numeric(12, 2), nullable=False),
            sa.Column("line_cost", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("sale_id", "line_number", name="uq_pharmacy_sale_line_number"),
            sa.CheckConstraint("quantity > 0", name="ck_pharmacy_sale_line_quantity_positive"),
            sa.CheckConstraint("unit_price >= 0", name="ck_pharmacy_sale_line_unit_price_non_negative"),
            sa.CheckConstraint("unit_cost >= 0", name="ck_pharmacy_sale_line_unit_cost_non_negative"),
            sa.CheckConstraint("line_total >= 0", name="ck_pharmacy_sale_line_total_non_negative"),
            sa.CheckConstraint("line_cost >= 0", name="ck_pharmacy_sale_line_cost_non_negative"),
        )
        op.create_index("ix_pharmacy_sale_lines_sale_drug", "pharmacy_sale_lines", ["sale_id", "drug_catalog_id"])


def downgrade() -> None:
    if _table_exists("pharmacy_sale_lines"):
        op.drop_index("ix_pharmacy_sale_lines_sale_drug", table_name="pharmacy_sale_lines")
        op.drop_table("pharmacy_sale_lines")
    if _table_exists("pharmacy_sales"):
        op.drop_index("ix_pharmacy_sales_lab_sold_at", table_name="pharmacy_sales")
        op.drop_index("ix_pharmacy_sales_lab_citizen", table_name="pharmacy_sales")
        op.drop_index("ix_pharmacy_sales_lab_status", table_name="pharmacy_sales")
        op.drop_table("pharmacy_sales")
