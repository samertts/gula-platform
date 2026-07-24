"""Financial Engine Phase B — integration tests for services and models."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from app.financial.models import (
    FinInvoice,
    FinPayment,
    FinPricingRule,
    FinProvider,
    FinSubscription,
    FinTransaction,
)


@pytest.fixture(autouse=True)
def _enable_financial_engine(monkeypatch):
    monkeypatch.setattr("app.config.ENABLE_FINANCIAL_ENGINE", True)
    monkeypatch.setattr("app.financial.ENABLE_FINANCIAL_ENGINE", True)


def _create_provider(db, lab_id: int = 1, **kw) -> FinProvider:
    p = FinProvider(
        lab_id=lab_id,
        name=kw.get("name", "Test Provider"),
        status=kw.get("status", "active"),
        quality_score=kw.get("quality_score", 0.85),
        accredited=kw.get("accredited", True),
    )
    db.add(p)
    db.flush()
    return p


def _create_subscription(db, provider_id: int, **kw) -> FinSubscription:
    s = FinSubscription(
        provider_id=provider_id,
        plan=kw.get("plan", "premium"),
        status=kw.get("status", "active"),
        billing_cycle=kw.get("billing_cycle", "monthly"),
        amount=kw.get("amount", Decimal("150000.00")),
        currency=kw.get("currency", "IQD"),
    )
    db.add(s)
    db.flush()
    return s


class TestInvoiceService:
    def test_create_invoice(self, db):
        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        from app.financial.services import InvoiceService
        result = InvoiceService.create_invoice(
            db=db, lab_id=1, subscription_id=s.id,
            amount=Decimal("50000.00"), currency="IQD",
            due_date=date.today() + timedelta(days=30),
        )
        assert result["lab_id"] == 1
        assert result["amount"] == Decimal("50000.00")
        assert result["status"] == "issued"
        assert "INV-" in result["invoice_number"]

    def test_get_invoice(self, db):
        from app.financial.services import InvoiceService
        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        created = InvoiceService.create_invoice(db=db, lab_id=1, subscription_id=s.id, amount=Decimal("25000.00"))
        fetched = InvoiceService.get_invoice(db, created["id"], 1)
        assert fetched is not None
        assert fetched["id"] == created["id"]
        assert fetched["amount"] == Decimal("25000.00")

    def test_get_invoice_wrong_lab(self, db):
        from app.financial.services import InvoiceService
        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        created = InvoiceService.create_invoice(db=db, lab_id=1, subscription_id=s.id, amount=Decimal("10000.00"))
        assert InvoiceService.get_invoice(db, created["id"], 999) is None

    def test_list_invoices(self, db):
        from app.financial.services import InvoiceService
        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        InvoiceService.create_invoice(db=db, lab_id=1, subscription_id=s.id, amount=Decimal("10000.00"))
        InvoiceService.create_invoice(db=db, lab_id=1, subscription_id=s.id, amount=Decimal("20000.00"))
        invoices = InvoiceService.list_invoices(db, lab_id=1)
        assert len(invoices) >= 2

    def test_list_invoices_lab_isolation(self, db):
        from app.financial.services import InvoiceService
        p1 = _create_provider(db, lab_id=1)
        p2 = _create_provider(db, lab_id=2)
        s1 = _create_subscription(db, provider_id=p1.id)
        s2 = _create_subscription(db, provider_id=p2.id)
        InvoiceService.create_invoice(db=db, lab_id=1, subscription_id=s1.id, amount=Decimal("10000.00"))
        InvoiceService.create_invoice(db=db, lab_id=2, subscription_id=s2.id, amount=Decimal("20000.00"))
        lab1_invoices = InvoiceService.list_invoices(db, lab_id=1)
        lab2_invoices = InvoiceService.list_invoices(db, lab_id=2)
        assert len(lab1_invoices) == 1
        assert len(lab2_invoices) == 1
        assert lab1_invoices[0]["lab_id"] == 1
        assert lab2_invoices[0]["lab_id"] == 2


class TestPaymentService:
    def test_process_full_payment(self, db):
        from app.financial.services import InvoiceService, PaymentService
        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        inv = InvoiceService.create_invoice(db=db, lab_id=1, subscription_id=s.id, amount=Decimal("50000.00"))
        result = PaymentService.process_payment(db=db, invoice_id=inv["id"], lab_id=1, amount=Decimal("50000.00"))
        assert result["status"] == "completed"
        assert result["amount"] == Decimal("50000.00")
        updated = InvoiceService.get_invoice(db, inv["id"], 1)
        assert updated["status"] == "paid"
        assert updated["paid_amount"] == Decimal("50000.00")

    def test_process_partial_payment(self, db):
        from app.financial.services import InvoiceService, PaymentService
        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        inv = InvoiceService.create_invoice(db=db, lab_id=1, subscription_id=s.id, amount=Decimal("50000.00"))
        result = PaymentService.process_payment(db=db, invoice_id=inv["id"], lab_id=1, amount=Decimal("30000.00"))
        assert result["status"] == "completed"
        updated = InvoiceService.get_invoice(db, inv["id"], 1)
        assert updated["status"] == "partial"

    def test_full_after_partial(self, db):
        from app.financial.services import InvoiceService, PaymentService
        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        inv = InvoiceService.create_invoice(db=db, lab_id=1, subscription_id=s.id, amount=Decimal("50000.00"))
        PaymentService.process_payment(db=db, invoice_id=inv["id"], lab_id=1, amount=Decimal("30000.00"))
        PaymentService.process_payment(db=db, invoice_id=inv["id"], lab_id=1, amount=Decimal("20000.00"))
        updated = InvoiceService.get_invoice(db, inv["id"], 1)
        assert updated["status"] == "paid"
        assert updated["paid_amount"] == Decimal("50000.00")

    def test_process_payment_invoice_not_found(self, db):
        from app.financial.services import PaymentService
        with pytest.raises(ValueError, match="Invoice not found"):
            PaymentService.process_payment(db=db, invoice_id=99999, lab_id=1, amount=Decimal("100.00"))

    def test_process_payment_zero_amount(self, db):
        from app.financial.services import PaymentService
        with pytest.raises(ValueError, match="must be positive"):
            PaymentService.process_payment(db=db, invoice_id=1, lab_id=1, amount=Decimal("0"))

    def test_list_payments(self, db):
        from app.financial.services import InvoiceService, PaymentService
        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        inv = InvoiceService.create_invoice(db=db, lab_id=1, subscription_id=s.id, amount=Decimal("30000.00"))
        PaymentService.process_payment(db=db, invoice_id=inv["id"], lab_id=1, amount=Decimal("30000.00"))
        payments = PaymentService.list_payments(db, lab_id=1)
        assert len(payments) >= 1
        assert payments[0]["amount"] == Decimal("30000.00")

    def test_list_payments_lab_isolation(self, db):
        from app.financial.services import InvoiceService, PaymentService
        p1 = _create_provider(db, lab_id=1)
        p2 = _create_provider(db, lab_id=2)
        s1 = _create_subscription(db, provider_id=p1.id)
        s2 = _create_subscription(db, provider_id=p2.id)
        inv1 = InvoiceService.create_invoice(db=db, lab_id=1, subscription_id=s1.id, amount=Decimal("10000.00"))
        inv2 = InvoiceService.create_invoice(db=db, lab_id=2, subscription_id=s2.id, amount=Decimal("20000.00"))
        PaymentService.process_payment(db=db, invoice_id=inv1["id"], lab_id=1, amount=Decimal("10000.00"))
        PaymentService.process_payment(db=db, invoice_id=inv2["id"], lab_id=2, amount=Decimal("20000.00"))
        lab1_payments = PaymentService.list_payments(db, lab_id=1)
        lab2_payments = PaymentService.list_payments(db, lab_id=2)
        assert len(lab1_payments) == 1
        assert len(lab2_payments) == 1


class TestReceivableService:
    def test_get_receivables(self, db):
        from app.financial.services import InvoiceService, ReceivableService
        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        InvoiceService.create_invoice(db=db, lab_id=1, subscription_id=s.id, amount=Decimal("75000.00"))
        receivables = ReceivableService.get_receivables(db, lab_id=1)
        assert len(receivables) >= 1
        assert receivables[0]["amount"] > 0

    def test_get_aging_summary(self, db):
        from app.financial.services import InvoiceService, ReceivableService
        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        InvoiceService.create_invoice(db=db, lab_id=1, subscription_id=s.id, amount=Decimal("50000.00"))
        summary = ReceivableService.get_aging_summary(db, lab_id=1)
        assert isinstance(summary, dict)
        assert "0-30" in summary


class TestPricingService:
    def test_get_price(self, db):
        from app.financial.services import PricingService
        rule = FinPricingRule(
            name="CBC Test", test_type="CBC",
            base_price=Decimal("15000"), active=True,
        )
        db.add(rule)
        db.flush()
        result = PricingService.get_price(db, test_name="CBC", lab_id=1, quantity=2)
        assert result["base_price"] == Decimal("15000")
        assert result["quantity"] == 2
        assert result["total"] > 0
        assert result["currency"] == "IQD"

    def test_get_price_default_when_no_rule(self, db):
        from app.financial.services import PricingService
        result = PricingService.get_price(db, test_name="UNKNOWN_TEST", lab_id=1)
        assert result["base_price"] == Decimal("10000")

    def test_create_rule(self, db):
        from app.financial.services import PricingService
        result = PricingService.create_rule(
            db=db, name="Glucose", test_type="GLU",
            base_price=Decimal("8000"), currency="IQD",
        )
        assert result["name"] == "Glucose"
        assert result["base_price"] == Decimal("8000")
        assert result["active"] is True


class TestBillingService:
    def test_run_billing_cycle(self, db):
        from app.financial.services import BillingService
        p = _create_provider(db, lab_id=1)
        _create_subscription(db, provider_id=p.id, amount=Decimal("100000.00"))
        results = BillingService.run_billing_cycle(db)
        assert len(results) >= 1
        assert results[0]["amount"] == Decimal("100000.00")


class TestFinancialReportService:
    def test_generate_report_empty(self, db):
        from app.financial.services import FinancialReportService
        report = FinancialReportService.generate_report(
            db=db, lab_id=1,
            date_from=date(2024, 1, 1),
            date_to=date(2024, 12, 31),
        )
        assert report["total_invoiced"] == Decimal("0")
        assert report["total_collected"] == Decimal("0")
        assert report["total_outstanding"] == Decimal("0")

    def test_generate_report_with_data(self, db):
        from app.financial.services import FinancialReportService, InvoiceService, PaymentService
        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        inv = InvoiceService.create_invoice(db=db, lab_id=1, subscription_id=s.id, amount=Decimal("60000.00"))
        PaymentService.process_payment(db=db, invoice_id=inv["id"], lab_id=1, amount=Decimal("60000.00"))
        report = FinancialReportService.generate_report(
            db=db, lab_id=1,
            date_from=date.today() - timedelta(days=1),
            date_to=date.today() + timedelta(days=1),
        )
        assert report["total_invoiced"] == Decimal("60000.00")


class TestEdgeCases:
    def test_create_invoice_zero_amount(self, db):
        from app.financial.services import InvoiceService
        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        result = InvoiceService.create_invoice(db=db, lab_id=1, subscription_id=s.id, amount=Decimal("0"))
        assert result["amount"] == Decimal("0")

    def test_multiple_providers_same_lab(self, db):
        from app.financial.services import InvoiceService
        p1 = _create_provider(db, lab_id=10, name="Prov A")
        p2 = _create_provider(db, lab_id=10, name="Prov B")
        s1 = _create_subscription(db, provider_id=p1.id)
        s2 = _create_subscription(db, provider_id=p2.id)
        inv1 = InvoiceService.create_invoice(db=db, lab_id=10, subscription_id=s1.id, amount=Decimal("1000"))
        inv2 = InvoiceService.create_invoice(db=db, lab_id=10, subscription_id=s2.id, amount=Decimal("2000"))
        assert inv1["lab_id"] == 10
        assert inv2["lab_id"] == 10
