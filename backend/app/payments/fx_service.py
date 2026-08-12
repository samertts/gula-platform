"""Currency and FX quote engine.

This module produces transparent reference quotes only. It does not exchange
funds, hold balances, call a bank, or authorize an external payment provider.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_UP
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.domain.exceptions import ConflictError, NotFoundError, ServiceError

from .models import CurrencyDefinition, FxFeePolicy, FxQuote, FxRateSnapshot, PaymentRiskAssessment
from .service import PLATFORM_ROLES, money

ROUNDING = {
    "HALF_UP": ROUND_HALF_UP,
    "HALF_EVEN": ROUND_HALF_EVEN,
    "DOWN": ROUND_DOWN,
    "UP": ROUND_UP,
}
MAX_RATE_AGE = timedelta(hours=24)


def now_utc() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class FxService:
    def __init__(self, db: Session):
        self.db = db

    def assert_institution_access(self, actor: Any, institution_id: int) -> None:
        if getattr(actor, "role", None) in PLATFORM_ROLES:
            return
        if getattr(actor, "lab_id", None) != institution_id:
            raise ServiceError("Cross-institution FX access is not allowed", status_code=403)

    def _currency(self, code: str) -> CurrencyDefinition:
        currency = self.db.query(CurrencyDefinition).filter(CurrencyDefinition.code == code.upper()).first()
        if currency is None:
            raise NotFoundError(f"Currency {code.upper()} is not registered")
        if not currency.enabled:
            raise ServiceError(f"Currency {code.upper()} is disabled", status_code=409)
        return currency

    def _round(self, amount: Decimal, currency: CurrencyDefinition) -> Decimal:
        quantizer = Decimal(1).scaleb(-currency.minor_unit)
        return Decimal(amount).quantize(quantizer, rounding=ROUNDING[currency.rounding_mode])

    def create_currency(
        self,
        *,
        code: str,
        display_name: str,
        minor_unit: int,
        rounding_mode: str,
        fx_quote_enabled: bool,
    ) -> CurrencyDefinition:
        normalized = code.upper()
        existing = self.db.query(CurrencyDefinition).filter(CurrencyDefinition.code == normalized).first()
        if existing is not None:
            raise ConflictError("Currency code already exists")
        currency = CurrencyDefinition(
            code=normalized,
            display_name=display_name,
            minor_unit=minor_unit,
            rounding_mode=rounding_mode,
            fx_quote_enabled=fx_quote_enabled,
        )
        self.db.add(currency)
        self.db.flush()
        return currency

    def create_rate_snapshot(
        self,
        *,
        source_code: str,
        source_reference: str,
        source_digest: str | None,
        rate_version: str,
        base_currency: str,
        quote_currency: str,
        reference_rate: Decimal,
        published_at: datetime,
        actor_user_id: int,
    ) -> FxRateSnapshot:
        base = self._currency(base_currency)
        quote = self._currency(quote_currency)
        if base.code == quote.code:
            raise ServiceError("FX rate currencies must differ")
        if Decimal(reference_rate) <= 0:
            raise ServiceError("FX reference rate must be positive")
        duplicate = (
            self.db.query(FxRateSnapshot)
            .filter(
                FxRateSnapshot.source_code == source_code,
                FxRateSnapshot.source_reference == source_reference,
                FxRateSnapshot.base_currency == base.code,
                FxRateSnapshot.quote_currency == quote.code,
                FxRateSnapshot.rate_version == rate_version,
            )
            .first()
        )
        if duplicate is not None:
            raise ConflictError("The supplied source rate snapshot already exists")
        snapshot = FxRateSnapshot(
            source_code=source_code,
            source_reference=source_reference,
            source_digest=source_digest,
            rate_version=rate_version,
            base_currency=base.code,
            quote_currency=quote.code,
            reference_rate=Decimal(reference_rate),
            published_at=as_utc(published_at),
            verification_status="PENDING_REVIEW",
            created_by=actor_user_id,
        )
        self.db.add(snapshot)
        self.db.flush()
        return snapshot

    def verify_rate_snapshot(self, *, snapshot_id: str, actor_user_id: int) -> FxRateSnapshot:
        snapshot = self.db.query(FxRateSnapshot).filter(FxRateSnapshot.id == snapshot_id).first()
        if snapshot is None:
            raise NotFoundError("FX rate snapshot not found")
        if snapshot.verification_status != "PENDING_REVIEW":
            raise ConflictError("Only pending rate snapshots can be verified")
        if snapshot.created_by == actor_user_id:
            raise ServiceError("A different authorized user must verify a rate snapshot", status_code=403)
        # Source data must be independently reviewed before it can drive quotes.
        snapshot.verification_status = "VERIFIED"
        snapshot.verified_by = actor_user_id
        snapshot.verified_at = now_utc()
        return snapshot

    def create_fee_policy(
        self,
        *,
        institution_id: int | None,
        policy_version: str,
        base_currency: str | None,
        quote_currency: str | None,
        service_reference: str | None,
        provider_code: str | None,
        fee_bps: int,
        minimum_fee: Decimal,
        maximum_fee: Decimal | None,
        currency: str,
        effective_from: datetime,
        effective_until: datetime | None,
        active: bool,
        actor_user_id: int,
    ) -> FxFeePolicy:
        if effective_until is not None and as_utc(effective_until) <= as_utc(effective_from):
            raise ServiceError("Fee policy expiration must be later than its effective time")
        if maximum_fee is not None and money(maximum_fee) < money(minimum_fee):
            raise ServiceError("Maximum fee cannot be smaller than minimum fee")
        self._currency(currency)
        if base_currency:
            self._currency(base_currency)
        if quote_currency:
            self._currency(quote_currency)
        policy = FxFeePolicy(
            institution_id=institution_id,
            policy_version=policy_version,
            base_currency=base_currency,
            quote_currency=quote_currency,
            service_reference=service_reference,
            provider_code=provider_code,
            fee_bps=fee_bps,
            minimum_fee=money(minimum_fee),
            maximum_fee=money(maximum_fee) if maximum_fee is not None else None,
            currency=currency.upper(),
            effective_from=as_utc(effective_from),
            effective_until=as_utc(effective_until) if effective_until else None,
            active=False,
            created_by=actor_user_id,
            approved_by=None,
        )
        self.db.add(policy)
        self.db.flush()
        return policy

    def activate_fee_policy(self, *, policy_id: str, actor_user_id: int) -> FxFeePolicy:
        policy = self.db.query(FxFeePolicy).filter(FxFeePolicy.id == policy_id).first()
        if policy is None:
            raise NotFoundError("FX fee policy not found")
        if policy.active:
            raise ConflictError("FX fee policy is already active")
        if policy.created_by == actor_user_id:
            raise ServiceError("A different authorized user must approve an FX fee policy", status_code=403)
        if as_utc(policy.effective_from) > now_utc():
            raise ServiceError("FX fee policy cannot be activated before its effective time", status_code=409)
        if policy.effective_until is not None and as_utc(policy.effective_until) <= now_utc():
            raise ServiceError("FX fee policy is already expired", status_code=409)
        policy.active = True
        policy.approved_by = actor_user_id
        self.db.flush()
        return policy

    def _select_fee_policy(
        self,
        institution_id: int,
        base_currency: str,
        quote_currency: str,
        service_reference: str | None,
        provider_code: str | None,
    ) -> FxFeePolicy | None:
        now = now_utc()
        candidates = (
            self.db.query(FxFeePolicy)
            .filter(
                FxFeePolicy.active.is_(True),
                FxFeePolicy.currency == quote_currency,
                FxFeePolicy.effective_from <= now,
                (FxFeePolicy.effective_until.is_(None) | (FxFeePolicy.effective_until > now)),
            )
            .all()
        )

        def matches(policy: FxFeePolicy) -> bool:
            return (
                policy.institution_id in {None, institution_id}
                and policy.base_currency in {None, base_currency}
                and policy.quote_currency in {None, quote_currency}
                and policy.service_reference in {None, service_reference}
                and policy.provider_code in {None, provider_code}
            )

        def specificity(policy: FxFeePolicy) -> tuple[int, int]:
            fields = (policy.institution_id, policy.base_currency, policy.quote_currency, policy.service_reference, policy.provider_code)
            return (sum(value is not None for value in fields), int(policy.institution_id == institution_id))

        matching = [policy for policy in candidates if matches(policy)]
        return max(matching, key=specificity) if matching else None

    def _latest_verified_rate(self, base_currency: str, quote_currency: str) -> FxRateSnapshot:
        snapshot = (
            self.db.query(FxRateSnapshot)
            .filter(
                FxRateSnapshot.base_currency == base_currency,
                FxRateSnapshot.quote_currency == quote_currency,
                FxRateSnapshot.verification_status == "VERIFIED",
            )
            .order_by(FxRateSnapshot.published_at.desc(), FxRateSnapshot.created_at.desc())
            .first()
        )
        if snapshot is None:
            raise NotFoundError("No verified official FX rate is available for this currency pair")
        if now_utc() - as_utc(snapshot.published_at) > MAX_RATE_AGE:
            raise ServiceError("STALE_RATE: a fresh verified FX rate is required before issuing a quote", status_code=409)
        return snapshot

    def create_quote(
        self,
        *,
        institution_id: int,
        invoice_id: str | None,
        base_currency: str,
        quote_currency: str,
        base_amount: Decimal,
        service_reference: str | None,
        provider_code: str | None,
        quote_ttl_seconds: int,
        actor_user_id: int,
    ) -> tuple[FxQuote, PaymentRiskAssessment]:
        base = self._currency(base_currency)
        quote = self._currency(quote_currency)
        if not base.fx_quote_enabled or not quote.fx_quote_enabled:
            raise ServiceError("FX quoting is disabled for one or both currencies", status_code=409)
        if base.code == quote.code:
            raise ServiceError("FX quoting requires different currencies")
        normalized_base_amount = self._round(Decimal(base_amount), base)
        if normalized_base_amount <= 0:
            raise ServiceError("FX quote base amount must be positive")
        snapshot = self._latest_verified_rate(base.code, quote.code)
        policy = self._select_fee_policy(
            institution_id, base.code, quote.code, service_reference, provider_code
        )
        converted = self._round(normalized_base_amount * Decimal(snapshot.reference_rate), quote)
        fee = Decimal("0.00")
        if policy is not None:
            fee = self._round(converted * Decimal(policy.fee_bps) / Decimal(10_000), quote)
            fee = max(fee, self._round(policy.minimum_fee, quote))
            if policy.maximum_fee is not None:
                fee = min(fee, self._round(policy.maximum_fee, quote))
        total = self._round(converted + fee, quote)
        quote_record = FxQuote(
            institution_id=institution_id,
            invoice_id=invoice_id,
            rate_snapshot_id=snapshot.id,
            fee_policy_id=policy.id if policy else None,
            base_currency=base.code,
            quote_currency=quote.code,
            base_amount=normalized_base_amount,
            reference_rate=snapshot.reference_rate,
            base_converted_amount=converted,
            administrative_fee_amount=fee,
            provider_fee_amount=Decimal("0.00"),
            total_quote_amount=total,
            status="CREATED",
            expires_at=now_utc() + timedelta(seconds=quote_ttl_seconds),
            created_by=actor_user_id,
        )
        self.db.add(quote_record)
        self.db.flush()
        risk = self._create_non_blocking_risk_assessment(quote_record)
        return quote_record, risk

    def _create_non_blocking_risk_assessment(self, quote: FxQuote) -> PaymentRiskAssessment:
        total = Decimal(quote.total_quote_amount)
        if total >= Decimal("10000000"):
            score, level, reasons = Decimal("75.00"), "HIGH", ["HIGH_QUOTE_VALUE"]
        elif total >= Decimal("1000000"):
            score, level, reasons = Decimal("35.00"), "MEDIUM", ["ELEVATED_QUOTE_VALUE"]
        else:
            score, level, reasons = Decimal("5.00"), "LOW", []
        assessment = PaymentRiskAssessment(
            institution_id=quote.institution_id,
            fx_quote_id=quote.id,
            risk_score=score,
            risk_level=level,
            recommended_action="REVIEW" if level in {"HIGH", "CRITICAL"} else "ALLOW",
            reason_codes=reasons,
        )
        self.db.add(assessment)
        return assessment

    def lock_quote(self, *, quote_id: str, institution_id: int, actor_user_id: int) -> FxQuote:
        quote = (
            self.db.query(FxQuote)
            .filter(FxQuote.id == quote_id, FxQuote.institution_id == institution_id)
            .first()
        )
        if quote is None:
            raise NotFoundError("FX quote not found")
        if quote.status != "CREATED":
            raise ConflictError("Only newly created FX quotes can be locked")
        if as_utc(quote.expires_at) <= now_utc():
            quote.status = "EXPIRED"
            raise ServiceError("REQUOTE_REQUIRED: FX quote has expired", status_code=409)
        quote.status = "LOCKED"
        quote.locked_at = now_utc()
        return quote

    def quote_summary(self, quote: FxQuote) -> dict[str, Any]:
        snapshot = self.db.query(FxRateSnapshot).filter(FxRateSnapshot.id == quote.rate_snapshot_id).one()
        return {
            "id": quote.id,
            "status": quote.status,
            "base_currency": quote.base_currency,
            "base_amount": quote.base_amount,
            "quote_currency": quote.quote_currency,
            "reference_rate": quote.reference_rate,
            "base_converted_amount": quote.base_converted_amount,
            "administrative_fee_amount": quote.administrative_fee_amount,
            "provider_fee_amount": quote.provider_fee_amount,
            "total_quote_amount": quote.total_quote_amount,
            "rate_version": snapshot.rate_version,
            "source_code": snapshot.source_code,
            "expires_at": quote.expires_at,
        }
