"""Provider-, rail-, and currency-agnostic payment routing recommendations.

The service intentionally never invokes a payment provider. It records an
advisory selection that a separately approved provider adapter may use later.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.domain.exceptions import ConflictError, NotFoundError, ServiceError

from .models import (
    PaymentEntity,
    PaymentIntent,
    PaymentProvider,
    PaymentRail,
    PaymentRiskAssessment,
    PaymentRoutingDecision,
    PaymentRoutingRule,
)


def now_utc() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


RISK_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


class PaymentOrchestrationService:
    def __init__(self, db: Session):
        self.db = db

    def _entity(self, entity_id: str) -> PaymentEntity:
        entity = self.db.query(PaymentEntity).filter(PaymentEntity.id == entity_id).first()
        if entity is None:
            raise NotFoundError("Payment entity not found")
        return entity

    def _rail(self, rail_code: str) -> PaymentRail:
        rail = self.db.query(PaymentRail).filter(PaymentRail.code == rail_code).first()
        if rail is None:
            raise NotFoundError("Payment rail not found")
        return rail

    def _provider(self, provider_code: str) -> PaymentProvider:
        provider = self.db.query(PaymentProvider).filter(PaymentProvider.code == provider_code).first()
        if provider is None:
            raise NotFoundError("Payment provider not found")
        return provider

    def create_entity(
        self, *, code: str, legal_name: str, jurisdiction_code: str, entity_type: str,
        ledger_namespace: str, actor_user_id: int,
    ) -> PaymentEntity:
        if self.db.query(PaymentEntity).filter(PaymentEntity.code == code).first():
            raise ConflictError("Payment entity code already exists")
        if self.db.query(PaymentEntity).filter(PaymentEntity.ledger_namespace == ledger_namespace).first():
            raise ConflictError("Ledger namespace is already allocated to another entity")
        entity = PaymentEntity(
            code=code,
            legal_name=legal_name,
            jurisdiction_code=jurisdiction_code,
            entity_type=entity_type,
            ledger_namespace=ledger_namespace,
            status="PENDING_REVIEW",
            created_by=actor_user_id,
            live_operations_approved=False,
        )
        self.db.add(entity)
        self.db.flush()
        return entity

    def approve_entity(self, *, entity_id: str, actor_user_id: int) -> PaymentEntity:
        entity = self._entity(entity_id)
        if entity.status != "PENDING_REVIEW":
            raise ConflictError("Only pending payment entities can be approved")
        if entity.created_by == actor_user_id:
            raise ServiceError("A different authorized user must approve a payment entity", status_code=403)
        entity.status = "ACTIVE"
        entity.approved_by = actor_user_id
        entity.approved_at = now_utc()
        self.db.flush()
        return entity

    def create_rail(
        self, *, payment_entity_id: str, code: str, rail_type: str,
        jurisdiction_code: str, supported_currencies: list[str], actor_user_id: int,
    ) -> PaymentRail:
        entity = self._entity(payment_entity_id)
        if entity.jurisdiction_code != jurisdiction_code and rail_type != "SANDBOX":
            raise ServiceError("A rail jurisdiction must match its owning entity", status_code=409)
        if self.db.query(PaymentRail).filter(PaymentRail.code == code).first():
            raise ConflictError("Payment rail code already exists")
        rail = PaymentRail(
            payment_entity_id=entity.id,
            code=code,
            rail_type=rail_type,
            jurisdiction_code=jurisdiction_code,
            supported_currencies=supported_currencies,
            status="DISABLED",
            created_by=actor_user_id,
            kill_switch_enabled=False,
            live_operations_approved=False,
        )
        self.db.add(rail)
        self.db.flush()
        return rail

    def enable_rail_for_advisory_routing(self, *, rail_code: str, actor_user_id: int) -> PaymentRail:
        rail = self._rail(rail_code)
        if rail.status != "DISABLED":
            raise ConflictError("Only disabled rails can be enabled")
        if rail.created_by == actor_user_id:
            raise ServiceError("A different authorized user must approve a payment rail", status_code=403)
        rail.status = "ACTIVE"
        # Do not change live_operations_approved. This is a non-production selector only.
        self.db.flush()
        return rail

    def register_provider(
        self, *, code: str, display_name: str, provider_type: str, payment_entity_id: str,
        rail_code: str, jurisdiction_code: str, supports_refund: bool,
        supports_reconciliation: bool, actor_user_id: int,
    ) -> PaymentProvider:
        entity = self._entity(payment_entity_id)
        rail = self._rail(rail_code)
        if rail.payment_entity_id != entity.id:
            raise ServiceError("A provider cannot be registered across payment entities", status_code=409)
        if rail.jurisdiction_code != jurisdiction_code:
            raise ServiceError("Provider jurisdiction must match its rail", status_code=409)
        if self.db.query(PaymentProvider).filter(PaymentProvider.code == code).first():
            raise ConflictError("Payment provider code already exists")
        provider = PaymentProvider(
            code=code,
            display_name=display_name,
            provider_type=provider_type,
            environment="sandbox",
            created_by=actor_user_id,
            payment_entity_id=entity.id,
            rail_code=rail.code,
            jurisdiction_code=jurisdiction_code,
            live_approved=False,
            status="PENDING_REVIEW",
            supports_refund=supports_refund,
            supports_reconciliation=supports_reconciliation,
        )
        self.db.add(provider)
        self.db.flush()
        return provider

    def approve_provider_for_advisory_routing(self, *, provider_code: str, actor_user_id: int) -> PaymentProvider:
        provider = self._provider(provider_code)
        if provider.status != "PENDING_REVIEW":
            raise ConflictError("Only pending providers can be approved")
        if provider.created_by == actor_user_id:
            raise ServiceError("A different authorized user must approve a payment provider", status_code=403)
        provider.status = "ACTIVE"
        provider.reviewed_by = actor_user_id
        provider.reviewed_at = now_utc()
        # Explicitly retain the default: live calls remain prohibited.
        provider.live_approved = False
        self.db.flush()
        return provider

    def create_rule(self, *, actor_user_id: int, **fields: Any) -> PaymentRoutingRule:
        entity = self._entity(fields["payment_entity_id"])
        rail = self._rail(fields["rail_code"])
        provider = self._provider(fields["provider_code"])
        if rail.payment_entity_id != entity.id or provider.payment_entity_id != entity.id:
            raise ServiceError("Routing rule entity, rail, and provider must match", status_code=409)
        if provider.rail_code != rail.code:
            raise ServiceError("Routing rule provider must be bound to the selected rail", status_code=409)
        if fields.get("maximum_amount") is not None and fields.get("minimum_amount") is not None:
            if Decimal(fields["maximum_amount"]) < Decimal(fields["minimum_amount"]):
                raise ServiceError("Routing rule maximum amount cannot be lower than minimum amount")
        if fields.get("effective_until") is not None and as_utc(fields["effective_until"]) <= as_utc(fields["effective_from"]):
            raise ServiceError("Routing rule expiration must be later than effective time")
        if self.db.query(PaymentRoutingRule).filter(PaymentRoutingRule.rule_version == fields["rule_version"]).first():
            raise ConflictError("Routing rule version already exists")
        rule = PaymentRoutingRule(**fields, active=False, created_by=actor_user_id, approved_by=None)
        self.db.add(rule)
        self.db.flush()
        return rule

    def approve_rule(self, *, rule_id: str, actor_user_id: int) -> PaymentRoutingRule:
        rule = self.db.query(PaymentRoutingRule).filter(PaymentRoutingRule.id == rule_id).first()
        if rule is None:
            raise NotFoundError("Payment routing rule not found")
        if rule.active:
            raise ConflictError("Payment routing rule is already active")
        if rule.created_by == actor_user_id:
            raise ServiceError("A different authorized user must approve a routing rule", status_code=403)
        if as_utc(rule.effective_from) > now_utc():
            raise ServiceError("Routing rule cannot be approved before its effective time", status_code=409)
        if rule.effective_until is not None and as_utc(rule.effective_until) <= now_utc():
            raise ServiceError("Routing rule is already expired", status_code=409)
        rule.active = True
        rule.approved_by = actor_user_id
        self.db.flush()
        return rule

    def advise_route(
        self, *, payment_intent_id: str, payment_entity_id: str,
        correlation_id: str, service_reference: str | None, actor_user_id: int,
    ) -> PaymentRoutingDecision:
        intent = self.db.query(PaymentIntent).filter(PaymentIntent.id == payment_intent_id).first()
        if intent is None:
            raise NotFoundError("Payment intent not found")
        entity = self._entity(payment_entity_id)
        if entity.status != "ACTIVE":
            raise ServiceError("Payment entity is not approved for advisory routing", status_code=409)
        if intent.payment_entity_id not in {None, entity.id}:
            raise ServiceError("Payment intent is already bound to a different payment entity", status_code=409)
        intent.payment_entity_id = entity.id
        now = now_utc()
        latest_risk = (
            self.db.query(PaymentRiskAssessment)
            .filter(PaymentRiskAssessment.payment_intent_id == intent.id)
            .order_by(PaymentRiskAssessment.created_at.desc())
            .first()
        )
        risk_level = latest_risk.risk_level if latest_risk else "LOW"
        rules = (
            self.db.query(PaymentRoutingRule)
            .filter(
                PaymentRoutingRule.payment_entity_id == entity.id,
                PaymentRoutingRule.active.is_(True),
                PaymentRoutingRule.effective_from <= now,
                (PaymentRoutingRule.effective_until.is_(None) | (PaymentRoutingRule.effective_until > now)),
            )
            .all()
        )
        candidates: list[dict[str, Any]] = []
        for rule in rules:
            rail = self._rail(rule.rail_code)
            provider = self._provider(rule.provider_code)
            exclusions: list[str] = []
            if rail.status != "ACTIVE" or rail.kill_switch_enabled:
                exclusions.append("RAIL_DISABLED_OR_KILL_SWITCH")
            if intent.currency not in (rail.supported_currencies or []):
                exclusions.append("RAIL_CURRENCY_UNSUPPORTED")
            if provider.status != "ACTIVE":
                exclusions.append("PROVIDER_NOT_ACTIVE")
            if provider.live_approved:
                exclusions.append("LIVE_PROVIDER_NOT_ALLOWED_IN_ADVISORY_MODE")
            if rule.currency_code and rule.currency_code != intent.currency:
                exclusions.append("RULE_CURRENCY_MISMATCH")
            if rule.minimum_amount is not None and Decimal(intent.amount) < Decimal(rule.minimum_amount):
                exclusions.append("AMOUNT_BELOW_RULE_MINIMUM")
            if rule.maximum_amount is not None and Decimal(intent.amount) > Decimal(rule.maximum_amount):
                exclusions.append("AMOUNT_ABOVE_RULE_MAXIMUM")
            if rule.service_reference and rule.service_reference != service_reference:
                exclusions.append("SERVICE_REFERENCE_MISMATCH")
            if rule.required_risk_level and RISK_ORDER[risk_level] > RISK_ORDER[rule.required_risk_level]:
                exclusions.append("RISK_LEVEL_REQUIRES_REVIEW")
            score = (
                Decimal(rule.success_rate_bps)
                - Decimal(rule.estimated_fee_bps) * Decimal("2")
                - Decimal(min(rule.latency_ms or 0, 60000)) / Decimal("10")
                + Decimal(max(0, 10000 - rule.priority)) / Decimal("100")
            )
            candidates.append({
                "rail_code": rail.code,
                "provider_code": provider.code,
                "rule_version": rule.rule_version,
                "score": str(score),
                "excluded": exclusions,
            })

        eligible = [item for item in candidates if not item["excluded"]]
        selected = max(eligible, key=lambda item: Decimal(item["score"])) if eligible else None
        if selected is None:
            decision_name, reasons, score = "NO_ELIGIBLE_ROUTE", ["NO_ELIGIBLE_ADVISORY_ROUTE"], None
        elif RISK_ORDER[risk_level] >= RISK_ORDER["HIGH"]:
            decision_name, reasons, score = "MANUAL_REVIEW", ["HIGH_RISK_REQUIRES_HUMAN_REVIEW"], Decimal(selected["score"])
        else:
            decision_name, reasons, score = "ADVISORY_SELECT", ["ADVISORY_ONLY_NO_PROVIDER_CALL"], Decimal(selected["score"])
        decision = PaymentRoutingDecision(
            payment_intent_id=intent.id,
            payment_entity_id=entity.id,
            rail_code=selected["rail_code"] if selected else None,
            provider_code=selected["provider_code"] if selected else None,
            correlation_id=correlation_id,
            decision=decision_name,
            score=score,
            reason_codes=reasons,
            evaluated_candidates=candidates,
            rule_version=selected["rule_version"] if selected else None,
        )
        self.db.add(decision)
        self.db.flush()
        return decision
