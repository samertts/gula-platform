from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.financial.models import FinBase
from app.payments.orchestration_service import PaymentOrchestrationService, now_utc
from app.payments.schemas import InvoiceLineCreate
from app.payments.service import PaymentService


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


def issue_intent(db):
    payments = PaymentService(db)
    invoice = payments.create_invoice(
        institution_id=12,
        patient_reference="PATIENT-REFERENCE-ONLY",
        due_at=None,
        lines=[
            InvoiceLineCreate(
                description="International consultation",
                service_reference="CONSULT-001",
                quantity=1,
                unit_amount=Decimal("10000.00"),
            )
        ],
        actor_user_id=101,
    )
    return payments.create_intent(
        institution_id=12,
        invoice_id=invoice.id,
        amount=Decimal("10000.00"),
        method="CARD",
        idempotency_key="orchestration-intent-001",
        expires_at=None,
        actor_user_id=101,
    )


def seed_advisory_route(db):
    service = PaymentOrchestrationService(db)
    entity = service.create_entity(
        code="GULA_IQ",
        legal_name="GULA Iraq Entity",
        jurisdiction_code="IQ",
        entity_type="DOMESTIC",
        ledger_namespace="ledger.gula-iq",
        actor_user_id=101,
    )
    service.approve_entity(entity_id=entity.id, actor_user_id=202)
    rail = service.create_rail(
        payment_entity_id=entity.id,
        code="IRAQ_DOMESTIC_SANDBOX",
        rail_type="IRAQ_DOMESTIC",
        jurisdiction_code="IQ",
        supported_currencies=["IQD"],
        actor_user_id=101,
    )
    service.enable_rail_for_advisory_routing(rail_code=rail.code, actor_user_id=202)
    provider = service.register_provider(
        code="IRAQ_PSP_SANDBOX_A",
        display_name="Iraq PSP Sandbox A",
        provider_type="psp",
        payment_entity_id=entity.id,
        rail_code=rail.code,
        jurisdiction_code="IQ",
        supports_refund=True,
        supports_reconciliation=True,
        actor_user_id=101,
    )
    service.approve_provider_for_advisory_routing(provider_code=provider.code, actor_user_id=202)
    rule = service.create_rule(
        payment_entity_id=entity.id,
        rail_code=rail.code,
        provider_code=provider.code,
        rule_version="ROUTE-IQ-PSP-A-V1",
        priority=100,
        minimum_amount=Decimal("1"),
        maximum_amount=Decimal("1000000"),
        currency_code="IQD",
        required_risk_level="MEDIUM",
        service_reference=None,
        estimated_fee_bps=180,
        success_rate_bps=9870,
        latency_ms=300,
        effective_from=now_utc() - timedelta(minutes=1),
        effective_until=None,
        actor_user_id=101,
    )
    service.approve_rule(rule_id=rule.id, actor_user_id=202)
    return service, entity, rail, provider, rule


def test_advisory_router_selects_eligible_sandbox_provider_without_execution(db):
    intent = issue_intent(db)
    service, entity, rail, provider, rule = seed_advisory_route(db)

    decision = service.advise_route(
        payment_intent_id=intent.id,
        payment_entity_id=entity.id,
        correlation_id="corr-advisory-0001",
        service_reference=None,
        actor_user_id=101,
    )

    assert decision.decision == "ADVISORY_SELECT"
    assert decision.provider_code == provider.code
    assert decision.rail_code == rail.code
    assert decision.rule_version == rule.rule_version
    assert decision.reason_codes == ["ADVISORY_ONLY_NO_PROVIDER_CALL"]
    assert provider.environment == "sandbox"
    assert provider.live_approved is False
    assert intent.payment_entity_id == entity.id


def test_orchestration_approval_requires_a_different_authorized_user(db):
    service = PaymentOrchestrationService(db)
    entity = service.create_entity(
        code="GULA_INTL",
        legal_name="GULA International Entity",
        jurisdiction_code="US",
        entity_type="INTERNATIONAL",
        ledger_namespace="ledger.gula-intl",
        actor_user_id=101,
    )

    with pytest.raises(Exception, match="different authorized user"):
        service.approve_entity(entity_id=entity.id, actor_user_id=101)


def test_provider_cannot_cross_entity_boundaries(db):
    service, _entity, rail, _provider, _rule = seed_advisory_route(db)
    other = service.create_entity(
        code="GULA_INTL_X",
        legal_name="GULA International Entity X",
        jurisdiction_code="US",
        entity_type="INTERNATIONAL",
        ledger_namespace="ledger.gula-intl-x",
        actor_user_id=303,
    )
    service.approve_entity(entity_id=other.id, actor_user_id=404)

    with pytest.raises(Exception, match="across payment entities"):
        service.register_provider(
            code="BAD_CROSS_ENTITY_PROVIDER",
            display_name="Bad Provider",
            provider_type="psp",
            payment_entity_id=other.id,
            rail_code=rail.code,
            jurisdiction_code="IQ",
            supports_refund=False,
            supports_reconciliation=True,
            actor_user_id=303,
        )
