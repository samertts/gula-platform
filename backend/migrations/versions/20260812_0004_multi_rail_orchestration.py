"""Multi-rail payment orchestration foundation (advisory only).

Revision ID: 20260812_0004
Revises: 20260812_0003
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260812_0004"
down_revision = "20260812_0003"
branch_labels = None
depends_on = None

FX_AMOUNT = sa.Numeric(24, 6)


def upgrade() -> None:
    op.create_table(
        "pay_payment_entities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("legal_name", sa.String(256), nullable=False),
        sa.Column("jurisdiction_code", sa.String(16), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("ledger_namespace", sa.String(96), nullable=False, unique=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING_REVIEW"),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("live_operations_approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "pay_payment_rails",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("payment_entity_id", sa.String(36), sa.ForeignKey("pay_payment_entities.id"), nullable=False),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("rail_type", sa.String(32), nullable=False),
        sa.Column("jurisdiction_code", sa.String(16), nullable=False),
        sa.Column("supported_currencies", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="DISABLED"),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("kill_switch_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("live_operations_approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("payment_entity_id", "code", name="uq_pay_rail_entity_code"),
    )
    op.create_index("ix_pay_payment_rails_payment_entity_id", "pay_payment_rails", ["payment_entity_id"])

    op.add_column("pay_providers", sa.Column("created_by", sa.Integer(), nullable=True))
    op.add_column("pay_providers", sa.Column("payment_entity_id", sa.String(36), nullable=True))
    op.add_column("pay_providers", sa.Column("rail_code", sa.String(64), nullable=True))
    op.add_column("pay_providers", sa.Column("jurisdiction_code", sa.String(16), nullable=True))
    op.add_column("pay_providers", sa.Column("live_approved", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_foreign_key("fk_pay_provider_entity", "pay_providers", "pay_payment_entities", ["payment_entity_id"], ["id"])
    op.create_foreign_key("fk_pay_provider_rail", "pay_providers", "pay_payment_rails", ["rail_code"], ["code"])
    op.create_index("ix_pay_providers_payment_entity_id", "pay_providers", ["payment_entity_id"])
    op.create_index("ix_pay_providers_rail_code", "pay_providers", ["rail_code"])

    op.add_column("pay_payment_intents", sa.Column("payment_entity_id", sa.String(36), nullable=True))
    op.create_foreign_key("fk_pay_intent_entity", "pay_payment_intents", "pay_payment_entities", ["payment_entity_id"], ["id"])
    op.create_index("ix_pay_payment_intents_payment_entity_id", "pay_payment_intents", ["payment_entity_id"])

    op.create_table(
        "pay_payment_routing_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("payment_entity_id", sa.String(36), sa.ForeignKey("pay_payment_entities.id"), nullable=False),
        sa.Column("rail_code", sa.String(64), sa.ForeignKey("pay_payment_rails.code"), nullable=False),
        sa.Column("provider_code", sa.String(64), sa.ForeignKey("pay_providers.code"), nullable=False),
        sa.Column("rule_version", sa.String(96), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("minimum_amount", FX_AMOUNT, nullable=True),
        sa.Column("maximum_amount", FX_AMOUNT, nullable=True),
        sa.Column("currency_code", sa.String(3), nullable=True),
        sa.Column("required_risk_level", sa.String(16), nullable=True),
        sa.Column("service_reference", sa.String(128), nullable=True),
        sa.Column("estimated_fee_bps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_rate_bps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("rule_version", name="uq_pay_routing_rule_version"),
        sa.CheckConstraint("priority >= 0", name="ck_pay_routing_priority_non_negative"),
    )
    op.create_index("ix_pay_payment_routing_rules_payment_entity_id", "pay_payment_routing_rules", ["payment_entity_id"])
    op.create_index("ix_pay_payment_routing_rules_rail_code", "pay_payment_routing_rules", ["rail_code"])
    op.create_index("ix_pay_payment_routing_rules_provider_code", "pay_payment_routing_rules", ["provider_code"])

    op.create_table(
        "pay_payment_routing_decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("payment_intent_id", sa.String(36), sa.ForeignKey("pay_payment_intents.id"), nullable=False),
        sa.Column("payment_entity_id", sa.String(36), sa.ForeignKey("pay_payment_entities.id"), nullable=False),
        sa.Column("rail_code", sa.String(64), nullable=True),
        sa.Column("provider_code", sa.String(64), nullable=True),
        sa.Column("correlation_id", sa.String(128), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("score", sa.Numeric(10, 4), nullable=True),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.Column("evaluated_candidates", sa.JSON(), nullable=False),
        sa.Column("rule_version", sa.String(96), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_pay_payment_routing_decisions_payment_intent_id", "pay_payment_routing_decisions", ["payment_intent_id"])
    op.create_index("ix_pay_payment_routing_decisions_payment_entity_id", "pay_payment_routing_decisions", ["payment_entity_id"])
    op.create_index("ix_pay_payment_routing_decisions_correlation_id", "pay_payment_routing_decisions", ["correlation_id"])


def downgrade() -> None:
    op.drop_table("pay_payment_routing_decisions")
    op.drop_table("pay_payment_routing_rules")
    op.drop_index("ix_pay_payment_intents_payment_entity_id", table_name="pay_payment_intents")
    op.drop_constraint("fk_pay_intent_entity", "pay_payment_intents", type_="foreignkey")
    op.drop_column("pay_payment_intents", "payment_entity_id")
    op.drop_index("ix_pay_providers_rail_code", table_name="pay_providers")
    op.drop_index("ix_pay_providers_payment_entity_id", table_name="pay_providers")
    op.drop_constraint("fk_pay_provider_rail", "pay_providers", type_="foreignkey")
    op.drop_constraint("fk_pay_provider_entity", "pay_providers", type_="foreignkey")
    op.drop_column("pay_providers", "live_approved")
    op.drop_column("pay_providers", "created_by")
    op.drop_column("pay_providers", "jurisdiction_code")
    op.drop_column("pay_providers", "rail_code")
    op.drop_column("pay_providers", "payment_entity_id")
    op.drop_table("pay_payment_rails")
    op.drop_table("pay_payment_entities")
