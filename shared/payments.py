from __future__ import annotations

import logging
from datetime import timezone, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger("gula.payments")


class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"
    ONLINE = "online"


class Payment:
    def __init__(
        self, amount: float, currency: str = "IQD", method: PaymentMethod = PaymentMethod.ONLINE,
        description: str = "", lab_id: int = 0, payment_id: str | None = None,
    ) -> None:
        self.id = payment_id or str(uuid4())
        self.amount = amount
        self.currency = currency
        self.method = method
        self.description = description
        self.lab_id = lab_id
        self.status = PaymentStatus.PENDING
        self.created_at = datetime.now(timezone.utc)
        self.processed_at: datetime | None = None
        self.reference: str = ""

    def complete(self, reference: str = "") -> None:
        self.status = PaymentStatus.COMPLETED
        self.processed_at = datetime.now(timezone.utc)
        self.reference = reference

    def fail(self) -> None:
        self.status = PaymentStatus.FAILED

    def refund(self) -> None:
        if self.status == PaymentStatus.COMPLETED:
            self.status = PaymentStatus.REFUNDED

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "amount": self.amount, "currency": self.currency,
            "method": self.method.value, "description": self.description, "lab_id": self.lab_id,
            "status": self.status.value, "reference": self.reference,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }


class PaymentGateway:
    def __init__(self, api_key: str = "", sandbox: bool = True) -> None:
        self._api_key = api_key
        self._sandbox = sandbox
        self._transactions: dict[str, Payment] = {}

    def charge(self, payment: Payment) -> Payment:
        if self._sandbox:
            payment.complete(reference=f"SIM_{payment.id[:8]}")
        self._transactions[payment.id] = payment
        logger.info("Payment %s: %.2f %s (%s)", payment.id, payment.amount, payment.currency, payment.status.value)
        return payment

    def get(self, payment_id: str) -> Payment | None:
        return self._transactions.get(payment_id)

    def list(self, lab_id: int | None = None) -> list[Payment]:
        if lab_id is None:
            return list(self._transactions.values())
        return [p for p in self._transactions.values() if p.lab_id == lab_id]


__all__ = ["PaymentStatus", "PaymentMethod", "Payment", "PaymentGateway"]
