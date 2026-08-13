"""Secure institutional subscriptions and usage entitlements.

No payment provider calls or automatic charges are made by this service.
"""
from __future__ import annotations

import calendar
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import update
from sqlalchemy.orm import Session

from app._compat import UTC
from app.domain.exceptions import ConflictError, NotFoundError, ServiceError

from .subscription_models import (
    PlatformSubscription,
    SubscriptionAuditEvent,
    SubscriptionBillingCycle,
    SubscriptionPlan,
    SubscriptionUsageCounter,
    SubscriptionUsageEvent,
)


def now_utc() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def add_months(value: datetime, months: int) -> datetime:
    """Calendar-aware period arithmetic without floating time durations."""
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


class InstitutionalSubscriptionService:
    def __init__(self, db: Session):
        self.db = db

    def _audit(self, *, action: str, actor_user_id: int, subscription_id: str | None = None,
               plan_id: str | None = None, cycle_id: str | None = None, metadata: dict[str, Any] | None = None) -> None:
        self.db.add(SubscriptionAuditEvent(
            subscription_id=subscription_id,
            plan_id=plan_id,
            cycle_id=cycle_id,
            action=action,
            actor_user_id=actor_user_id,
            metadata_json=metadata or {},
        ))

    def _plan(self, plan_id: str) -> SubscriptionPlan:
        plan = self.db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
        if plan is None:
            raise NotFoundError("Subscription plan not found")
        return plan

    def _subscription(self, subscription_id: str) -> PlatformSubscription:
        subscription = self.db.query(PlatformSubscription).filter(PlatformSubscription.id == subscription_id).first()
        if subscription is None:
            raise NotFoundError("Platform subscription not found")
        return subscription

    def create_plan(self, *, actor_user_id: int, **fields: Any) -> SubscriptionPlan:
        duplicate = self.db.query(SubscriptionPlan).filter(
            SubscriptionPlan.plan_code == fields["plan_code"],
            SubscriptionPlan.version == fields["version"],
        ).first()
        if duplicate:
            raise ConflictError("Subscription plan code and version already exist")
        plan = SubscriptionPlan(**fields, status="DRAFT", created_by=actor_user_id, approved_by=None)
        self.db.add(plan)
        self.db.flush()
        self._audit(action="PLAN_CREATED", actor_user_id=actor_user_id, plan_id=plan.id, metadata={"plan_code": plan.plan_code, "version": plan.version})
        return plan

    def approve_plan(self, *, plan_id: str, actor_user_id: int) -> SubscriptionPlan:
        plan = self._plan(plan_id)
        if plan.status != "DRAFT":
            raise ConflictError("Only draft subscription plans can be approved")
        if plan.created_by == actor_user_id:
            raise ServiceError("A different authorized user must approve a subscription plan", status_code=403)
        plan.status = "ACTIVE"
        plan.approved_by = actor_user_id
        plan.approved_at = now_utc()
        self._audit(action="PLAN_APPROVED", actor_user_id=actor_user_id, plan_id=plan.id)
        self.db.flush()
        return plan

    def create_subscription(self, *, lab_id: int, plan_id: str, billing_cycle: str,
                            starts_at: datetime, auto_renew: bool, actor_user_id: int) -> PlatformSubscription:
        plan = self._plan(plan_id)
        if plan.status != "ACTIVE":
            raise ServiceError("Subscription plan is not approved", status_code=409)
        existing = self.db.query(PlatformSubscription).filter(
            PlatformSubscription.lab_id == lab_id,
            PlatformSubscription.status.in_(("DRAFT", "ACTIVE", "PAST_DUE", "SUSPENDED")),
        ).first()
        if existing:
            raise ConflictError("An active or pending institutional subscription already exists for this lab")
        start = as_utc(starts_at)
        period_end = add_months(start, 1 if billing_cycle == "MONTHLY" else 12)
        subscription = PlatformSubscription(
            lab_id=lab_id,
            plan_id=plan.id,
            plan_code=plan.plan_code,
            plan_version=plan.version,
            status="DRAFT",
            billing_cycle=billing_cycle,
            starts_at=start,
            current_period_start=start,
            current_period_end=period_end,
            next_billing_at=period_end,
            auto_renew=auto_renew,
            cancel_at_period_end=False,
            created_by=actor_user_id,
        )
        self.db.add(subscription)
        self.db.flush()
        self._audit(action="SUBSCRIPTION_CREATED", actor_user_id=actor_user_id, subscription_id=subscription.id, plan_id=plan.id, metadata={"lab_id": lab_id, "billing_cycle": billing_cycle})
        return subscription

    def approve_subscription(self, *, subscription_id: str, actor_user_id: int) -> PlatformSubscription:
        subscription = self._subscription(subscription_id)
        if subscription.status != "DRAFT":
            raise ConflictError("Only draft subscriptions can be approved")
        if subscription.created_by == actor_user_id:
            raise ServiceError("A different authorized user must approve a subscription", status_code=403)
        subscription.status = "ACTIVE"
        subscription.approved_by = actor_user_id
        subscription.approved_at = now_utc()
        self._audit(action="SUBSCRIPTION_APPROVED", actor_user_id=actor_user_id, subscription_id=subscription.id)
        self._ensure_cycle(subscription=subscription, actor_user_id=actor_user_id)
        self.db.flush()
        return subscription

    def _cycle_amount(self, subscription: PlatformSubscription, plan: SubscriptionPlan) -> Decimal:
        return Decimal(plan.monthly_price if subscription.billing_cycle == "MONTHLY" else plan.yearly_price)

    def _ensure_cycle(self, *, subscription: PlatformSubscription, actor_user_id: int) -> SubscriptionBillingCycle:
        cycle_key = f"{subscription.id}:{subscription.current_period_start.isoformat()}"
        existing = self.db.query(SubscriptionBillingCycle).filter(SubscriptionBillingCycle.cycle_key == cycle_key).first()
        if existing:
            return existing
        plan = self._plan(subscription.plan_id)
        due_at = min(
            subscription.current_period_end,
            subscription.current_period_start + timedelta(days=plan.grace_period_days),
        )
        cycle = SubscriptionBillingCycle(
            subscription_id=subscription.id,
            cycle_key=cycle_key,
            period_start=subscription.current_period_start,
            period_end=subscription.current_period_end,
            due_at=due_at,
            amount=self._cycle_amount(subscription, plan),
            currency=plan.currency,
            status="ISSUED",
            created_by=actor_user_id,
        )
        self.db.add(cycle)
        self.db.flush()
        self._audit(action="CYCLE_ISSUED", actor_user_id=actor_user_id, subscription_id=subscription.id, cycle_id=cycle.id, metadata={"cycle_key": cycle_key, "amount": str(cycle.amount), "currency": cycle.currency})
        return cycle

    def generate_current_cycle(self, *, subscription_id: str, as_of: datetime, actor_user_id: int) -> SubscriptionBillingCycle:
        subscription = self._subscription(subscription_id)
        if subscription.status not in {"ACTIVE", "PAST_DUE"}:
            raise ServiceError("Subscription is not eligible for a billing cycle", status_code=409)
        if as_utc(as_of) < as_utc(subscription.current_period_start):
            raise ServiceError("Billing cycle cannot be generated before subscription start", status_code=409)
        return self._ensure_cycle(subscription=subscription, actor_user_id=actor_user_id)

    def record_usage(
        self, *, subscription_id: str, metric_code: str, quantity: int, idempotency_key: str,
        reference_type: str | None, reference_id: str | None, hard_limit: bool, actor_user_id: int,
    ) -> dict[str, Any]:
        subscription = self._subscription(subscription_id)
        if subscription.status != "ACTIVE":
            raise ServiceError("Subscription is not active", status_code=409)
        plan = self._plan(subscription.plan_id)
        if metric_code not in (plan.usage_limits or {}):
            raise ServiceError("Metric is not entitled by this subscription plan", status_code=403)
        limit = int(plan.usage_limits[metric_code])
        existing_event = self.db.query(SubscriptionUsageEvent).filter(
            SubscriptionUsageEvent.subscription_id == subscription.id,
            SubscriptionUsageEvent.metric_code == metric_code,
            SubscriptionUsageEvent.idempotency_key == idempotency_key,
        ).first()
        period_start = as_utc(subscription.current_period_start)
        if existing_event:
            counter = self.db.query(SubscriptionUsageCounter).filter(
                SubscriptionUsageCounter.subscription_id == subscription.id,
                SubscriptionUsageCounter.metric_code == metric_code,
                SubscriptionUsageCounter.period_start == period_start,
            ).first()
            return self._usage_response(subscription, metric_code, period_start, counter, limit, True)
        counter = self.db.query(SubscriptionUsageCounter).filter(
            SubscriptionUsageCounter.subscription_id == subscription.id,
            SubscriptionUsageCounter.metric_code == metric_code,
            SubscriptionUsageCounter.period_start == period_start,
        ).first()
        if counter is None:
            counter = SubscriptionUsageCounter(
                subscription_id=subscription.id,
                metric_code=metric_code,
                period_start=period_start,
                period_end=as_utc(subscription.current_period_end),
                used_quantity=0,
                limit_quantity=limit,
                version=0,
            )
            self.db.add(counter)
            self.db.flush()
        new_total = counter.used_quantity + quantity
        if new_total > limit and hard_limit:
            return {
                "subscription_id": subscription.id,
                "metric_code": metric_code,
                "period_start": period_start,
                "used_quantity": counter.used_quantity,
                "limit_quantity": limit,
                "decision": "REJECTED",
                "idempotent_replay": False,
            }
        result = self.db.execute(
            update(SubscriptionUsageCounter)
            .where(SubscriptionUsageCounter.id == counter.id, SubscriptionUsageCounter.version == counter.version)
            .values(used_quantity=new_total, version=counter.version + 1, updated_at=now_utc())
        )
        if result.rowcount != 1:
            raise ConflictError("Concurrent subscription usage update detected; retry with the same idempotency key")
        event = SubscriptionUsageEvent(
            subscription_id=subscription.id,
            metric_code=metric_code,
            quantity=quantity,
            idempotency_key=idempotency_key,
            reference_type=reference_type,
            reference_id=reference_id,
            period_start=period_start,
            recorded_by=actor_user_id,
        )
        self.db.add(event)
        self._audit(action="USAGE_RECORDED", actor_user_id=actor_user_id, subscription_id=subscription.id, metadata={"metric_code": metric_code, "quantity": quantity, "reference_type": reference_type})
        self.db.flush()
        counter = self.db.query(SubscriptionUsageCounter).filter(SubscriptionUsageCounter.id == counter.id).first()
        return self._usage_response(subscription, metric_code, period_start, counter, limit, False)

    @staticmethod
    def _usage_response(subscription: PlatformSubscription, metric_code: str, period_start: datetime,
                        counter: SubscriptionUsageCounter | None, limit: int, idempotent_replay: bool) -> dict[str, Any]:
        used = int(counter.used_quantity) if counter else 0
        if used > limit:
            decision = "WARNING"
        elif limit and Decimal(used) / Decimal(limit) >= Decimal("0.80"):
            decision = "WARNING"
        else:
            decision = "ALLOWED"
        return {
            "subscription_id": subscription.id,
            "metric_code": metric_code,
            "period_start": period_start,
            "used_quantity": used,
            "limit_quantity": limit,
            "decision": decision,
            "idempotent_replay": idempotent_replay,
        }
