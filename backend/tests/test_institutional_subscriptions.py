from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.financial.models import FinBase
from app.payments.subscription_models import SubscriptionBillingCycle, SubscriptionUsageCounter
from app.payments.subscription_service import InstitutionalSubscriptionService, now_utc


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    FinBase.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    try:
        yield session
    finally:
        session.close()
        FinBase.metadata.drop_all(engine)
        engine.dispose()


def active_subscription(db, *, lab_id: int = 12):
    service = InstitutionalSubscriptionService(db)
    plan = service.create_plan(
        plan_code="GULA_GROWTH",
        version="2026.08",
        display_name="GULA Growth",
        currency="IQD",
        monthly_price=Decimal("50000"),
        yearly_price=Decimal("500000"),
        grace_period_days=7,
        usage_limits={"ORDERS_PER_DAY": 3, "AI_CALLS_PER_DAY": 10},
        feature_entitlements={"AI": True},
        actor_user_id=101,
    )
    service.approve_plan(plan_id=plan.id, actor_user_id=202)
    subscription = service.create_subscription(
        lab_id=lab_id,
        plan_id=plan.id,
        billing_cycle="MONTHLY",
        starts_at=now_utc(),
        auto_renew=False,
        actor_user_id=101,
    )
    service.approve_subscription(subscription_id=subscription.id, actor_user_id=202)
    return service, plan, subscription


def test_subscription_approval_issues_exactly_one_idempotent_billing_cycle(db):
    service, plan, subscription = active_subscription(db)

    initial_cycles = db.query(SubscriptionBillingCycle).filter_by(subscription_id=subscription.id).all()
    replay = service.generate_current_cycle(
        subscription_id=subscription.id,
        as_of=subscription.starts_at + timedelta(minutes=1),
        actor_user_id=202,
    )
    db.flush()

    assert subscription.status == "ACTIVE"
    assert len(initial_cycles) == 1
    assert replay.id == initial_cycles[0].id
    assert db.query(SubscriptionBillingCycle).filter_by(subscription_id=subscription.id).count() == 1
    assert Decimal(replay.amount) == Decimal("50000")
    assert replay.currency == "IQD"
    assert replay.status == "ISSUED"


def test_usage_limit_is_idempotent_and_hard_rejects_overage(db):
    service, _plan, subscription = active_subscription(db)

    first = service.record_usage(
        subscription_id=subscription.id,
        metric_code="ORDERS_PER_DAY",
        quantity=2,
        idempotency_key="order-event-0001",
        reference_type="ORDER",
        reference_id="ORDER-1",
        hard_limit=True,
        actor_user_id=101,
    )
    replay = service.record_usage(
        subscription_id=subscription.id,
        metric_code="ORDERS_PER_DAY",
        quantity=2,
        idempotency_key="order-event-0001",
        reference_type="ORDER",
        reference_id="ORDER-1",
        hard_limit=True,
        actor_user_id=101,
    )
    rejected = service.record_usage(
        subscription_id=subscription.id,
        metric_code="ORDERS_PER_DAY",
        quantity=2,
        idempotency_key="order-event-0002",
        reference_type="ORDER",
        reference_id="ORDER-2",
        hard_limit=True,
        actor_user_id=101,
    )
    db.flush()
    counter = db.query(SubscriptionUsageCounter).filter_by(subscription_id=subscription.id, metric_code="ORDERS_PER_DAY").one()

    assert first["used_quantity"] == 2
    assert first["idempotent_replay"] is False
    assert replay["used_quantity"] == 2
    assert replay["idempotent_replay"] is True
    assert rejected["decision"] == "REJECTED"
    assert rejected["used_quantity"] == 2
    assert counter.used_quantity == 2


def test_plan_and_subscription_require_independent_approval(db):
    service = InstitutionalSubscriptionService(db)
    plan = service.create_plan(
        plan_code="GULA_STARTER",
        version="2026.08",
        display_name="GULA Starter",
        currency="IQD",
        monthly_price=Decimal("0"),
        yearly_price=Decimal("0"),
        grace_period_days=0,
        usage_limits={},
        feature_entitlements={},
        actor_user_id=101,
    )
    with pytest.raises(Exception, match="different authorized user"):
        service.approve_plan(plan_id=plan.id, actor_user_id=101)

    service.approve_plan(plan_id=plan.id, actor_user_id=202)
    subscription = service.create_subscription(
        lab_id=13,
        plan_id=plan.id,
        billing_cycle="YEARLY",
        starts_at=now_utc(),
        auto_renew=False,
        actor_user_id=101,
    )
    with pytest.raises(Exception, match="different authorized user"):
        service.approve_subscription(subscription_id=subscription.id, actor_user_id=101)


def test_only_one_live_subscription_is_allowed_per_lab(db):
    service, plan, _subscription = active_subscription(db, lab_id=14)

    with pytest.raises(Exception, match="already exists"):
        service.create_subscription(
            lab_id=14,
            plan_id=plan.id,
            billing_cycle="MONTHLY",
            starts_at=now_utc(),
            auto_renew=False,
            actor_user_id=303,
        )
