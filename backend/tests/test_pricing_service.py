from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from app.financial.models import (
    FinInvoiceItem,
    FinPayable,
    FinPricingRule,
    FinProvider,
    FinSubscription,
)
from app.financial.pricing import (
    MINIMUM_BILL,
    VOLUME_DISCOUNT_THRESHOLD,
    apply_quality_discount,
    calculate_fee,
    enforce_minimum_bill,
)
from app.financial.services import (
    BillingService,
    FinancialReportService,
    InvoiceService,
    PayableService,
    PaymentService,
    PricingService,
    ReceivableService,
)

# ── Pricing Module (pricing.py) ───────────────────────────────────────


class TestCalculateFee:
    def test_basic_fee(self):
        result = calculate_fee(base_price=Decimal("10000"), quantity=1)
        assert result == Decimal("10000")

    def test_quantity_multiplier(self):
        result = calculate_fee(base_price=Decimal("5000"), quantity=3)
        assert result == Decimal("15000")

    def test_quality_discount_applied(self):
        result = calculate_fee(base_price=Decimal("10000"), quantity=1, quality_accredited=True)
        expected = Decimal("10000") - Decimal("10000") * Decimal("0.05")
        assert result == expected.quantize(Decimal("1"))

    def test_volume_discount_applied(self):
        result = calculate_fee(base_price=Decimal("10000"), quantity=1, monthly_volume=200)
        expected = Decimal("10000") - Decimal("10000") * Decimal("0.10")
        assert result == expected.quantize(Decimal("1"))

    def test_both_discounts(self):
        result = calculate_fee(
            base_price=Decimal("20000"), quantity=1, quality_accredited=True, monthly_volume=200
        )
        subtotal = Decimal("20000")
        discount = subtotal * Decimal("0.05") + subtotal * Decimal("0.10")
        expected = (subtotal - discount).quantize(Decimal("1"))
        assert result == expected

    def test_minimum_bill_enforced(self):
        result = calculate_fee(base_price=Decimal("100"), quantity=1)
        assert result == MINIMUM_BILL

    def test_minimum_bill_with_discount(self):
        result = calculate_fee(base_price=Decimal("5100"), quantity=1, quality_accredited=True)
        assert result >= MINIMUM_BILL

    def test_large_quantity(self):
        result = calculate_fee(base_price=Decimal("1000"), quantity=1000)
        assert result == Decimal("1000000")

    def test_negative_price_raises(self):
        with pytest.raises(ValueError, match="base_price must be non-negative"):
            calculate_fee(base_price=Decimal("-1"), quantity=1)

    def test_zero_quantity_raises(self):
        with pytest.raises(ValueError, match="quantity must be >= 1"):
            calculate_fee(base_price=Decimal("1000"), quantity=0)

    def test_volume_discount_threshold_boundary(self):
        below = calculate_fee(
            base_price=Decimal("10000"), quantity=1, monthly_volume=VOLUME_DISCOUNT_THRESHOLD
        )
        exact = calculate_fee(
            base_price=Decimal("10000"), quantity=1, monthly_volume=VOLUME_DISCOUNT_THRESHOLD + 1
        )
        assert below > exact  # discount kicks in above threshold


class TestApplyQualityDiscount:
    def test_zero_score(self):
        result = apply_quality_discount(Decimal("10000"), 0.0)
        assert result == Decimal("10000")

    def test_perfect_score(self):
        result = apply_quality_discount(Decimal("10000"), 1.0)
        expected = Decimal("10000") - Decimal("10000") * Decimal("0.05")
        assert result == expected.quantize(Decimal("1"))

    def test_mid_score(self):
        result = apply_quality_discount(Decimal("10000"), 0.5)
        expected = Decimal("10000") - Decimal("10000") * Decimal("0.5") * Decimal("0.05")
        assert result == expected.quantize(Decimal("1"))

    def test_minimum_bill_enforced(self):
        result = apply_quality_discount(Decimal("100"), 1.0)
        assert result >= MINIMUM_BILL

    def test_invalid_low_score_raises(self):
        with pytest.raises(ValueError, match=r"quality_score must be 0.0–1.0"):
            apply_quality_discount(Decimal("10000"), -0.1)

    def test_invalid_high_score_raises(self):
        with pytest.raises(ValueError, match=r"quality_score must be 0.0–1.0"):
            apply_quality_discount(Decimal("10000"), 1.1)


