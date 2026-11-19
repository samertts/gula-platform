"""Business rules for GULA Health Payments P0.

All state transitions and ledger posting live here.  Routes must not mutate
payment records directly.  Provider adapters are intentionally absent from the
P0 write path; cash is the only capturable payment method in this release.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC
from app.domain.exceptions import ConflictError, NotFoundError, ServiceError

from .state_machine import transition_payment, transition_refund

from .models import (
    CashShift,
    LedgerAccount,
    LedgerEntry,
    LedgerLine,
    PaymentAttempt,
    PaymentAuditEvent,
    PaymentIntent,
    PaymentInvoice,
    PaymentInvoiceLine,
    PaymentProvider,
    PaymentRefund,
    ReconciliationCase,
)

MONEY_QUANTUM = Decimal("0.01")
PLATFORM_ROLES = {"master_admin", "ministry_admin", "province_admin"}


def now_utc() -> datetime:
    return datetime.now(UTC)


def normalize_utc(value: datetime) -> datetime:
    """Treat legacy/SQLite naive timestamps as UTC; normalize aware values."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class PaymentStateError(ServiceError):
    """A prohibited payment-state transition."""

    def __init__(self, message: str):
        super().__init__(message, status_code=409)


def money(value: Decimal | int | str) -> Decimal:
    amount = Decimal(value).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
    if amount < 0:
        raise ServiceError("Amount cannot be negative")
    return amount


