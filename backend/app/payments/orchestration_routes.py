"""Administrative API for advisory-only multi-rail payment orchestration."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.exceptions import NotFoundError
from app.security.dependencies import require_permission

from .models import PaymentIntent
from .orchestration_schemas import (
    PaymentEntityCreate,
    PaymentProviderCreate,
    PaymentRailCreate,
    RoutingDecisionCreate,
    RoutingDecisionResponse,
    RoutingRuleCreate,
)
from .orchestration_service import PaymentOrchestrationService
from .service import PaymentService

router = APIRouter(prefix="/payments/orchestration", tags=["GULA Payment Orchestration"])
DbSession = Annotated[Session, Depends(get_db)]


def _commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _decision_response(decision) -> RoutingDecisionResponse:
    return RoutingDecisionResponse(
        id=decision.id,
        payment_intent_id=decision.payment_intent_id,
        payment_entity_id=decision.payment_entity_id,
        rail_code=decision.rail_code,
        provider_code=decision.provider_code,
        decision=decision.decision,
        score=decision.score,
        reason_codes=decision.reason_codes,
        evaluated_candidates=decision.evaluated_candidates,
        rule_version=decision.rule_version,
        correlation_id=decision.correlation_id,
    )


@router.post("/entities", status_code=status.HTTP_201_CREATED)
def create_payment_entity(
    payload: PaymentEntityCreate,
    db: DbSession,
    current_user=Depends(require_permission("payments:orchestration:manage")),
):
    entity = PaymentOrchestrationService(db).create_entity(actor_user_id=current_user.id, **payload.model_dump())
    _commit(db)
    return {"id": entity.id, "code": entity.code, "status": entity.status, "live_operations_approved": False}


@router.post("/entities/{entity_id}/approve")
def approve_payment_entity(
    entity_id: str,
    db: DbSession,
    current_user=Depends(require_permission("payments:orchestration:manage")),
):
    entity = PaymentOrchestrationService(db).approve_entity(entity_id=entity_id, actor_user_id=current_user.id)
    _commit(db)
    return {"id": entity.id, "code": entity.code, "status": entity.status, "live_operations_approved": entity.live_operations_approved}


@router.post("/rails", status_code=status.HTTP_201_CREATED)
def create_payment_rail(
    payload: PaymentRailCreate,
    db: DbSession,
    current_user=Depends(require_permission("payments:orchestration:manage")),
):
    rail = PaymentOrchestrationService(db).create_rail(actor_user_id=current_user.id, **payload.model_dump())
    _commit(db)
    return {"id": rail.id, "code": rail.code, "status": rail.status, "kill_switch_enabled": rail.kill_switch_enabled}


@router.post("/rails/{rail_code}/enable-advisory")
def enable_rail_for_advisory_routing(
    rail_code: str,
    db: DbSession,
    current_user=Depends(require_permission("payments:orchestration:manage")),
):
    rail = PaymentOrchestrationService(db).enable_rail_for_advisory_routing(rail_code=rail_code, actor_user_id=current_user.id)
    _commit(db)
    return {"id": rail.id, "code": rail.code, "status": rail.status, "live_operations_approved": rail.live_operations_approved}


@router.post("/providers", status_code=status.HTTP_201_CREATED)
def register_payment_provider(
    payload: PaymentProviderCreate,
    db: DbSession,
    current_user=Depends(require_permission("payments:orchestration:manage")),
):
    provider = PaymentOrchestrationService(db).register_provider(actor_user_id=current_user.id, **payload.model_dump())
    _commit(db)
    return {"id": provider.id, "code": provider.code, "status": provider.status, "environment": provider.environment, "live_approved": provider.live_approved}


@router.post("/providers/{provider_code}/approve-advisory")
def approve_provider_for_advisory_routing(
    provider_code: str,
    db: DbSession,
    current_user=Depends(require_permission("payments:orchestration:manage")),
):
    provider = PaymentOrchestrationService(db).approve_provider_for_advisory_routing(provider_code=provider_code, actor_user_id=current_user.id)
    _commit(db)
    return {"id": provider.id, "code": provider.code, "status": provider.status, "live_approved": provider.live_approved}


@router.post("/rules", status_code=status.HTTP_201_CREATED)
def create_routing_rule(
    payload: RoutingRuleCreate,
    db: DbSession,
    current_user=Depends(require_permission("payments:orchestration:manage")),
):
    rule = PaymentOrchestrationService(db).create_rule(actor_user_id=current_user.id, **payload.model_dump())
    _commit(db)
    return {"id": rule.id, "rule_version": rule.rule_version, "active": rule.active}


@router.post("/rules/{rule_id}/approve")
def approve_routing_rule(
    rule_id: str,
    db: DbSession,
    current_user=Depends(require_permission("payments:orchestration:manage")),
):
    rule = PaymentOrchestrationService(db).approve_rule(rule_id=rule_id, actor_user_id=current_user.id)
    _commit(db)
    return {"id": rule.id, "rule_version": rule.rule_version, "active": rule.active}


@router.post("/intents/{payment_intent_id}/advise", response_model=RoutingDecisionResponse, status_code=status.HTTP_201_CREATED)
def advise_payment_route(
    payment_intent_id: str,
    payload: RoutingDecisionCreate,
    db: DbSession,
    current_user=Depends(require_permission("payments:orchestration:route")),
):
    intent = db.query(PaymentIntent).filter(PaymentIntent.id == payment_intent_id).first()
    if intent is None:
        raise NotFoundError("Payment intent not found")
    PaymentService(db).assert_institution_access(current_user, intent.institution_id)
    decision = PaymentOrchestrationService(db).advise_route(
        payment_intent_id=payment_intent_id,
        payment_entity_id=payload.payment_entity_id,
        correlation_id=payload.correlation_id,
        service_reference=payload.service_reference,
        actor_user_id=current_user.id,
    )
    _commit(db)
    return _decision_response(decision)
