"""Institutional subscriptions, recurring billing cycles, and usage limits.

Revision ID: 20260812_0005
Revises: 20260812_0004
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260812_0005"
down_revision = "20260812_0004"
branch_labels = None
depends_on = None

SUB_AMOUNT = sa.Numeric(24, 6)


def upgrade() -> None:
    op.create_table(
        "pay_subscription_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("plan_code", sa.String(64), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IQD"),
        sa.Column("monthly_price", SUB_AMOUNT, nullable=False, server_default="0"),
        sa.Column("yearly_price", SUB_AMOUNT, nullable=False, server_default="0"),
        sa.Column("grace_period_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("usage_limits", sa.JSON(), nullable=False),
        sa.Column("feature_entitlements", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("plan_code", "version", name="uq_pay_subscription_plan_version"),
        sa.CheckConstraint("monthly_price >= 0", name="ck_pay_sub_plan_monthly_non_negative"),
        sa.CheckConstraint("yearly_price >= 0", name="ck_pay_sub_plan_yearly_non_negative"),
        sa.CheckConstraint("grace_period_days >= 0", name="ck_pay_sub_plan_grace_non_negative"),
    )
    op.create_index("ix_pay_subscription_plans_plan_code", "pay_subscription_plans", ["plan_code"])

    op.create_table(
        "pay_platform_subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("pay_subscription_plans.id"), nullable=False),
        sa.Column("plan_code", sa.String(64), nullable=False),
        sa.Column("plan_version", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("billing_cycle", sa.String(16), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_billing_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("billing_cycle IN ('MONTHLY', 'YEARLY')", name="ck_pay_platform_sub_cycle"),
    )
    op.create_index("ix_pay_platform_subscriptions_lab_id", "pay_platform_subscriptions", ["lab_id"])
    op.create_index("ix_pay_platform_subscriptions_plan_id", "pay_platform_subscriptions", ["plan_id"])
    op.create_index("ix_pay_platform_subscriptions_status", "pay_platform_subscriptions", ["status"])

    op.create_table(
        "pay_subscription_billing_cycles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("subscription_id", sa.String(36), sa.ForeignKey("pay_platform_subscriptions.id"), nullable=False),
        sa.Column("cycle_key", sa.String(160), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount", SUB_AMOUNT, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="ISSUED"),
        sa.Column("payment_reference", sa.String(128), nullable=True, unique=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.UniqueConstraint("subscription_id", "period_start", name="uq_pay_sub_cycle_period"),
        sa.UniqueConstraint("cycle_key", name="uq_pay_sub_cycle_key"),
        sa.CheckConstraint("amount >= 0", name="ck_pay_sub_cycle_amount_non_negative"),
    )
    op.create_index("ix_pay_subscription_billing_cycles_subscription_id", "pay_subscription_billing_cycles", ["subscription_id"])
    op.create_index("ix_pay_subscription_billing_cycles_status", "pay_subscription_billing_cycles", ["status"])

    op.create_table(
        "pay_subscription_usage_counters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("subscription_id", sa.String(36), sa.ForeignKey("pay_platform_subscriptions.id"), nullable=False),
        sa.Column("metric_code", sa.String(64), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("limit_quantity", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("subscription_id", "metric_code", "period_start", name="uq_pay_sub_usage_counter"),
        sa.CheckConstraint("used_quantity >= 0", name="ck_pay_sub_usage_used_non_negative"),
        sa.CheckConstraint("limit_quantity >= 0", name="ck_pay_sub_usage_limit_non_negative"),
        sa.CheckConstraint("version >= 0", name="ck_pay_sub_usage_version_non_negative"),
    )
    op.create_index("ix_pay_subscription_usage_counters_subscription_id", "pay_subscription_usage_counters", ["subscription_id"])
    op.create_index("ix_pay_subscription_usage_counters_metric_code", "pay_subscription_usage_counters", ["metric_code"])

    op.create_table(
        "pay_subscription_usage_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("subscription_id", sa.String(36), sa.ForeignKey("pay_platform_subscriptions.id"), nullable=False),
        sa.Column("metric_code", sa.String(64), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("reference_type", sa.String(64), nullable=True),
        sa.Column("reference_id", sa.String(128), nullable=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("subscription_id", "metric_code", "idempotency_key", name="uq_pay_sub_usage_event_idempotency"),
        sa.CheckConstraint("quantity > 0", name="ck_pay_sub_usage_event_positive"),
    )
    op.create_index("ix_pay_subscription_usage_events_subscription_id", "pay_subscription_usage_events", ["subscription_id"])
    op.create_index("ix_pay_subscription_usage_events_metric_code", "pay_subscription_usage_events", ["metric_code"])

    op.create_table(
        "pay_subscription_audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("subscription_id", sa.String(36), sa.ForeignKey("pay_platform_subscriptions.id"), nullable=True),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("pay_subscription_plans.id"), nullable=True),
        sa.Column("cycle_id", sa.String(36), sa.ForeignKey("pay_subscription_billing_cycles.id"), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_pay_subscription_audit_events_subscription_id", "pay_subscription_audit_events", ["subscription_id"])
    op.create_index("ix_pay_subscription_audit_events_plan_id", "pay_subscription_audit_events", ["plan_id"])
    op.create_index("ix_pay_subscription_audit_events_cycle_id", "pay_subscription_audit_events", ["cycle_id"])
    op.create_index("ix_pay_subscription_audit_events_action", "pay_subscription_audit_events", ["action"])


def downgrade() -> None:
    op.drop_table("pay_subscription_audit_events")
    op.drop_table("pay_subscription_usage_events")
    op.drop_table("pay_subscription_usage_counters")
    op.drop_table("pay_subscription_billing_cycles")
    op.drop_table("pay_platform_subscriptions")
    op.drop_table("pay_subscription_plans")
