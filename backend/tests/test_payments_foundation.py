from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from app.financial.models import FinBase
from app.payments.models import LedgerLine, PaymentAuditEvent, PaymentIntent, PaymentInvoice
from app.payments.schemas import InvoiceLineCreate
from app.payments.service import PaymentService, PaymentStateError


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


def issue_invoice(service: PaymentService, actor_id: int = 101):
    return service.create_invoice(
        institution_id=12,
        patient_reference="PATIENT-REFERENCE-ONLY",
        due_at=None,
        lines=[
            InvoiceLineCreate(
                description="CBC test",
                service_reference="SERVICE-CBC",
                quantity=1,
                unit_amount=Decimal("10000.00"),
            )
        ],
        actor_user_id=actor_id,
    )


def test_cash_capture_creates_a_balanced_double_entry_and_audit_event(db):
    service = PaymentService(db)
    invoice = issue_invoice(service)
    shift = service.open_cash_shift(
        institution_id=12,
        cashier_user_id=101,
        terminal_reference="CASH-01",
        opening_float=Decimal("1000.00"),
    )
    intent = service.create_intent(
        institution_id=12,
        invoice_id=invoice.id,
        amount=Decimal("10000.00"),
        method="CASH",
        idempotency_key="request-001",
        expires_at=None,
        actor_user_id=101,
    )

    attempt = service.capture_cash(
        institution_id=12,
        intent_id=intent.id,
        cash_shift_id=shift.id,
        cashier_reference="CASH-RECEIPT-001",
        actor_user_id=101,
    )
    db.flush()

    refreshed_invoice = db.query(PaymentInvoice).filter_by(id=invoice.id).one()
    refreshed_intent = db.query(PaymentIntent).filter_by(id=intent.id).one()
    lines = db.query(LedgerLine).all()
    debit_total = db.query(func.coalesce(func.sum(LedgerLine.debit_amount), 0)).scalar()
    credit_total = db.query(func.coalesce(func.sum(LedgerLine.credit_amount), 0)).scalar()

    assert attempt.status == "SUCCEEDED"
    assert refreshed_intent.status == "SUCCEEDED"
    assert refreshed_invoice.status == "PAID"
    assert Decimal(refreshed_invoice.paid_amount) == Decimal("10000.00")
    assert len(lines) == 2
    assert Decimal(debit_total) == Decimal("10000.00")
    assert Decimal(credit_total) == Decimal("10000.00")
    assert db.query(PaymentAuditEvent).filter_by(entity_id=attempt.id, action="CASH_CAPTURED").count() == 1


def test_idempotency_returns_original_intent_and_rejects_different_payload(db):
    service = PaymentService(db)
    invoice = issue_invoice(service)
    first = service.create_intent(
        institution_id=12,
        invoice_id=invoice.id,
        amount=Decimal("4000.00"),
        method="CASH",
        idempotency_key="same-operation",
        expires_at=None,
        actor_user_id=101,
    )
    repeated = service.create_intent(
        institution_id=12,
        invoice_id=invoice.id,
        amount=Decimal("4000.00"),
        method="CASH",
        idempotency_key="same-operation",
        expires_at=None,
        actor_user_id=101,
    )

    assert repeated.id == first.id
    with pytest.raises(Exception, match="Idempotency key"):
        service.create_intent(
            institution_id=12,
            invoice_id=invoice.id,
            amount=Decimal("5000.00"),
            method="CASH",
            idempotency_key="same-operation",
            expires_at=None,
            actor_user_id=101,
        )


def test_refund_requires_separate_approver_and_adjusts_cash_shift_expected_balance(db):
    service = PaymentService(db)
    invoice = issue_invoice(service, actor_id=101)
    shift = service.open_cash_shift(
        institution_id=12,
        cashier_user_id=101,
        terminal_reference="CASH-02",
        opening_float=Decimal("1000.00"),
    )
    intent = service.create_intent(
        institution_id=12,
        invoice_id=invoice.id,
        amount=Decimal("10000.00"),
        method="CASH",
        idempotency_key="refund-flow",
        expires_at=None,
        actor_user_id=101,
    )
    service.capture_cash(
        institution_id=12,
        intent_id=intent.id,
        cash_shift_id=shift.id,
        cashier_reference="CASH-RECEIPT-002",
        actor_user_id=101,
    )
    refund = service.request_refund(
        institution_id=12,
        payment_intent_id=intent.id,
        amount=Decimal("3000.00"),
        reason="Service not delivered",
        external_reference=None,
        actor_user_id=101,
    )

    with pytest.raises(Exception, match="different authorized user"):
        service.approve_refund(institution_id=12, refund_id=refund.id, actor_user_id=101)

    service.approve_refund(institution_id=12, refund_id=refund.id, actor_user_id=202)
    completed = service.process_cash_refund(
        institution_id=12,
        refund_id=refund.id,
        cash_shift_id=shift.id,
        cashier_reference="CASH-REFUND-002",
        actor_user_id=202,
    )
    closed, reconciliation_case = service.close_cash_shift(
        institution_id=12,
        shift_id=shift.id,
        actual_closing=Decimal("8000.00"),
        variance_reason=None,
        actor_user_id=202,
    )
    db.flush()

    refreshed_invoice = db.query(PaymentInvoice).filter_by(id=invoice.id).one()
    assert completed.status == "SUCCEEDED"
    assert Decimal(refreshed_invoice.refunded_amount) == Decimal("3000.00")
    assert refreshed_invoice.status == "PARTIALLY_REFUNDED"
    assert closed.status == "CLOSED_MATCHED"
    assert Decimal(closed.expected_closing) == Decimal("8000.00")
    assert reconciliation_case is None


def test_cash_shift_variance_creates_an_exception_case(db):
    service = PaymentService(db)
    shift = service.open_cash_shift(
        institution_id=12,
        cashier_user_id=101,
        terminal_reference="CASH-03",
        opening_float=Decimal("1000.00"),
    )
    closed, reconciliation_case = service.close_cash_shift(
        institution_id=12,
        shift_id=shift.id,
        actual_closing=Decimal("995.00"),
        variance_reason="Counted by supervisor",
        actor_user_id=202,
    )

    assert closed.status == "CLOSED_VARIANCE"
    assert Decimal(closed.variance_amount) == Decimal("-5.00")
    assert reconciliation_case is not None
    assert reconciliation_case.status == "AMOUNT_MISMATCH"


def test_tenant_isolation_blocks_cross_institution_access(db):
    service = PaymentService(db)
    actor = SimpleNamespace(id=100, lab_id=12, role="lab_staff")
    service.assert_institution_access(actor, 12)
    with pytest.raises(Exception, match="Cross-institution"):
        service.assert_institution_access(actor, 13)
