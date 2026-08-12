"""Currency and FX quote engine (non-production reference quotes).

Revision ID: 20260812_0003
Revises: 20260812_0002
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260812_0003"
down_revision = "20260812_0002"
branch_labels = None
depends_on = None

FX_AMOUNT = sa.Numeric(24, 6)


def upgrade() -> None:
    op.create_table(
        "pay_currency_definitions",
        sa.Column("code", sa.String(3), primary_key=True),
        sa.Column("display_name", sa.String(96), nullable=False),
        sa.Column("minor_unit", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("rounding_mode", sa.String(32), nullable=False, server_default="HALF_UP"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("fx_quote_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "pay_fx_rate_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_code", sa.String(64), nullable=False),
        sa.Column("source_reference", sa.String(512), nullable=False),
        sa.Column("source_digest", sa.String(128), nullable=True),
        sa.Column("rate_version", sa.String(96), nullable=False),
        sa.Column("base_currency", sa.String(3), sa.ForeignKey("pay_currency_definitions.code"), nullable=False),
        sa.Column("quote_currency", sa.String(3), sa.ForeignKey("pay_currency_definitions.code"), nullable=False),
        sa.Column("reference_rate", sa.Numeric(24, 10), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("verification_status", sa.String(32), nullable=False, server_default="PENDING_REVIEW"),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("verified_by", sa.Integer(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "source_code", "source_reference", "base_currency", "quote_currency", "rate_version",
            name="uq_pay_fx_snapshot_source_version",
        ),
        sa.CheckConstraint("reference_rate > 0", name="ck_pay_fx_rate_positive"),
    )
    op.create_index("ix_pay_fx_rate_snapshots_base_currency", "pay_fx_rate_snapshots", ["base_currency"])
    op.create_index("ix_pay_fx_rate_snapshots_quote_currency", "pay_fx_rate_snapshots", ["quote_currency"])

    op.create_table(
        "pay_fx_fee_policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("institution_id", sa.Integer(), nullable=True),
        sa.Column("policy_version", sa.String(96), nullable=False),
        sa.Column("base_currency", sa.String(3), nullable=True),
        sa.Column("quote_currency", sa.String(3), nullable=True),
        sa.Column("service_reference", sa.String(128), nullable=True),
        sa.Column("provider_code", sa.String(64), nullable=True),
        sa.Column("fee_bps", sa.Integer(), nullable=False, server_default="200"),
        sa.Column("minimum_fee", FX_AMOUNT, nullable=False, server_default="0"),
        sa.Column("maximum_fee", FX_AMOUNT, nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IQD"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("policy_version", name="uq_pay_fx_fee_policy_version"),
        sa.CheckConstraint("fee_bps >= 0 AND fee_bps <= 10000", name="ck_pay_fx_fee_bps_range"),
        sa.CheckConstraint("minimum_fee >= 0", name="ck_pay_fx_fee_minimum_non_negative"),
        sa.CheckConstraint("maximum_fee IS NULL OR maximum_fee >= minimum_fee", name="ck_pay_fx_fee_maximum"),
    )
    op.create_index("ix_pay_fx_fee_policies_institution_id", "pay_fx_fee_policies", ["institution_id"])

    op.create_table(
        "pay_fx_quotes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.String(36), sa.ForeignKey("pay_invoices.id"), nullable=True),
        sa.Column("rate_snapshot_id", sa.String(36), sa.ForeignKey("pay_fx_rate_snapshots.id"), nullable=False),
        sa.Column("fee_policy_id", sa.String(36), sa.ForeignKey("pay_fx_fee_policies.id"), nullable=True),
        sa.Column("base_currency", sa.String(3), nullable=False),
        sa.Column("quote_currency", sa.String(3), nullable=False),
        sa.Column("base_amount", FX_AMOUNT, nullable=False),
        sa.Column("reference_rate", sa.Numeric(24, 10), nullable=False),
        sa.Column("base_converted_amount", FX_AMOUNT, nullable=False),
        sa.Column("administrative_fee_amount", FX_AMOUNT, nullable=False, server_default="0"),
        sa.Column("provider_fee_amount", FX_AMOUNT, nullable=False, server_default="0"),
        sa.Column("total_quote_amount", FX_AMOUNT, nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="CREATED"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("base_amount > 0", name="ck_pay_fx_quote_base_positive"),
        sa.CheckConstraint("reference_rate > 0", name="ck_pay_fx_quote_rate_positive"),
        sa.CheckConstraint("base_converted_amount >= 0", name="ck_pay_fx_quote_converted_non_negative"),
        sa.CheckConstraint("administrative_fee_amount >= 0", name="ck_pay_fx_quote_fee_non_negative"),
        sa.CheckConstraint("provider_fee_amount >= 0", name="ck_pay_fx_quote_provider_fee_non_negative"),
        sa.CheckConstraint("total_quote_amount >= 0", name="ck_pay_fx_quote_total_non_negative"),
    )
    op.create_index("ix_pay_fx_quotes_institution_id", "pay_fx_quotes", ["institution_id"])
    op.create_index("ix_pay_fx_quotes_invoice_id", "pay_fx_quotes", ["invoice_id"])
    op.create_index("ix_pay_fx_quotes_rate_snapshot_id", "pay_fx_quotes", ["rate_snapshot_id"])
    op.create_index("ix_pay_fx_quotes_fee_policy_id", "pay_fx_quotes", ["fee_policy_id"])
    op.create_index("ix_pay_fx_quotes_status", "pay_fx_quotes", ["status"])

    op.create_table(
        "pay_risk_assessments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("payment_intent_id", sa.String(36), sa.ForeignKey("pay_payment_intents.id"), nullable=True),
        sa.Column("fx_quote_id", sa.String(36), sa.ForeignKey("pay_fx_quotes.id"), nullable=True),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("risk_level", sa.String(16), nullable=False),
        sa.Column("recommended_action", sa.String(32), nullable=False, server_default="REVIEW"),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_outcome", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="ck_pay_risk_score_range"),
    )
    op.create_index("ix_pay_risk_assessments_institution_id", "pay_risk_assessments", ["institution_id"])
    op.create_index("ix_pay_risk_assessments_payment_intent_id", "pay_risk_assessments", ["payment_intent_id"])
    op.create_index("ix_pay_risk_assessments_fx_quote_id", "pay_risk_assessments", ["fx_quote_id"])


def downgrade() -> None:
    for table in (
        "pay_risk_assessments",
        "pay_fx_quotes",
        "pay_fx_fee_policies",
        "pay_fx_rate_snapshots",
        "pay_currency_definitions",
    ):
        op.drop_table(table)
