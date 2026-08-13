"""Authenticated API surface for the GULA Health Payments foundation."""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.exceptions import NotFoundError
from app.security.dependencies import require_permission

from .models import CashShift, PaymentInvoice, PaymentProvider
from .schemas import (
    CashPaymentCapture,
    CashShiftClose,
    CashShiftOpen,
    InvoiceCreate,
    InvoiceResponse,
    PaymentIntentCreate,
    PaymentIntentResponse,
    PaymentProviderResponse,
    ReconciliationCaseResponse,
    RefundCreate,
    RefundResponse,
)
from .service import PaymentService

router = APIRouter(prefix="/payments", tags=["GULA Health Payments"])
DbSession = Annotated[Session, Depends(get_db)]


def _service(db: Session) -> PaymentService:
    return PaymentService(db)


def _commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _intent_response(intent) -> PaymentIntentResponse:
    return PaymentIntentResponse(
        id=intent.id,
        invoice_id=intent.invoice_id,
        institution_id=intent.institution_id,
        amount=Decimal(intent.amount),
        currency=intent.currency,
        method=intent.method,
        status=intent.status,
        expires_at=intent.expires_at,
        created_at=intent.created_at,
    )


def _refund_response(refund) -> RefundResponse:
    return RefundResponse(
        id=refund.id,
        invoice_id=refund.invoice_id,
        payment_intent_id=refund.payment_intent_id,
        amount=Decimal(refund.amount),
        currency=refund.currency,
        status=refund.status,
        reason=refund.reason,
        created_at=refund.created_at,
    )


@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: InvoiceCreate,
    db: DbSession,
    current_user=Depends(require_permission("payments:write")),
):
    service = _service(db)
    service.assert_institution_access(current_user, payload.institution_id)
    invoice = service.create_invoice(
        institution_id=payload.institution_id,
        patient_reference=payload.patient_reference,
        due_at=payload.due_at,
        lines=payload.lines,
        actor_user_id=current_user.id,
    )
    _commit(db)
    return InvoiceResponse(**service.invoice_summary(invoice))


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: str,
    db: DbSession,
    current_user=Depends(require_permission("payments:read")),
):
    service = _service(db)
    invoice = db.query(PaymentInvoice).filter(PaymentInvoice.id == invoice_id).first()
    if invoice is None:
        raise NotFoundError("Payment invoice not found")
    service.assert_institution_access(current_user, invoice.institution_id)
    return InvoiceResponse(**service.invoice_summary(invoice))


@router.post("/intents", response_model=PaymentIntentResponse, status_code=status.HTTP_201_CREATED)
def create_payment_intent(
    payload: PaymentIntentCreate,
    db: DbSession,
    response: Response,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    current_user=Depends(require_permission("payments:write")),
):
    service = _service(db)
    invoice = service._invoice(payload.invoice_id)
    service.assert_institution_access(current_user, invoice.institution_id)
    intent = service.create_intent(
        institution_id=invoice.institution_id,
        invoice_id=payload.invoice_id,
        amount=payload.amount,
        method=payload.method,
        idempotency_key=idempotency_key or "",
        expires_at=payload.expires_at,
        actor_user_id=current_user.id,
    )
    _commit(db)
    response.headers["Idempotency-Key"] = idempotency_key or ""
    return _intent_response(intent)


@router.post("/cash-shifts", status_code=status.HTTP_201_CREATED)
def open_cash_shift(
    payload: CashShiftOpen,
    db: DbSession,
    current_user=Depends(require_permission("payments:cashier")),
):
    service = _service(db)
    if current_user.lab_id is None:
        raise NotFoundError("No active institution is associated with the current user")
    shift = service.open_cash_shift(
        institution_id=current_user.lab_id,
        cashier_user_id=current_user.id,
        terminal_reference=payload.terminal_reference,
        opening_float=payload.opening_float,
    )
    _commit(db)
    return {
        "id": shift.id,
        "status": shift.status,
        "terminal_reference": shift.terminal_reference,
        "opening_float": shift.opening_float,
        "currency": shift.currency,
        "opened_at": shift.opened_at,
    }


@router.post("/intents/{intent_id}/cash-capture", status_code=status.HTTP_201_CREATED)
def capture_cash_payment(
    intent_id: str,
    payload: CashPaymentCapture,
    db: DbSession,
    current_user=Depends(require_permission("payments:cashier")),
):
    service = _service(db)
    intent = service._intent(intent_id)
    service.assert_institution_access(current_user, intent.institution_id)
    attempt = service.capture_cash(
        institution_id=intent.institution_id,
        intent_id=intent_id,
        cash_shift_id=payload.cash_shift_id,
        cashier_reference=payload.cashier_reference,
        actor_user_id=current_user.id,
    )
    _commit(db)
    return {
        "id": attempt.id,
        "intent_id": attempt.intent_id,
        "status": attempt.status,
        "amount": attempt.amount,
        "currency": attempt.currency,
        "provider_code": attempt.provider_code,
        "verified_at": attempt.verified_at,
    }


