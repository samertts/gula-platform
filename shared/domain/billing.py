from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timezone, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class InvoiceStatus(Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class BillingCycle(Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    ONE_TIME = "one_time"


@dataclass
class Invoice:
    id: str = ""
    lab_id: int = 0
    amount: float = 0.0
    currency: str = "IQD"
    status: InvoiceStatus = InvoiceStatus.DRAFT
    description: str = ""
    items: list[dict[str, Any]] = field(default_factory=list)
    due_date: str = ""
    paid_at: str | None = None
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid4())
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "lab_id": self.lab_id, "amount": self.amount,
            "currency": self.currency, "status": self.status.value,
            "description": self.description, "items": self.items,
            "due_date": self.due_date, "paid_at": self.paid_at,
            "created_at": self.created_at,
        }


@dataclass
class PricingTier:
    name: str = ""
    price_monthly: float = 0.0
    price_yearly: float = 0.0
    max_labs: int = 1
    max_users: int = 5
    max_results_monthly: int = 1000
    features: list[str] = field(default_factory=list)


__all__ = ["Invoice", "PricingTier", "InvoiceStatus", "BillingCycle"]