class TestEnforceMinimumBill:
    def test_above_minimum(self):
        assert enforce_minimum_bill(Decimal("10000")) == Decimal("10000")

    def test_below_minimum(self):
        assert enforce_minimum_bill(Decimal("1000")) == MINIMUM_BILL

    def test_at_minimum(self):
        assert enforce_minimum_bill(MINIMUM_BILL) == MINIMUM_BILL

    def test_zero(self):
        assert enforce_minimum_bill(Decimal("0")) == MINIMUM_BILL

    def test_negative(self):
        assert enforce_minimum_bill(Decimal("-500")) == MINIMUM_BILL


# ── Service Layer Edge Cases ──────────────────────────────────────────


@pytest.fixture(autouse=True)
def _enable_financial_engine(monkeypatch):
    monkeypatch.setattr("app.config.ENABLE_FINANCIAL_ENGINE", True)
    monkeypatch.setattr("app.financial.ENABLE_FINANCIAL_ENGINE", True)
    monkeypatch.setattr("app.financial.services._engine_enabled", lambda: True)


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


class TestInvoiceServiceEdgeCases:
    def test_create_with_items(self, db):
        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        items = [
            {"description": "CBC Test", "quantity": 2, "unit_price": 5000, "total_price": 10000},
            {"description": "Blood Sugar", "quantity": 1, "unit_price": 3000, "total_price": 3000},
        ]
        result = InvoiceService.create_invoice(
            db=db,
            lab_id=1,
            subscription_id=s.id,
            amount=Decimal("13000.00"),
            items=items,
        )
        assert result["lab_id"] == 1
        invoice_items = (
            db.query(FinInvoiceItem).filter(FinInvoiceItem.invoice_id == result["id"]).all()
        )
        assert len(invoice_items) == 2
        assert invoice_items[0].description == "CBC Test"

    def test_create_without_subscription(self, db):
        _create_provider(db, lab_id=2)
        result = InvoiceService.create_invoice(
            db=db,
            lab_id=2,
            subscription_id=None,
            amount=Decimal("25000.00"),
        )
        assert result["lab_id"] == 2
        assert result["status"] == "issued"

    def test_list_invoices_status_filter(self, db):
        from datetime import date, timedelta

        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        InvoiceService.create_invoice(
            db=db, lab_id=1, subscription_id=s.id, amount=Decimal("10000.00")
        )
        InvoiceService.create_invoice(
            db=db, lab_id=1, subscription_id=s.id, amount=Decimal("20000.00")
        )
        issued = InvoiceService.list_invoices(db, lab_id=1, status="issued")
        assert len(issued) >= 2
        paid = InvoiceService.list_invoices(db, lab_id=1, status="paid")
        assert len(paid) == 0

    def test_list_invoices_pagination(self, db):
        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        for i in range(5):
            InvoiceService.create_invoice(
                db=db, lab_id=1, subscription_id=s.id, amount=Decimal(f"{i + 1}0000.00")
            )
        page1 = InvoiceService.list_invoices(db, lab_id=1, limit=2, offset=0)
        page2 = InvoiceService.list_invoices(db, lab_id=1, limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0]["id"] != page2[0]["id"]