@router.post("/cash-shifts/{shift_id}/close", status_code=status.HTTP_200_OK)
def close_cash_shift(
    shift_id: str,
    payload: CashShiftClose,
    db: DbSession,
    current_user=Depends(require_permission("payments:reconcile")),
):
    service = _service(db)
    shift = db.query(CashShift).filter(CashShift.id == shift_id).first()
    if shift is None:
        raise NotFoundError("Cash shift not found")
    service.assert_institution_access(current_user, shift.institution_id)
    closed_shift, reconciliation_case = service.close_cash_shift(
        institution_id=shift.institution_id,
        shift_id=shift_id,
        actual_closing=payload.actual_closing,
        variance_reason=payload.variance_reason,
        actor_user_id=current_user.id,
    )
    _commit(db)
    result = {
        "cash_shift_id": closed_shift.id,
        "status": closed_shift.status,
        "expected_closing": closed_shift.expected_closing,
        "actual_closing": closed_shift.actual_closing,
        "variance_amount": closed_shift.variance_amount,
    }
    if reconciliation_case is not None:
        result["reconciliation_case"] = ReconciliationCaseResponse(
            id=reconciliation_case.id,
            source_type=reconciliation_case.source_type,
            source_reference=reconciliation_case.source_reference,
            status=reconciliation_case.status,
            expected_amount=reconciliation_case.expected_amount,
            observed_amount=reconciliation_case.observed_amount,
            discrepancy_reason=reconciliation_case.discrepancy_reason,
            created_at=reconciliation_case.created_at,
        ).model_dump()
    return result


@router.post("/refunds", response_model=RefundResponse, status_code=status.HTTP_201_CREATED)
def request_refund(
    payload: RefundCreate,
    db: DbSession,
    current_user=Depends(require_permission("payments:refund:request")),
):
    service = _service(db)
    intent = service._intent(payload.payment_intent_id)
    service.assert_institution_access(current_user, intent.institution_id)
    refund = service.request_refund(
        institution_id=intent.institution_id,
        payment_intent_id=payload.payment_intent_id,
        amount=payload.amount,
        reason=payload.reason,
        external_reference=payload.external_reference,
        actor_user_id=current_user.id,
    )
    _commit(db)
    return _refund_response(refund)


@router.post("/refunds/{refund_id}/approve", response_model=RefundResponse)
def approve_refund(
    refund_id: str,
    db: DbSession,
    current_user=Depends(require_permission("payments:refund:approve")),
):
    service = _service(db)
    refund = service._refund(refund_id)
    service.assert_institution_access(current_user, refund.institution_id)
    refund = service.approve_refund(
        institution_id=refund.institution_id,
        refund_id=refund_id,
        actor_user_id=current_user.id,
    )
    _commit(db)
    return _refund_response(refund)


@router.post("/refunds/{refund_id}/cash-process", response_model=RefundResponse)
def process_cash_refund(
    refund_id: str,
    payload: CashPaymentCapture,
    db: DbSession,
    current_user=Depends(require_permission("payments:refund:process")),
):
    service = _service(db)
    refund = service._refund(refund_id)
    service.assert_institution_access(current_user, refund.institution_id)
    refund = service.process_cash_refund(
        institution_id=refund.institution_id,
        refund_id=refund_id,
        cash_shift_id=payload.cash_shift_id,
        cashier_reference=payload.cashier_reference,
        actor_user_id=current_user.id,
    )
    _commit(db)
    return _refund_response(refund)


@router.get("/providers", response_model=list[PaymentProviderResponse])
def list_payment_providers(
    db: DbSession,
    current_user=Depends(require_permission("payments:read")),
):
    # The registry contains integration metadata only; never credentials or payment tokens.
    providers = db.query(PaymentProvider).order_by(PaymentProvider.display_name).all()
    return [
        PaymentProviderResponse(
            code=provider.code,
            display_name=provider.display_name,
            provider_type=provider.provider_type,
            environment=provider.environment,
            status=provider.status,
            supports_refund=provider.supports_refund,
            supports_reconciliation=provider.supports_reconciliation,
        )
        for provider in providers
    ]
