"""Financial Engine — Business services for billing, invoicing, payments."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

import sys

from ..services.audit_service import log_action
from .pricing import MINIMUM_BILL


def _engine_enabled() -> bool:
    """Read Financial Engine flag at call time (supports monkeypatching in tests)."""
    # Use sys.modules to get the dynamically-mutable config value
    config = sys.modules.get("app.config")
    if config is None:
        return False
    return bool(getattr(config, "ENABLE_FINANCIAL_ENGINE", False))
from .models import (
    FinInvoice,
    FinInvoiceItem,
    FinPayable,
    FinPayment,
    FinPricingRule,
    FinProvider,
    FinReceivable,
    FinSubscription,
    FinTransaction,
)
from .pricing import calculate_fee

logger = logging.getLogger("gula.financial.services")

__all__ = [
    "BillingService",
    "InvoiceService",
    "PaymentService",
    "ReceivableService",
    "PayableService",
    "PricingService",
    "FinancialReportService",
]


class BillingService:
    """Monthly billing cycle for all active subscriptions."""

    @staticmethod
    def run_billing_cycle(db: Session, billing_date: date | None = None) -> list[dict[str, Any]]:
        if not _engine_enabled():
            return []
        billing_date = billing_date or date.today()
        results: list[dict[str, Any]] = []
        subscriptions = (
            db.query(FinSubscription)
            .filter(FinSubscription.status == "active")
            .all()
        )
        for sub in subscriptions:
            provider = db.query(FinProvider).filter(FinProvider.id == sub.provider_id).first()
            if not provider:
                continue
            invoice = InvoiceService.create_invoice(
                db=db,
                lab_id=provider.lab_id,
                subscription_id=sub.id,
                amount=sub.amount or Decimal("0"),
                currency=sub.currency or "IQD",
                due_date=billing_date + timedelta(days=30),
                notes=f"Monthly billing — {sub.plan} plan",
            )
            results.append(invoice)
        logger.info("Billing cycle complete: %d invoices generated", len(results))
        return results


class InvoiceService:
    """Invoice creation, management, and lifecycle."""

    @staticmethod
    def create_invoice(
        db: Session,
        lab_id: int,
        subscription_id: int | None = None,
        amount: Decimal = Decimal("0"),
        currency: str = "IQD",
        due_date: date | None = None,
        notes: str | None = None,
        items: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if not _engine_enabled():
            return {}
        invoice_count = (
            db.query(sa_func.count(FinInvoice.id))
            .filter(FinInvoice.lab_id == lab_id)
            .scalar()
            or 0
        )
        invoice_number = f"INV-{lab_id:04d}-{invoice_count + 1:06d}"
        now = datetime.utcnow()
        invoice = FinInvoice(
            lab_id=lab_id,
            invoice_number=invoice_number,
            subscription_id=subscription_id,
            status="issued",
            amount=amount,
            currency=currency,
            due_date=due_date or date.today() + timedelta(days=30),
            issued_at=now,
            notes=notes,
        )
        db.add(invoice)
        db.flush()

        if items:
            for idx, item_data in enumerate(items):
                item = FinInvoiceItem(
                    invoice_id=invoice.id,
                    line_number=idx + 1,
                    description=item_data.get("description", ""),
                    quantity=item_data.get("quantity", 1),
                    unit_price=Decimal(str(item_data.get("unit_price", 0))),
                    total_price=Decimal(str(item_data.get("total_price", 0))),
                )
                db.add(item)

        log_action(
            db=db,
            action="financial.invoice.created",
            resource_type="fin_invoice",
            resource_id=invoice.id,
            details=f"invoice={invoice_number} amount={amount}",
        )
        db.flush()
        return {
            "id": invoice.id,
            "lab_id": lab_id,
            "invoice_number": invoice_number,
            "status": "issued",
            "amount": amount,
            "currency": currency,
            "due_date": invoice.due_date,
            "issued_at": now,
            "notes": notes,
        }

    @staticmethod
    def get_invoice(db: Session, invoice_id: int, lab_id: int) -> dict[str, Any] | None:
        invoice = (
            db.query(FinInvoice)
            .filter(FinInvoice.id == invoice_id, FinInvoice.lab_id == lab_id)
            .first()
        )
        if not invoice:
            return None
        return {
            "id": invoice.id,
            "lab_id": invoice.lab_id,
            "invoice_number": invoice.invoice_number,
            "status": invoice.status,
            "amount": invoice.amount,
            "paid_amount": invoice.paid_amount or Decimal("0"),
            "currency": invoice.currency,
            "due_date": invoice.due_date,
            "issued_at": invoice.issued_at,
            "paid_at": invoice.paid_at,
            "notes": invoice.notes,
        }

    @staticmethod
    def list_invoices(
        db: Session, lab_id: int, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        q = db.query(FinInvoice).filter(FinInvoice.lab_id == lab_id)
        if status:
            q = q.filter(FinInvoice.status == status)
        q = q.order_by(FinInvoice.issued_at.desc()).offset(offset).limit(limit)
        return [
            {
                "id": inv.id,
                "lab_id": inv.lab_id,
                "invoice_number": inv.invoice_number,
                "status": inv.status,
                "amount": inv.amount,
                "paid_amount": inv.paid_amount or Decimal("0"),
                "currency": inv.currency,
                "due_date": inv.due_date,
                "issued_at": inv.issued_at,
                "paid_at": inv.paid_at,
            }
            for inv in q.all()
        ]


class PaymentService:
    """Payment processing, allocation, and reconciliation."""

    @staticmethod
    def process_payment(
        db: Session,
        invoice_id: int,
        lab_id: int,
        amount: Decimal,
        currency: str = "IQD",
        method: str = "bank_transfer",
        reference: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not _engine_enabled():
            return {}
        if amount <= 0:
            raise ValueError("Payment amount must be positive")

        invoice = (
            db.query(FinInvoice)
            .filter(FinInvoice.id == invoice_id, FinInvoice.lab_id == lab_id)
            .first()
        )
        if not invoice:
            raise ValueError("Invoice not found")

        now = datetime.utcnow()
        payment = FinPayment(
            invoice_id=invoice_id,
            lab_id=lab_id,
            amount=amount,
            currency=currency,
            method=method,
            status="completed",
            reference=reference,
            processed_at=now,
            notes=notes,
        )
        db.add(payment)

        invoice.paid_amount = (invoice.paid_amount or Decimal("0")) + amount
        if invoice.paid_amount >= invoice.amount:
            invoice.status = "paid"
            invoice.paid_at = now
        else:
            invoice.status = "partial"

        log_action(
            db=db,
            action="financial.payment.processed",
            resource_type="fin_payment",
            resource_id=payment.id,
            details=f"invoice={invoice_id} amount={amount} method={method}",
        )

        txn = FinTransaction(
            provider_id=None,
            subscription_id=None,
            transaction_type="payment",
            amount=amount,
            currency=currency,
            status="settled",
            description=notes or f"Payment for invoice {invoice.invoice_number}",
            reference_id=str(payment.id),
            reference_type="payment",
            created_at=now,
            settled_at=now,
        )
        db.add(txn)
        db.flush()

        return {
            "id": payment.id,
            "invoice_id": invoice_id,
            "amount": amount,
            "currency": currency,
            "method": method,
            "status": "completed",
            "reference": reference,
            "processed_at": now,
            "notes": notes,
        }

    @staticmethod
    def list_payments(
        db: Session, lab_id: int, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        q = (
            db.query(FinPayment)
            .filter(FinPayment.lab_id == lab_id)
            .order_by(FinPayment.processed_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return [
            {
                "id": p.id,
                "invoice_id": p.invoice_id,
                "amount": p.amount,
                "currency": p.currency,
                "method": p.method,
                "status": p.status,
                "reference": p.reference,
                "processed_at": p.processed_at,
            }
            for p in q.all()
        ]


class ReceivableService:
    """Accounts receivable tracking and aging."""

    @staticmethod
    def get_receivables(db: Session, lab_id: int) -> list[dict[str, Any]]:
        invoices = (
            db.query(FinInvoice)
            .filter(
                FinInvoice.lab_id == lab_id,
                FinInvoice.status.in_(["issued", "partial"]),
            )
            .all()
        )
        today = date.today()
        result = []
        for inv in invoices:
            outstanding = inv.amount - (inv.paid_amount or Decimal("0"))
            due = inv.due_date or today
            aging_days = (today - due).days if due < today else 0
            result.append({
                "id": inv.id,
                "lab_id": lab_id,
                "invoice_id": inv.id,
                "amount": outstanding,
                "currency": inv.currency,
                "status": inv.status,
                "due_date": due,
                "aging_days": max(aging_days, 0),
            })
        return result

    @staticmethod
    def get_aging_summary(db: Session, lab_id: int) -> dict[str, Decimal]:
        invoices = (
            db.query(FinInvoice)
            .filter(
                FinInvoice.lab_id == lab_id,
                FinInvoice.status.in_(["issued", "partial"]),
            )
            .all()
        )
        today = date.today()
        buckets = {"0-30": Decimal("0"), "31-60": Decimal("0"), "61-90": Decimal("0"), "90+": Decimal("0")}
        for inv in invoices:
            outstanding = inv.amount - (inv.paid_amount or Decimal("0"))
            due = inv.due_date or today
            days = (today - due).days if due < today else 0
            if days <= 30:
                buckets["0-30"] += outstanding
            elif days <= 60:
                buckets["31-60"] += outstanding
            elif days <= 90:
                buckets["61-90"] += outstanding
            else:
                buckets["90+"] += outstanding
        return buckets


class PayableService:
    """Accounts payable management."""

    @staticmethod
    def get_payables(db: Session, provider_id: int) -> list[dict[str, Any]]:
        payables = (
            db.query(FinPayable)
            .filter(FinPayable.provider_id == provider_id)
            .order_by(FinPayable.due_date.asc())
            .all()
        )
        return [
            {
                "id": p.id,
                "provider_id": p.provider_id,
                "amount": p.amount,
                "currency": p.currency,
                "status": p.status,
                "due_date": p.due_date,
            }
            for p in payables
        ]


class PricingService:
    """Pricing rules engine."""

    @staticmethod
    def get_price(
        db: Session,
        test_name: str,
        lab_id: int,
        quantity: int = 1,
        quality_score: float | None = None,
        monthly_volume: int = 0,
    ) -> dict[str, Any]:
        rule = (
            db.query(FinPricingRule)
            .filter(
                FinPricingRule.test_type == test_name,
                FinPricingRule.active.is_(True),
            )
            .first()
        )
        base_price = rule.base_price if rule else Decimal("10000")
        accredited = False
        if quality_score is not None:
            accredited = quality_score >= 0.8
        total = calculate_fee(
            base_price=base_price,
            quantity=quantity,
            quality_accredited=accredited,
            monthly_volume=monthly_volume,
        )
        return {
            "base_price": base_price,
            "quantity": quantity,
            "quality_discount_pct": 5.0 if accredited else 0.0,
            "volume_discount_pct": 10.0 if monthly_volume > 100 else 0.0,
            "total": total,
            "currency": "IQD",
        }

    @staticmethod
    def create_rule(
        db: Session,
        name: str,
        test_type: str | None,
        base_price: Decimal,
        currency: str = "IQD",
        quality_discount_pct: float = 0.0,
        volume_discount_pct: float = 0.0,
    ) -> dict[str, Any]:
        rule = FinPricingRule(
            name=name,
            test_type=test_type,
            base_price=base_price,
            currency=currency,
            quality_discount_pct=quality_discount_pct,
            volume_discount_pct=volume_discount_pct,
            active=True,
        )
        db.add(rule)
        db.flush()
        return {
            "id": rule.id,
            "name": rule.name,
            "test_type": rule.test_type,
            "base_price": rule.base_price,
            "currency": rule.currency,
            "active": rule.active,
        }


class FinancialReportService:
    """Financial reporting and analytics."""

    @staticmethod
    def generate_report(
        db: Session,
        lab_id: int,
        date_from: date,
        date_to: date,
        group_by: str = "month",
    ) -> dict[str, Any]:
        invoices = (
            db.query(FinInvoice)
            .filter(
                FinInvoice.lab_id == lab_id,
                FinInvoice.issued_at >= datetime.combine(date_from, datetime.min.time()),
                FinInvoice.issued_at <= datetime.combine(date_to, datetime.max.time()),
            )
            .all()
        )
        payments = (
            db.query(FinPayment)
            .filter(
                FinPayment.lab_id == lab_id,
                FinPayment.processed_at >= datetime.combine(date_from, datetime.min.time()),
                FinPayment.processed_at <= datetime.combine(date_to, datetime.max.time()),
            )
            .all()
        )

        total_invoiced = sum((inv.amount or Decimal("0")) for inv in invoices)
        total_collected = sum((p.amount or Decimal("0")) for p in payments)
        total_outstanding = total_invoiced - total_collected
        breakdown: list[dict[str, Any]] = [{"period": f"{date_from} - {date_to}", "invoiced": total_invoiced, "collected": total_collected}]

        return {
            "lab_id": lab_id,
            "period": {"from": date_from, "to": date_to},
            "total_invoiced": total_invoiced,
            "total_collected": total_collected,
            "total_outstanding": total_outstanding,
            "invoice_count": len(invoices),
            "payment_count": len(payments),
            "group_by": group_by,
            "breakdown": breakdown,
        }
