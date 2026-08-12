"""API for institutional subscription billing and entitlement usage."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.exceptions import NotFoundError
from app.security.dependencies import require_permission

from .service import PaymentService
from .subscription_models import PlatformSubscription
from .subscription_schemas import (
    PlatformSubscriptionCreate,
    SubscriptionCycleGenerate,
    SubscriptionCycleResponse,
    SubscriptionPlanCreate,
    SubscriptionUsageRecord,
    UsageDecisionResponse,
)
from .subscription_service import InstitutionalSubscriptionService

router = APIRouter(prefix="/payments/subscriptions", tags=["GULA Institutional Subscriptions"])
DbSession = Annotated[Session, Depends(get_db)]


def _commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _cycle_response(cycle) -> SubscriptionCycleResponse:
    return SubscriptionCycleResponse(
        id=cycle.id,
        subscription_id=cycle.subscription_id,
        cycle_key=cycle.cycle_key,
        period_start=cycle.period_start,
        period_end=cycle.period_end,
        due_at=cycle.due_at,
        amount=cycle.amount,
        currency=cycle.currency,
        status=cycle.status,
    )


def _subscription_for_lab(db: Session, subscription_id: str, current_user) -> PlatformSubscription:
    subscription = db.query(PlatformSubscription).filter(PlatformSubscription.id == subscription_id).first()
    if subscription is None:
        raise NotFoundError("Platform subscription not found")
    PaymentService(db).assert_institution_access(current_user, subscription.lab_id)
    return subscription


@router.post("/plans", status_code=status.HTTP_201_CREATED)
def create_subscription_plan(
    payload: SubscriptionPlanCreate,
    db: DbSession,
    current_user=Depends(require_permission("subscriptions:manage")),
):
    plan = InstitutionalSubscriptionService(db).create_plan(actor_user_id=current_user.id, **payload.model_dump())
    _commit(db)
    return {"id": plan.id, "plan_code": plan.plan_code, "version": plan.version, "status": plan.status}


@router.post("/plans/{plan_id}/approve")
def approve_subscription_plan(
    plan_id: str,
    db: DbSession,
    current_user=Depends(require_permission("subscriptions:manage")),
):
    plan = InstitutionalSubscriptionService(db).approve_plan(plan_id=plan_id, actor_user_id=current_user.id)
    _commit(db)
    return {"id": plan.id, "plan_code": plan.plan_code, "version": plan.version, "status": plan.status}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_platform_subscription(
    payload: PlatformSubscriptionCreate,
    db: DbSession,
    current_user=Depends(require_permission("subscriptions:manage")),
):
    subscription = InstitutionalSubscriptionService(db).create_subscription(actor_user_id=current_user.id, **payload.model_dump())
    _commit(db)
    return {"id": subscription.id, "lab_id": subscription.lab_id, "status": subscription.status, "plan_code": subscription.plan_code}


@router.post("/{subscription_id}/approve")
def approve_platform_subscription(
    subscription_id: str,
    db: DbSession,
    current_user=Depends(require_permission("subscriptions:manage")),
):
    subscription = InstitutionalSubscriptionService(db).approve_subscription(subscription_id=subscription_id, actor_user_id=current_user.id)
    _commit(db)
    return {"id": subscription.id, "status": subscription.status, "next_billing_at": subscription.next_billing_at}


@router.get("/{subscription_id}")
def get_platform_subscription(
    subscription_id: str,
    db: DbSession,
    current_user=Depends(require_permission("subscriptions:read")),
):
    subscription = _subscription_for_lab(db, subscription_id, current_user)
    return {
        "id": subscription.id,
        "lab_id": subscription.lab_id,
        "plan_code": subscription.plan_code,
        "plan_version": subscription.plan_version,
        "status": subscription.status,
        "billing_cycle": subscription.billing_cycle,
        "current_period_start": subscription.current_period_start,
        "current_period_end": subscription.current_period_end,
        "next_billing_at": subscription.next_billing_at,
        "auto_renew": subscription.auto_renew,
    }


@router.post("/{subscription_id}/cycles/current", response_model=SubscriptionCycleResponse, status_code=status.HTTP_201_CREATED)
def generate_current_subscription_cycle(
    subscription_id: str,
    payload: SubscriptionCycleGenerate,
    db: DbSession,
    current_user=Depends(require_permission("subscriptions:manage")),
):
    cycle = InstitutionalSubscriptionService(db).generate_current_cycle(
        subscription_id=subscription_id,
        as_of=payload.as_of,
        actor_user_id=current_user.id,
    )
    _commit(db)
    return _cycle_response(cycle)


@router.post("/{subscription_id}/usage", response_model=UsageDecisionResponse)
def record_subscription_usage(
    subscription_id: str,
    payload: SubscriptionUsageRecord,
    db: DbSession,
    current_user=Depends(require_permission("subscriptions:usage")),
):
    _subscription_for_lab(db, subscription_id, current_user)
    decision = InstitutionalSubscriptionService(db).record_usage(
        subscription_id=subscription_id,
        actor_user_id=current_user.id,
        **payload.model_dump(),
    )
    _commit(db)
    return UsageDecisionResponse(**decision)
