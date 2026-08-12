"""Institutional subscription billing models, independent from patient service payments."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, JSON, Numeric, String, UniqueConstraint, event

from app._compat import UTC
from app.financial.models import FinBase


SUB_AMOUNT = Numeric(24, 6)


def _uuid() -> str:
    return str(uuid4())


class SubscriptionPlan(FinBase):
    __tablename__ = "pay_subscription_plans"
    __table_args__ = (
        UniqueConstraint("plan_code", "version", name="uq_pay_subscription_plan_version"),
        CheckConstraint("monthly_price >= 0", name="ck_pay_sub_plan_monthly_non_negative"),
        CheckConstraint("yearly_price >= 0", name="ck_pay_sub_plan_yearly_non_negative"),
        CheckConstraint("grace_period_days >= 0", name="ck_pay_sub_plan_grace_non_negative"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    plan_code = Column(String(64), nullable=False, index=True)
    version = Column(String(64), nullable=False)
    display_name = Column(String(128), nullable=False)
    currency = Column(String(3), nullable=False, default="IQD")
    monthly_price = Column(SUB_AMOUNT, nullable=False, default=Decimal("0"))
    yearly_price = Column(SUB_AMOUNT, nullable=False, default=Decimal("0"))
    grace_period_days = Column(Integer, nullable=False, default=0)
    usage_limits = Column(JSON, nullable=False, default=dict)
    feature_entitlements = Column(JSON, nullable=False, default=dict)
    status = Column(String(32), nullable=False, default="DRAFT")
    created_by = Column(Integer, nullable=True)
    approved_by = Column(Integer, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class PlatformSubscription(FinBase):
    __tablename__ = "pay_platform_subscriptions"
    __table_args__ = (
        CheckConstraint("billing_cycle IN ('MONTHLY', 'YEARLY')", name="ck_pay_platform_sub_cycle"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    lab_id = Column(Integer, nullable=False, index=True)
    plan_id = Column(String(36), ForeignKey("pay_subscription_plans.id"), nullable=False, index=True)
    plan_code = Column(String(64), nullable=False)
    plan_version = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="DRAFT", index=True)
    billing_cycle = Column(String(16), nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    next_billing_at = Column(DateTime(timezone=True), nullable=False)
    auto_renew = Column(Boolean, nullable=False, default=False)
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)
    created_by = Column(Integer, nullable=True)
    approved_by = Column(Integer, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class SubscriptionBillingCycle(FinBase):
    __tablename__ = "pay_subscription_billing_cycles"
    __table_args__ = (
        UniqueConstraint("subscription_id", "period_start", name="uq_pay_sub_cycle_period"),
        UniqueConstraint("cycle_key", name="uq_pay_sub_cycle_key"),
        CheckConstraint("amount >= 0", name="ck_pay_sub_cycle_amount_non_negative"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    subscription_id = Column(String(36), ForeignKey("pay_platform_subscriptions.id"), nullable=False, index=True)
    cycle_key = Column(String(160), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=False)
    amount = Column(SUB_AMOUNT, nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String(32), nullable=False, default="ISSUED", index=True)
    payment_reference = Column(String(128), nullable=True, unique=True)
    issued_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    settled_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, nullable=True)


class SubscriptionUsageCounter(FinBase):
    __tablename__ = "pay_subscription_usage_counters"
    __table_args__ = (
        UniqueConstraint("subscription_id", "metric_code", "period_start", name="uq_pay_sub_usage_counter"),
        CheckConstraint("used_quantity >= 0", name="ck_pay_sub_usage_used_non_negative"),
        CheckConstraint("limit_quantity >= 0", name="ck_pay_sub_usage_limit_non_negative"),
        CheckConstraint("version >= 0", name="ck_pay_sub_usage_version_non_negative"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    subscription_id = Column(String(36), ForeignKey("pay_platform_subscriptions.id"), nullable=False, index=True)
    metric_code = Column(String(64), nullable=False, index=True)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    used_quantity = Column(Integer, nullable=False, default=0)
    limit_quantity = Column(Integer, nullable=False)
    version = Column(Integer, nullable=False, default=0)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class SubscriptionUsageEvent(FinBase):
    __tablename__ = "pay_subscription_usage_events"
    __table_args__ = (
        UniqueConstraint("subscription_id", "metric_code", "idempotency_key", name="uq_pay_sub_usage_event_idempotency"),
        CheckConstraint("quantity > 0", name="ck_pay_sub_usage_event_positive"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    subscription_id = Column(String(36), ForeignKey("pay_platform_subscriptions.id"), nullable=False, index=True)
    metric_code = Column(String(64), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    idempotency_key = Column(String(128), nullable=False)
    reference_type = Column(String(64), nullable=True)
    reference_id = Column(String(128), nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=False)
    recorded_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class SubscriptionAuditEvent(FinBase):
    __tablename__ = "pay_subscription_audit_events"

    id = Column(String(36), primary_key=True, default=_uuid)
    subscription_id = Column(String(36), ForeignKey("pay_platform_subscriptions.id"), nullable=True, index=True)
    plan_id = Column(String(36), ForeignKey("pay_subscription_plans.id"), nullable=True, index=True)
    cycle_id = Column(String(36), ForeignKey("pay_subscription_billing_cycles.id"), nullable=True, index=True)
    action = Column(String(64), nullable=False, index=True)
    actor_user_id = Column(Integer, nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


def _reject_subscription_history_mutation(*_args, **_kwargs) -> None:
    raise ValueError("Subscription usage and audit history are immutable")


for _immutable_model in (SubscriptionUsageEvent, SubscriptionAuditEvent):
    event.listen(_immutable_model, "before_update", _reject_subscription_history_mutation)
    event.listen(_immutable_model, "before_delete", _reject_subscription_history_mutation)