class TestPaymentServiceEdgeCases:
    def test_different_methods(self, db):
        from app.financial.services import InvoiceService, PaymentService

        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        inv = InvoiceService.create_invoice(
            db=db, lab_id=1, subscription_id=s.id, amount=Decimal("50000.00")
        )
        for method in ["bank_transfer", "credit_card", "cash", "check"]:
            result = PaymentService.process_payment(
                db=db,
                invoice_id=inv["id"],
                lab_id=1,
                amount=Decimal("10000.00"),
                method=method,
                reference=f"ref-{method}",
            )
            assert result["method"] == method
            assert result["reference"] == f"ref-{method}"

    def test_with_reference_and_notes(self, db):
        from app.financial.services import InvoiceService, PaymentService

        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        inv = InvoiceService.create_invoice(
            db=db, lab_id=1, subscription_id=s.id, amount=Decimal("30000.00")
        )
        result = PaymentService.process_payment(
            db=db,
            invoice_id=inv["id"],
            lab_id=1,
            amount=Decimal("30000.00"),
            reference="TXN-001",
            notes="Test payment",
        )
        assert result["reference"] == "TXN-001"
        assert result["notes"] == "Test payment"

    def test_payment_lab_isolation_wrong_lab(self, db):
        from app.financial.services import InvoiceService, PaymentService

        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        inv = InvoiceService.create_invoice(
            db=db, lab_id=1, subscription_id=s.id, amount=Decimal("10000.00")
        )
        with pytest.raises(ValueError, match="Invoice not found"):
            PaymentService.process_payment(
                db=db, invoice_id=inv["id"], lab_id=999, amount=Decimal("10000.00")
            )


class TestPayableService:
    def test_get_payables_empty(self, db):
        p = _create_provider(db, lab_id=1)
        payables = PayableService.get_payables(db, provider_id=p.id)
        assert payables == []

    def test_get_payables_with_data(self, db):
        p = _create_provider(db, lab_id=1)
        payable = FinPayable(
            provider_id=p.id,
            amount=Decimal("50000.00"),
            currency="IQD",
            status="pending",
        )
        db.add(payable)
        db.flush()
        payables = PayableService.get_payables(db, provider_id=p.id)
        assert len(payables) == 1
        assert payables[0]["amount"] == Decimal("50000.00")

    def test_get_payables_provider_isolation(self, db):
        p1 = _create_provider(db, lab_id=1)
        p2 = _create_provider(db, lab_id=2)
        db.add(
            FinPayable(provider_id=p1.id, amount=Decimal("10000"), currency="IQD", status="pending")
        )
        db.add(
            FinPayable(provider_id=p2.id, amount=Decimal("20000"), currency="IQD", status="pending")
        )
        db.flush()
        assert len(PayableService.get_payables(db, provider_id=p1.id)) == 1
        assert len(PayableService.get_payables(db, provider_id=p2.id)) == 1


class TestReceivableServiceEdgeCases:
    def test_get_receivables_empty(self, db):
        receivables = ReceivableService.get_receivables(db, lab_id=999)
        assert receivables == []

    def test_get_aging_summary_empty(self, db):
        summary = ReceivableService.get_aging_summary(db, lab_id=999)
        assert summary == {
            "0-30": Decimal("0"),
            "31-60": Decimal("0"),
            "61-90": Decimal("0"),
            "90+": Decimal("0"),
        }

    def test_get_receivables_only_unpaid(self, db):
        from app.financial.services import InvoiceService, PaymentService

        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        inv = InvoiceService.create_invoice(
            db=db, lab_id=1, subscription_id=s.id, amount=Decimal("50000.00")
        )
        PaymentService.process_payment(
            db=db, invoice_id=inv["id"], lab_id=1, amount=Decimal("50000.00")
        )
        receivables = ReceivableService.get_receivables(db, lab_id=1)
        # paid invoices should not appear in receivables
        assert all(r["status"] != "paid" for r in receivables)


