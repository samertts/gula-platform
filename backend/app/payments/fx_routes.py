"""Authenticated non-production API for GULA currency and FX reference quotes."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.exceptions import NotFoundError
from app.security.dependencies import require_permission

from .fx_schemas import (
    CurrencyDefinitionCreate,
    FxFeePolicyCreate,
    FxQuoteCreate,
    FxQuoteResponse,
    FxRateSnapshotCreate,
    RiskAssessmentResponse,
)
from .fx_service import FxService
from .models import CurrencyDefinition, PaymentInvoice

router = APIRouter(prefix="/payments/fx", tags=["GULA Currency & FX"])
DbSession = Annotated[Session, Depends(get_db)]


def _commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _actor_institution(current_user, db: Session, invoice_id: str | None = None) -> int:
    if invoice_id:
        invoice = db.query(PaymentInvoice).filter(PaymentInvoice.id == invoice_id).first()
        if invoice is None:
            raise NotFoundError("Payment invoice not found")
        FxService(db).assert_institution_access(current_user, invoice.institution_id)
        return invoice.institution_id
    if current_user.lab_id is None:
        raise NotFoundError("An active institution is required for this FX operation")
    return current_user.lab_id


@router.get("/currencies")
def list_currencies(
    db: DbSession,
    current_user=Depends(require_permission("payments:fx:quote")),
):
    currencies = db.query(CurrencyDefinition).order_by(CurrencyDefinition.code).all()
    return [
        {
            "code": currency.code,
            "display_name": currency.display_name,
            "minor_unit": currency.minor_unit,
            "rounding_mode": currency.rounding_mode,
            "enabled": currency.enabled,
            "fx_quote_enabled": currency.fx_quote_enabled,
        }
        for currency in currencies
    ]


@router.post("/currencies", status_code=status.HTTP_201_CREATED)
def create_currency(
    payload: CurrencyDefinitionCreate,
    db: DbSession,
    current_user=Depends(require_permission("payments:fx:manage")),
):
    currency = FxService(db).create_currency(**payload.model_dump())
    _commit(db)
    return {
        "code": currency.code,
        "display_name": currency.display_name,
        "minor_unit": currency.minor_unit,
        "rounding_mode": currency.rounding_mode,
        "fx_quote_enabled": currency.fx_quote_enabled,
    }


@router.post("/rate-snapshots", status_code=status.HTTP_201_CREATED)
def create_rate_snapshot(
    payload: FxRateSnapshotCreate,
    db: DbSession,
    current_user=Depends(require_permission("payments:fx:manage")),
):
    snapshot = FxService(db).create_rate_snapshot(actor_user_id=current_user.id, **payload.model_dump())
    _commit(db)
    return {
        "id": snapshot.id,
        "verification_status": snapshot.verification_status,
        "source_code": snapshot.source_code,
        "rate_version": snapshot.rate_version,
        "base_currency": snapshot.base_currency,
        "quote_currency": snapshot.quote_currency,
        "reference_rate": snapshot.reference_rate,
        "published_at": snapshot.published_at,
    }


@router.post("/rate-snapshots/{snapshot_id}/verify")
def verify_rate_snapshot(
    snapshot_id: str,
    db: DbSession,
    current_user=Depends(require_permission("payments:fx:manage")),
):
    snapshot = FxService(db).verify_rate_snapshot(snapshot_id=snapshot_id, actor_user_id=current_user.id)
    _commit(db)
    return {"id": snapshot.id, "verification_status": snapshot.verification_status, "verified_at": snapshot.verified_at}


@router.post("/fee-policies", status_code=status.HTTP_201_CREATED)
def create_fee_policy(
    payload: FxFeePolicyCreate,
    db: DbSession,
    current_user=Depends(require_permission("payments:fx:manage")),
):
    fields = payload.model_dump()
    # Activation always follows a separate approval request; the supplied flag is deliberately ignored.
    fields.pop("active", None)
    policy = FxService(db).create_fee_policy(actor_user_id=current_user.id, active=False, **fields)
    _commit(db)
    return {"id": policy.id, "policy_version": policy.policy_version, "active": policy.active}


@router.post("/fee-policies/{policy_id}/activate")
def activate_fee_policy(
    policy_id: str,
    db: DbSession,
    current_user=Depends(require_permission("payments:fx:manage")),
):
    policy = FxService(db).activate_fee_policy(policy_id=policy_id, actor_user_id=current_user.id)
    _commit(db)
    return {"id": policy.id, "policy_version": policy.policy_version, "active": policy.active}


@router.post("/quotes", response_model=FxQuoteResponse, status_code=status.HTTP_201_CREATED)
def create_fx_quote(
    payload: FxQuoteCreate,
    db: DbSession,
    current_user=Depends(require_permission("payments:fx:quote")),
):
    institution_id = _actor_institution(current_user, db, payload.invoice_id)
    quote, _risk = FxService(db).create_quote(
        institution_id=institution_id,
        actor_user_id=current_user.id,
        **payload.model_dump(),
    )
    _commit(db)
    return FxQuoteResponse(**FxService(db).quote_summary(quote))


@router.post("/quotes/{quote_id}/lock", response_model=FxQuoteResponse)
def lock_fx_quote(
    quote_id: str,
    db: DbSession,
    current_user=Depends(require_permission("payments:fx:quote")),
):
    institution_id = _actor_institution(current_user, db)
    quote = FxService(db).lock_quote(
        quote_id=quote_id,
        institution_id=institution_id,
        actor_user_id=current_user.id,
    )
    _commit(db)
    return FxQuoteResponse(**FxService(db).quote_summary(quote))
