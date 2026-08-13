from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app._compat import UTC
from app.financial.models import FinBase
from app.payments.fx_service import FxService, now_utc


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


def seed_currencies(service: FxService):
    service.create_currency(
        code="USD", display_name="US Dollar", minor_unit=2, rounding_mode="HALF_UP", fx_quote_enabled=True
    )
    service.create_currency(
        code="IQD", display_name="Iraqi Dinar", minor_unit=0, rounding_mode="HALF_UP", fx_quote_enabled=True
    )


def verified_usd_iqd_rate(service: FxService, *, published_at=None):
    snapshot = service.create_rate_snapshot(
        source_code="CBI_PUBLISHED_RATE",
        source_reference="https://cbi.iq/page/144#rate-file",
        source_digest="test-digest",
        rate_version="FX-TEST-001",
        base_currency="USD",
        quote_currency="IQD",
        reference_rate=Decimal("1310.0000000000"),
        published_at=published_at or now_utc(),
        actor_user_id=100,
    )
    service.verify_rate_snapshot(snapshot_id=snapshot.id, actor_user_id=200)
    return snapshot


def approved_default_fee_policy(service: FxService):
    policy = service.create_fee_policy(
        institution_id=None,
        policy_version="FX-FEE-DEFAULT-200BPS",
        base_currency="USD",
        quote_currency="IQD",
        service_reference=None,
        provider_code=None,
        fee_bps=200,
        minimum_fee=Decimal("0"),
        maximum_fee=None,
        currency="IQD",
        effective_from=now_utc() - timedelta(minutes=1),
        effective_until=None,
        active=False,
        actor_user_id=100,
    )
    service.activate_fee_policy(policy_id=policy.id, actor_user_id=200)
    return policy


def test_fx_quote_separates_reference_rate_and_administrative_fee(db):
    service = FxService(db)
    seed_currencies(service)
    verified_usd_iqd_rate(service)
    approved_default_fee_policy(service)

    quote, assessment = service.create_quote(
        institution_id=12,
        invoice_id=None,
        base_currency="USD",
        quote_currency="IQD",
        base_amount=Decimal("100.00"),
        service_reference=None,
        provider_code=None,
        quote_ttl_seconds=600,
        actor_user_id=101,
    )
    db.flush()

    assert quote.base_converted_amount == Decimal("131000")
    assert quote.administrative_fee_amount == Decimal("2620")
    assert quote.provider_fee_amount == Decimal("0")
    assert quote.total_quote_amount == Decimal("133620")
    assert assessment.risk_level == "LOW"
    assert service.lock_quote(quote_id=quote.id, institution_id=12, actor_user_id=101).status == "LOCKED"


def test_rate_snapshot_requires_independent_verification(db):
    service = FxService(db)
    seed_currencies(service)
    snapshot = service.create_rate_snapshot(
        source_code="CBI_PUBLISHED_RATE",
        source_reference="https://cbi.iq/page/144#another-rate-file",
        source_digest=None,
        rate_version="FX-TEST-002",
        base_currency="USD",
        quote_currency="IQD",
        reference_rate=Decimal("1310"),
        published_at=now_utc(),
        actor_user_id=100,
    )

    with pytest.raises(Exception, match="different authorized user"):
        service.verify_rate_snapshot(snapshot_id=snapshot.id, actor_user_id=100)


def test_stale_rate_requires_requote_instead_of_silent_fallback(db):
    service = FxService(db)
    seed_currencies(service)
    verified_usd_iqd_rate(service, published_at=now_utc() - timedelta(hours=25))
    approved_default_fee_policy(service)

    with pytest.raises(Exception, match="STALE_RATE"):
        service.create_quote(
            institution_id=12,
            invoice_id=None,
            base_currency="USD",
            quote_currency="IQD",
            base_amount=Decimal("50.00"),
            service_reference=None,
            provider_code=None,
            quote_ttl_seconds=600,
            actor_user_id=101,
        )


def test_fee_policy_requires_independent_activation(db):
    service = FxService(db)
    seed_currencies(service)
    policy = service.create_fee_policy(
        institution_id=None,
        policy_version="FX-FEE-SELF-APPROVAL-BLOCKED",
        base_currency="USD",
        quote_currency="IQD",
        service_reference=None,
        provider_code=None,
        fee_bps=200,
        minimum_fee=Decimal("0"),
        maximum_fee=None,
        currency="IQD",
        effective_from=now_utc() - timedelta(minutes=1),
        effective_until=None,
        active=False,
        actor_user_id=100,
    )

    with pytest.raises(Exception, match="different authorized user"):
        service.activate_fee_policy(policy_id=policy.id, actor_user_id=100)