class TestBillingServiceEdgeCases:
    def test_no_subscriptions(self, db):
        results = BillingService.run_billing_cycle(db)
        assert results == []

    def test_inactive_subscription_skipped(self, db):
        p = _create_provider(db, lab_id=1)
        _create_subscription(db, provider_id=p.id, status="inactive")
        results = BillingService.run_billing_cycle(db)
        assert results == []

    def test_subscription_without_provider(self, db):
        _create_subscription(db, provider_id=99999)
        results = BillingService.run_billing_cycle(db)
        # subscription with non-existent provider should be skipped
        assert results == []


class TestPricingServiceEdgeCases:
    def test_get_price_with_quality_score(self, db):
        rule = FinPricingRule(
            name="Lipid Panel",
            test_type="LIPID",
            base_price=Decimal("25000"),
            active=True,
        )
        db.add(rule)
        db.flush()
        result = PricingService.get_price(
            db, test_name="LIPID", lab_id=1, quantity=1, quality_score=0.9
        )
        assert result["quality_discount_pct"] == 5.0
        assert result["total"] < result["base_price"]

    def test_get_price_with_volume(self, db):
        result = PricingService.get_price(
            db,
            test_name="ANY",
            lab_id=1,
            quantity=1,
            monthly_volume=200,
        )
        assert result["volume_discount_pct"] == 10.0

    def test_create_rule_with_discounts(self, db):
        result = PricingService.create_rule(
            db=db,
            name="Advanced CBC",
            test_type="CBC-ADV",
            base_price=Decimal("20000"),
            quality_discount_pct=10.0,
            volume_discount_pct=5.0,
        )
        assert result["name"] == "Advanced CBC"
        assert result["base_price"] == Decimal("20000")

    def test_create_rule_no_test_type(self, db):
        result = PricingService.create_rule(
            db=db,
            name="Generic",
            test_type=None,
            base_price=Decimal("5000"),
        )
        assert result["test_type"] is None


class TestFinancialReportServiceEdgeCases:
    def test_generate_report_no_payments(self, db):
        from app.financial.services import InvoiceService

        p = _create_provider(db, lab_id=1)
        s = _create_subscription(db, provider_id=p.id)
        InvoiceService.create_invoice(
            db=db, lab_id=1, subscription_id=s.id, amount=Decimal("50000.00")
        )
        report = FinancialReportService.generate_report(
            db=db,
            lab_id=1,
            date_from=date(2020, 1, 1),
            date_to=date(2030, 12, 31),
        )
        assert report["total_invoiced"] == Decimal("50000.00")
        assert report["total_collected"] == Decimal("0")
        assert report["total_outstanding"] == Decimal("50000.00")
        assert report["invoice_count"] >= 1
        assert report["payment_count"] == 0

    def test_generate_report_group_by(self, db):
        report = FinancialReportService.generate_report(
            db=db,
            lab_id=1,
            date_from=date(2024, 1, 1),
            date_to=date(2024, 12, 31),
            group_by="quarter",
        )
        assert report["group_by"] == "quarter"
        assert len(report["breakdown"]) >= 1


class TestEngineDisabled:
    def test_billing_service_returns_empty(self, monkeypatch, db):
        monkeypatch.setattr("app.financial.services._engine_enabled", lambda: False)
        from app.financial.services import _engine_enabled

        assert _engine_enabled() is False
        results = BillingService.run_billing_cycle(db)
        assert results == []

    def test_invoice_service_returns_empty(self, monkeypatch, db):
        monkeypatch.setattr("app.financial.services._engine_enabled", lambda: False)
        result = InvoiceService.create_invoice(db=db, lab_id=1, amount=Decimal("10000"))
        assert result == {}

    def test_payment_service_returns_empty(self, monkeypatch, db):
        monkeypatch.setattr("app.financial.services._engine_enabled", lambda: False)
        result = PaymentService.process_payment(
            db=db, invoice_id=1, lab_id=1, amount=Decimal("10000")
        )
        assert result == {}
