"""Financial Engine — Phase B routes for billing, invoices, payments, reports."""

from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..config import ENABLE_FINANCIAL_ENGINE
from ..database import get_db
from ..models.lab import Lab
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services.audit_service import log_action
from .models import (
    FinPricingRule,
    FinProvider,
    FinSubscription,
    FinTransaction,
)
from .services import (
    BillingService,
    FinancialReportService,
    InvoiceService,
    PayableService,
    PaymentService,
    PricingService,
    ReceivableService,
)

logger = logging.getLogger("gula.financial.routes")

router = APIRouter(prefix="/financial", tags=["financial"])


def _check_enabled() -> None:
    if not ENABLE_FINANCIAL_ENGINE:
        raise HTTPException(status_code=404, detail="Financial Engine is not enabled")


def _get_provider(db: Session, lab_id: int) -> FinProvider:
    provider = db.query(FinProvider).filter(FinProvider.lab_id == lab_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="No billing provider found for this lab")
    return provider


# ── Billing Status ─────────────────────────────────────────────────────


@router.get("/billing/status")
def get_billing_status(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_enabled()
    lab = db.query(Lab).filter(Lab.id == current_user.lab_id).first()
    provider = db.query(FinProvider).filter(FinProvider.lab_id == current_user.lab_id).first()
    return {
        "lab_id": current_user.lab_id,
        "lab_name": lab.name if lab else "",
        "engine_enabled": True,
        "status": provider.status if provider else "inactive",
        "pricing_version": "2.1.0",
        "currency": "IQD",
        "minimum_bill": 5000,
        "provider_id": provider.id if provider else None,
    }


@router.get("/billing/rates")
def get_billing_rates(
    current_user: LabUser = Depends(get_current_user),
):
    _check_enabled()
    return {
        "base_rate": 10000,
        "currency": "IQD",
        "quality_discount_pct": 5.0,
        "volume_discount_threshold": 100,
        "volume_discount_pct": 10.0,
        "minimum_bill": 5000,
    }


# ── Invoices ───────────────────────────────────────────────────────────


@router.get("/invoices")
def list_invoices(
    status: str | None = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_enabled()
    return InvoiceService.list_invoices(db, current_user.lab_id, status, limit, offset)


@router.get("/invoices/{invoice_id}")
def get_invoice(
    invoice_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_enabled()
    invoice = InvoiceService.get_invoice(db, invoice_id, current_user.lab_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.post("/invoices", status_code=201)
def create_invoice(
    amount: float = Query(..., description="Invoice amount"),
    currency: str = Query("IQD"),
    due_date: date | None = Query(None),
    notes: str | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_enabled()
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    provider = _get_provider(db, current_user.lab_id)
    sub = db.query(FinSubscription).filter(FinSubscription.provider_id == provider.id).first()
    result = InvoiceService.create_invoice(
        db=db,
        lab_id=current_user.lab_id,
        subscription_id=sub.id if sub else None,
        amount=Decimal(str(amount)),
        currency=currency,
        due_date=due_date,
        notes=notes,
    )
    db.commit()
    return result


# ── Payments ───────────────────────────────────────────────────────────


@router.post("/payments", status_code=201)
def process_payment(
    invoice_id: int = Query(..., description="Invoice ID"),
    amount: float = Query(..., description="Payment amount"),
    currency: str = Query("IQD"),
    method: str = Query("bank_transfer"),
    reference: str | None = Query(None),
    notes: str | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_enabled()
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    try:
        result = PaymentService.process_payment(
            db=db,
            invoice_id=invoice_id,
            lab_id=current_user.lab_id,
            amount=Decimal(str(amount)),
            currency=currency,
            method=method,
            reference=reference,
            notes=notes,
        )
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/payments")
def list_payments(
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_enabled()
    return PaymentService.list_payments(db, current_user.lab_id, limit, offset)


# ── Receivables ────────────────────────────────────────────────────────


@router.get("/receivables")
def get_receivables(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_enabled()
    return ReceivableService.get_receivables(db, current_user.lab_id)


@router.get("/receivables/aging")
def get_receivable_aging(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_enabled()
    return ReceivableService.get_aging_summary(db, current_user.lab_id)


# ── Payables ───────────────────────────────────────────────────────────


@router.get("/payables")
def get_payables(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_enabled()
    provider = _get_provider(db, current_user.lab_id)
    return PayableService.get_payables(db, provider.id)


# ── Pricing ────────────────────────────────────────────────────────────


@router.get("/pricing/calculate")
def calculate_price(
    test_name: str = Query(..., description="Test name/code"),
    quantity: int = Query(1, ge=1),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_enabled()
    return PricingService.get_price(db, test_name, current_user.lab_id, quantity)


@router.post("/pricing/rules", status_code=201)
def create_pricing_rule(
    name: str = Query(...),
    test_type: str | None = Query(None),
    base_price: float = Query(...),
    quality_discount_pct: float = Query(0.0, ge=0.0, le=100.0),
    volume_discount_pct: float = Query(0.0, ge=0.0, le=100.0),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_enabled()
    if base_price <= 0:
        raise HTTPException(status_code=400, detail="Base price must be positive")
    result = PricingService.create_rule(
        db=db,
        name=name,
        test_type=test_type,
        base_price=Decimal(str(base_price)),
        quality_discount_pct=quality_discount_pct,
        volume_discount_pct=volume_discount_pct,
    )
    db.commit()
    return result


@router.get("/pricing/rules")
def list_pricing_rules(
    active_only: bool = Query(True),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_enabled()
    q = db.query(FinPricingRule)
    if active_only:
        q = q.filter(FinPricingRule.active.is_(True))
    rules = q.all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "test_type": r.test_type,
            "base_price": r.base_price,
            "currency": r.currency,
            "active": r.active,
        }
        for r in rules
    ]


# ── Transactions ───────────────────────────────────────────────────────


@router.post("/transactions")
def create_transaction(
    amount: float = Query(..., description="Transaction amount"),
    description: str = Query("", description="Transaction description"),
    transaction_type: str = Query("billing", description="Transaction type"),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_enabled()
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    provider = _get_provider(db, current_user.lab_id)
    txn = FinTransaction(
        provider_id=provider.id,
        transaction_type=transaction_type,
        amount=Decimal(str(amount)),
        currency="IQD",
        status="pending",
        description=description,
        created_at=datetime.utcnow(),
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    log_action(
        db=db,
        action="financial.transaction.created",
        entity_type="fin_transaction",
        entity_id=str(txn.id),
        lab_id=current_user.lab_id,
        user_id=current_user.id,
        details={"amount": amount, "type": transaction_type},
    )
    return {"id": txn.id, "status": "pending", "amount": amount, "description": description}


@router.get("/transactions")
def list_transactions(
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_enabled()
    provider = _get_provider(db, current_user.lab_id)
    txns = (
        db.query(FinTransaction)
        .filter(FinTransaction.provider_id == provider.id)
        .order_by(FinTransaction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": t.id,
            "type": t.transaction_type,
            "amount": t.amount,
            "currency": t.currency,
            "status": t.status,
            "description": t.description,
            "created_at": t.created_at,
            "settled_at": t.settled_at,
        }
        for t in txns
    ]


# ── Billing Cycle ──────────────────────────────────────────────────────


@router.post("/billing/run-cycle")
def run_billing_cycle(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_enabled()
    results = BillingService.run_billing_cycle(db)
    db.commit()
    log_action(
        db=db,
        action="financial.billing.cycle_run",
        entity_type="fin_billing_cycle",
        entity_id="",
        lab_id=current_user.lab_id,
        user_id=current_user.id,
        details={"invoices_generated": len(results)},
    )
    return {"invoices_generated": len(results), "invoices": results}


# ── Reports ────────────────────────────────────────────────────────────


@router.get("/reports/summary")
def get_financial_summary(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_enabled()
    from datetime import timedelta
    date_to = date_to or date.today()
    date_from = date_from or (date_to - timedelta(days=30))
    return FinancialReportService.generate_report(
        db=db,
        lab_id=current_user.lab_id,
        date_from=date_from,
        date_to=date_to,
    )


# ── Subscription management ────────────────────────────────────────────


@router.get("/subscriptions")
def list_subscriptions(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_enabled()
    provider = _get_provider(db, current_user.lab_id)
    subs = (
        db.query(FinSubscription)
        .filter(FinSubscription.provider_id == provider.id)
        .all()
    )
    return [
        {
            "id": s.id,
            "plan": s.plan,
            "status": s.status,
            "billing_cycle": s.billing_cycle,
            "amount": s.amount,
            "currency": s.currency,
            "start_date": s.start_date,
            "end_date": s.end_date,
            "auto_renew": s.auto_renew,
        }
        for s in subs
    ]