class PaymentService:
    def __init__(self, db: Session):
        self.db = db

    def assert_institution_access(self, actor: Any, institution_id: int) -> None:
        """Apply tenant isolation before any read or mutation."""
        if getattr(actor, "role", None) in PLATFORM_ROLES:
            return
        if getattr(actor, "lab_id", None) != institution_id:
            raise ServiceError("Cross-institution payment access is not allowed", status_code=403)

    def _audit(
        self,
        institution_id: int,
        entity_type: str,
        entity_id: str,
        action: str,
        actor_user_id: int | None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.db.add(
            PaymentAuditEvent(
                institution_id=institution_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                actor_user_id=actor_user_id,
                safe_metadata=metadata or {},
            )
        )

    def _invoice(
        self, invoice_id: str, institution_id: int | None = None, *, for_update: bool = False
    ) -> PaymentInvoice:
        query = self.db.query(PaymentInvoice).filter(PaymentInvoice.id == invoice_id)
        if institution_id is not None:
            query = query.filter(PaymentInvoice.institution_id == institution_id)
        if for_update:
            query = query.with_for_update()
        invoice = query.first()
        if invoice is None:
            raise NotFoundError("Payment invoice not found")
        return invoice

    def _intent(
        self, intent_id: str, institution_id: int | None = None, *, for_update: bool = False
    ) -> PaymentIntent:
        query = self.db.query(PaymentIntent).filter(PaymentIntent.id == intent_id)
        if institution_id is not None:
            query = query.filter(PaymentIntent.institution_id == institution_id)
        if for_update:
            query = query.with_for_update()
        intent = query.first()
        if intent is None:
            raise NotFoundError("Payment intent not found")
        return intent

    def _refund(
        self, refund_id: str, institution_id: int | None = None, *, for_update: bool = False
    ) -> PaymentRefund:
        query = self.db.query(PaymentRefund).filter(PaymentRefund.id == refund_id)
        if institution_id is not None:
            query = query.filter(PaymentRefund.institution_id == institution_id)
        if for_update:
            query = query.with_for_update()
        refund = query.first()
        if refund is None:
            raise NotFoundError("Payment refund not found")
        return refund

    def _cash_shift(self, shift_id: str, institution_id: int, *, for_update: bool = False) -> CashShift:
        query = self.db.query(CashShift).filter(
            CashShift.id == shift_id, CashShift.institution_id == institution_id
        )
        if for_update:
            query = query.with_for_update()
        shift = query.first()
        if shift is None:
            raise NotFoundError("Cash shift not found")
        return shift

    def _ensure_provider(self, code: str, display_name: str, provider_type: str) -> PaymentProvider:
        provider = self.db.query(PaymentProvider).filter(PaymentProvider.code == code).first()
        if provider is None:
            provider = PaymentProvider(
                code=code,
                display_name=display_name,
                provider_type=provider_type,
                environment="sandbox",
                status="INTERNAL_ONLY" if code == "cashier" else "PENDING_REVIEW",
                supports_refund=(code == "cashier"),
                supports_reconciliation=(code == "cashier"),
            )
            self.db.add(provider)
            self.db.flush()
        return provider

    def _account(self, institution_id: int, code: str, name: str, account_type: str) -> LedgerAccount:
        account = (
            self.db.query(LedgerAccount)
            .filter(LedgerAccount.institution_id == institution_id, LedgerAccount.code == code)
            .first()
        )
        if account is None:
            account = LedgerAccount(
                institution_id=institution_id,
                code=code,
                name=name,
                account_type=account_type,
                currency="IQD",
            )
            self.db.add(account)
            self.db.flush()
        if not account.active:
            raise PaymentStateError(f"Ledger account {code} is inactive")
        return account

    def _post_entry(
        self,
        institution_id: int,
        reference_type: str,
        reference_id: str,
        description: str,
        lines: Iterable[tuple[LedgerAccount, Decimal, Decimal]],
        actor_user_id: int | None,
        reversal_of_entry_id: str | None = None,
    ) -> LedgerEntry:
        prepared = [(account, money(debit), money(credit)) for account, debit, credit in lines]
        if len(prepared) < 2:
            raise ServiceError("A ledger entry requires at least two lines")
        total_debit = sum((debit for _, debit, _ in prepared), Decimal("0.00"))
        total_credit = sum((credit for _, _, credit in prepared), Decimal("0.00"))
        if total_debit <= 0 or total_debit != total_credit:
            raise ServiceError("Ledger entry must balance", status_code=422)
        if any((debit > 0) == (credit > 0) for _, debit, credit in prepared):
            raise ServiceError("Every ledger line must have exactly one positive side", status_code=422)

        entry = LedgerEntry(
            institution_id=institution_id,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
            posted_by=actor_user_id,
            reversal_of_entry_id=reversal_of_entry_id,
        )
        self.db.add(entry)
        self.db.flush()
        for account, debit, credit in prepared:
            self.db.add(
                LedgerLine(
                    entry_id=entry.id,
                    account_id=account.id,
                    debit_amount=debit,
                    credit_amount=credit,
                    currency="IQD",
                )
            )
        return entry

    def create_invoice(
        self,
        *,
        institution_id: int,
        patient_reference: str | None,
        due_at: datetime | None,
        lines: list[Any],
        actor_user_id: int,
    ) -> PaymentInvoice:
        if not lines:
            raise ServiceError("An invoice requires at least one line")
        line_values: list[tuple[Any, Decimal]] = []
        total = Decimal("0.00")
        for line in lines:
            unit_amount = money(line.unit_amount)
            if unit_amount <= 0:
                raise ServiceError("Invoice line amount must be positive")
            line_total = money(unit_amount * line.quantity)
            line_values.append((line, line_total))
            total += line_total
        total = money(total)
        number = f"GHP-{institution_id}-{now_utc():%Y%m%d%H%M%S}-{uuid4().hex[:6].upper()}"
        invoice = PaymentInvoice(
            institution_id=institution_id,
            patient_reference=patient_reference,
            invoice_number=number,
            status="ISSUED",
            currency="IQD",
            total_amount=total,
            paid_amount=Decimal("0.00"),
            refunded_amount=Decimal("0.00"),
            issued_at=now_utc(),
            due_at=due_at,
            created_by=actor_user_id,
        )
        self.db.add(invoice)
        self.db.flush()
        for position, (line, line_total) in enumerate(line_values, start=1):
            self.db.add(
                PaymentInvoiceLine(
                    invoice_id=invoice.id,
                    line_number=position,
                    service_reference=line.service_reference,
                    description=line.description,
                    quantity=line.quantity,
                    unit_amount=money(line.unit_amount),
                    line_amount=line_total,
                )
            )
        self._audit(
            institution_id,
            "invoice",
            invoice.id,
            "ISSUED",
            actor_user_id,
            {"invoice_number": number, "amount": str(total), "currency": "IQD"},
        )
        return invoice

    def create_intent(
        self,
        *,
        institution_id: int,
        invoice_id: str,
        amount: Decimal,
        method: str,
        idempotency_key: str,
        expires_at: datetime | None,
        actor_user_id: int,
    ) -> PaymentIntent:
        normalized_key = idempotency_key.strip()
        if not normalized_key or len(normalized_key) > 128:
            raise ServiceError("A valid Idempotency-Key header is required", status_code=400)
        amount = money(amount)
        if amount <= 0:
            raise ServiceError("Payment amount must be positive")

        existing = (
            self.db.query(PaymentIntent)
            .filter(
                PaymentIntent.institution_id == institution_id,
                PaymentIntent.idempotency_key == normalized_key,
            )
            .first()
        )
        if existing is not None:
            same_request = (
                existing.invoice_id == invoice_id
                and money(existing.amount) == amount
                and existing.method == method
            )
            if not same_request:
                raise ConflictError("Idempotency key has already been used for a different payment request")
            return existing

        invoice = self._invoice(invoice_id, institution_id)
        if invoice.status in {"VOID", "REFUNDED"}:
            raise PaymentStateError("Cannot create a payment intent for this invoice")
        outstanding = money(invoice.total_amount - invoice.paid_amount)
        if amount > outstanding:
            raise PaymentStateError("Payment amount exceeds the outstanding invoice balance")
        if expires_at is not None and normalize_utc(expires_at) <= now_utc():
            raise ServiceError("Payment intent expiration must be in the future")

        intent = PaymentIntent(
            institution_id=institution_id,
            invoice_id=invoice.id,
            idempotency_key=normalized_key,
            amount=amount,
            currency="IQD",
            method=method,
            status="PENDING",
            expires_at=expires_at,
            created_by=actor_user_id,
        )
        self.db.add(intent)
        self.db.flush()
        self._audit(
            institution_id,
            "payment_intent",
            intent.id,
            "CREATED",
            actor_user_id,
            {"invoice_id": invoice.id, "amount": str(amount), "method": method},
        )
        return intent

    def open_cash_shift(
        self,
        *,
        institution_id: int,
        cashier_user_id: int,
        terminal_reference: str,
        opening_float: Decimal,
    ) -> CashShift:
        existing = (
            self.db.query(CashShift)
            .filter(
                CashShift.institution_id == institution_id,
                CashShift.cashier_user_id == cashier_user_id,
                CashShift.terminal_reference == terminal_reference,
                CashShift.status == "OPEN",
            )
            .first()
        )
        if existing is not None:
            raise ConflictError("An open cash shift already exists for this terminal and cashier")
        opening_float = money(opening_float)
        shift = CashShift(
            institution_id=institution_id,
            cashier_user_id=cashier_user_id,
            terminal_reference=terminal_reference,
            opening_float=opening_float,
            currency="IQD",
            status="OPEN",
        )
        self.db.add(shift)
        self.db.flush()
        self._ensure_provider("cashier", "GULA Cashier", "cash")
        self._account(institution_id, "CASH_ON_HAND", "Cash on hand", "asset")
        self._account(institution_id, "ACCOUNTS_RECEIVABLE", "Patient receivables", "asset")
        self._account(institution_id, "REFUNDS_AND_ALLOWANCES", "Refunds and allowances", "expense")
        self._audit(
            institution_id,
            "cash_shift",
            shift.id,
            "OPENED",
            cashier_user_id,
            {"terminal_reference": terminal_reference, "opening_float": str(opening_float)},
        )
        return shift

    def capture_cash(
        self,
        *,
        institution_id: int,
        intent_id: str,
        cash_shift_id: str,
        cashier_reference: str,
        actor_user_id: int,
    ) -> PaymentAttempt:
        intent = self._intent(intent_id, institution_id, for_update=True)
        if intent.method != "CASH":
            raise PaymentStateError("Only CASH payment intents can be captured by the cashier")
        if intent.expires_at is not None and normalize_utc(intent.expires_at) <= now_utc():
            transition_payment(intent, "EXPIRED")
            raise PaymentStateError("Payment intent has expired")
        successful = (
            self.db.query(PaymentAttempt)
            .filter(PaymentAttempt.intent_id == intent.id, PaymentAttempt.status == "SUCCEEDED")
            .first()
        )
        if successful is not None:
            return successful
        if intent.status not in {"PENDING", "PROCESSING"}:
            raise PaymentStateError("Payment intent cannot be captured in its current state")
        shift = self._cash_shift(cash_shift_id, institution_id, for_update=True)
        if shift.status != "OPEN":
            raise PaymentStateError("Cash shift is not open")
        invoice = self._invoice(intent.invoice_id, institution_id, for_update=True)
        if money(intent.amount) > money(invoice.total_amount - invoice.paid_amount):
            raise PaymentStateError("Invoice balance has changed; create a new payment intent")
        duplicate_reference = (
            self.db.query(PaymentAttempt)
            .filter(
                PaymentAttempt.provider_code == "cashier",
                PaymentAttempt.provider_transaction_id == cashier_reference,
            )
            .first()
        )
        if duplicate_reference is not None:
            raise ConflictError("Cashier reference has already been used")

        transition_payment(intent, "PROCESSING")
        attempt = PaymentAttempt(
            intent_id=intent.id,
            cash_shift_id=shift.id,
            provider_code="cashier",
            provider_transaction_id=cashier_reference,
            amount=intent.amount,
            currency="IQD",
            status="SUCCEEDED",
            verified_at=now_utc(),
            safe_provider_metadata={"verification": "cashier_operator_confirmed"},
        )
        self.db.add(attempt)
        self.db.flush()
        transition_payment(intent, "SUCCEEDED")
        invoice.paid_amount = money(invoice.paid_amount + intent.amount)
        invoice.status = "PAID" if money(invoice.paid_amount) == money(invoice.total_amount) else "PARTIALLY_PAID"

        cash_account = self._account(institution_id, "CASH_ON_HAND", "Cash on hand", "asset")
        receivable_account = self._account(
            institution_id, "ACCOUNTS_RECEIVABLE", "Patient receivables", "asset"
        )
        self._post_entry(
            institution_id,
            "cash_payment",
            attempt.id,
            "Cash receipt against patient invoice",
            [(cash_account, intent.amount, Decimal("0.00")), (receivable_account, Decimal("0.00"), intent.amount)],
            actor_user_id,
        )
        self._audit(
            institution_id,
            "payment_attempt",
            attempt.id,
            "CASH_CAPTURED",
            actor_user_id,
            {"intent_id": intent.id, "invoice_id": invoice.id, "amount": str(intent.amount), "cash_shift_id": shift.id},
        )
        return attempt

    def close_cash_shift(
        self,
        *,
        institution_id: int,
        shift_id: str,
        actual_closing: Decimal,
        variance_reason: str | None,
        actor_user_id: int,
    ) -> tuple[CashShift, ReconciliationCase | None]:
        shift = self._cash_shift(shift_id, institution_id, for_update=True)
        if shift.status != "OPEN":
            raise PaymentStateError("Cash shift is already closed")
        # Aggregate queries below must include captures/refunds created in this transaction.
        self.db.flush()
        actual_closing = money(actual_closing)
        captured = (
            self.db.query(func.coalesce(func.sum(PaymentAttempt.amount), 0))
            .filter(PaymentAttempt.cash_shift_id == shift.id, PaymentAttempt.status == "SUCCEEDED")
            .scalar()
        )
        refunded = (
            self.db.query(func.coalesce(func.sum(PaymentRefund.amount), 0))
            .filter(PaymentRefund.cash_shift_id == shift.id, PaymentRefund.status == "SUCCEEDED")
            .scalar()
        )
        expected = money(
            shift.opening_float + (captured or Decimal("0.00")) - (refunded or Decimal("0.00"))
        )
        variance = money(actual_closing - expected) if actual_closing >= expected else -money(expected - actual_closing)
        if variance != 0 and not variance_reason:
            raise ServiceError("A variance reason is required when the cash drawer does not match")

        shift.expected_closing = expected
        shift.actual_closing = actual_closing
        shift.variance_amount = variance
        shift.variance_reason = variance_reason
        shift.closed_at = now_utc()
        shift.status = "CLOSED_MATCHED" if variance == 0 else "CLOSED_VARIANCE"
        reconciliation_case: ReconciliationCase | None = None
        if variance != 0:
            reconciliation_case = ReconciliationCase(
                institution_id=institution_id,
                source_type="cash_shift",
                source_reference=shift.id,
                status="AMOUNT_MISMATCH",
                expected_amount=expected,
                observed_amount=actual_closing,
                currency="IQD",
                discrepancy_reason=variance_reason or "Cash drawer variance",
            )
            self.db.add(reconciliation_case)
            self.db.flush()
        self._audit(
            institution_id,
            "cash_shift",
            shift.id,
            "CLOSED",
            actor_user_id,
            {
                "expected_closing": str(expected),
                "actual_closing": str(actual_closing),
                "variance": str(variance),
                "reconciliation_case_id": reconciliation_case.id if reconciliation_case else None,
            },
        )
        return shift, reconciliation_case

    def request_refund(
        self,
        *,
        institution_id: int,
        payment_intent_id: str,
        amount: Decimal,
        reason: str,
        external_reference: str | None,
        actor_user_id: int,
    ) -> PaymentRefund:
        intent = self._intent(payment_intent_id, institution_id, for_update=True)
        if intent.status != "SUCCEEDED":
            raise PaymentStateError("Refunds are only available for successful payment intents")
        amount = money(amount)
        reserved = (
            self.db.query(func.coalesce(func.sum(PaymentRefund.amount), 0))
            .filter(
                PaymentRefund.payment_intent_id == intent.id,
                PaymentRefund.status.in_({"REQUESTED", "APPROVED", "PROCESSING", "SUCCEEDED"}),
            )
            .scalar()
        )
        if amount > money(intent.amount - (reserved or Decimal("0.00"))):
            raise PaymentStateError("Refund amount exceeds the remaining refundable amount")
        refund = PaymentRefund(
            institution_id=institution_id,
            invoice_id=intent.invoice_id,
            payment_intent_id=intent.id,
            amount=amount,
            currency="IQD",
            reason=reason,
            external_reference=external_reference,
            status="REQUESTED",
            requested_by=actor_user_id,
        )
        self.db.add(refund)
        self.db.flush()
        self._audit(
            institution_id,
            "refund",
            refund.id,
            "REQUESTED",
            actor_user_id,
            {"payment_intent_id": intent.id, "amount": str(amount)},
        )
        return refund

    def approve_refund(self, *, institution_id: int, refund_id: str, actor_user_id: int) -> PaymentRefund:
        refund = self._refund(refund_id, institution_id, for_update=True)
        if refund.status != "REQUESTED":
            raise PaymentStateError("Only requested refunds can be approved")
        if refund.requested_by == actor_user_id:
            raise ServiceError("Refund approval requires a different authorized user", status_code=403)
        transition_refund(refund, "APPROVED")
        refund.approved_by = actor_user_id
        self._audit(institution_id, "refund", refund.id, "APPROVED", actor_user_id, {})
        return refund

    def process_cash_refund(
        self,
        *,
        institution_id: int,
        refund_id: str,
        cash_shift_id: str,
        cashier_reference: str,
        actor_user_id: int,
    ) -> PaymentRefund:
        refund = self._refund(refund_id, institution_id, for_update=True)
        if refund.status != "APPROVED":
            raise PaymentStateError("Only approved refunds can be processed")
        intent = self._intent(refund.payment_intent_id, institution_id)
        if intent.method != "CASH":
            raise PaymentStateError("P0 can process cash refunds only; electronic refunds require a provider adapter")
        shift = self._cash_shift(cash_shift_id, institution_id, for_update=True)
        if shift.status != "OPEN":
            raise PaymentStateError("Cash refunds require an open cash shift")
        invoice = self._invoice(refund.invoice_id, institution_id, for_update=True)
        transition_refund(refund, "PROCESSING")
        refund.cash_shift_id = shift.id
        cash_account = self._account(institution_id, "CASH_ON_HAND", "Cash on hand", "asset")
        refund_account = self._account(
            institution_id, "REFUNDS_AND_ALLOWANCES", "Refunds and allowances", "expense"
        )
        entry = self._post_entry(
            institution_id,
            "cash_refund",
            refund.id,
            "Cash refund against a successful payment",
            [(refund_account, refund.amount, Decimal("0.00")), (cash_account, Decimal("0.00"), refund.amount)],
            actor_user_id,
        )
        transition_refund(refund, "SUCCEEDED")
        refund.external_reference = cashier_reference
        refund.processed_at = now_utc()
        invoice.refunded_amount = money(invoice.refunded_amount + refund.amount)
        invoice.status = "REFUNDED" if money(invoice.refunded_amount) == money(invoice.paid_amount) else "PARTIALLY_REFUNDED"
        self._audit(
            institution_id,
            "refund",
            refund.id,
            "CASH_REFUNDED",
            actor_user_id,
            {"cash_shift_id": shift.id, "ledger_entry_id": entry.id, "amount": str(refund.amount)},
        )
        return refund

    def invoice_summary(self, invoice: PaymentInvoice) -> dict[str, Any]:
        return {
            "id": invoice.id,
            "institution_id": invoice.institution_id,
            "invoice_number": invoice.invoice_number,
            "status": invoice.status,
            "currency": invoice.currency,
            "total_amount": money(invoice.total_amount),
            "paid_amount": money(invoice.paid_amount),
            "refunded_amount": money(invoice.refunded_amount),
            "outstanding_amount": money(invoice.total_amount - invoice.paid_amount),
            "created_at": invoice.created_at,
        }
