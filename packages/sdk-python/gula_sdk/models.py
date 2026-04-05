"""GULA SDK — Typed response models.

All dataclasses are constructed from raw API JSON dicts.
They provide attribute access, IDE completion, and runtime type safety.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Patient:
    id: int
    full_name: str
    phone: str
    blood_type: Optional[str]
    gender: str
    lab_id: int
    national_id: Optional[str] = None
    date_of_birth: Optional[str] = None
    created_at: Optional[str] = None
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "Patient":
        return cls(
            id=d["id"],
            full_name=d["full_name"],
            phone=d["phone"],
            blood_type=d.get("blood_type"),
            gender=d.get("gender", ""),
            lab_id=d.get("lab_id", 0),
            national_id=d.get("national_id"),
            date_of_birth=d.get("date_of_birth"),
            created_at=d.get("created_at"),
            extra={k: v for k, v in d.items()
                   if k not in ("id", "full_name", "phone", "blood_type", "gender",
                                "lab_id", "national_id", "date_of_birth", "created_at")},
        )


@dataclass
class LabOrder:
    id: int
    patient_id: int
    lab_id: int
    status: str
    ordered_tests: list[dict] = field(default_factory=list)
    barcode: Optional[str] = None
    priority: str = "routine"
    created_at: Optional[str] = None
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "LabOrder":
        return cls(
            id=d["id"],
            patient_id=d["patient_id"],
            lab_id=d.get("lab_id", 0),
            status=d.get("status", "pending"),
            ordered_tests=d.get("ordered_tests", []),
            barcode=d.get("barcode"),
            priority=d.get("priority", "routine"),
            created_at=d.get("created_at"),
            extra={k: v for k, v in d.items()
                   if k not in ("id", "patient_id", "lab_id", "status",
                                "ordered_tests", "barcode", "priority", "created_at")},
        )


@dataclass
class LabResult:
    id: int
    order_id: int
    test_type_id: int
    value: str
    unit: Optional[str]
    status: str
    interpretation: Optional[str] = None
    ai_interpretation: Optional[str] = None
    created_at: Optional[str] = None
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "LabResult":
        return cls(
            id=d["id"],
            order_id=d["order_id"],
            test_type_id=d["test_type_id"],
            value=str(d["value"]),
            unit=d.get("unit"),
            status=d.get("status", "pending"),
            interpretation=d.get("interpretation"),
            ai_interpretation=d.get("ai_interpretation"),
            created_at=d.get("created_at"),
            extra={k: v for k, v in d.items()
                   if k not in ("id", "order_id", "test_type_id", "value", "unit",
                                "status", "interpretation", "ai_interpretation", "created_at")},
        )


@dataclass
class Claim:
    id: int
    patient_id: int
    order_id: int
    amount: float
    currency: str
    status: str
    insurance_id: Optional[str] = None
    fraud_score: Optional[float] = None
    fraud_decision: Optional[str] = None
    created_at: Optional[str] = None
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "Claim":
        return cls(
            id=d["id"],
            patient_id=d["patient_id"],
            order_id=d["order_id"],
            amount=float(d.get("amount", 0)),
            currency=d.get("currency", "IQD"),
            status=d.get("status", "pending"),
            insurance_id=d.get("insurance_id"),
            fraud_score=d.get("fraud_score"),
            fraud_decision=d.get("fraud_decision"),
            created_at=d.get("created_at"),
            extra={k: v for k, v in d.items()
                   if k not in ("id", "patient_id", "order_id", "amount", "currency",
                                "status", "insurance_id", "fraud_score",
                                "fraud_decision", "created_at")},
        )


@dataclass
class BloodDonor:
    id: int
    full_name: str
    blood_type: str
    gender: str
    eligible: bool
    eligibility_reason: str = ""
    last_donation_date: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> "BloodDonor":
        return cls(
            id=d["id"],
            full_name=d["full_name"],
            blood_type=d["blood_type"],
            gender=d.get("gender", ""),
            eligible=d.get("eligible", False),
            eligibility_reason=d.get("eligibility_reason", ""),
            last_donation_date=d.get("last_donation_date"),
        )


@dataclass
class InventorySummary:
    items: list[dict] = field(default_factory=list)
    shortages: list[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "InventorySummary":
        return cls(
            items=list(d.get("summary", {}).values()),
            shortages=d.get("shortages", []),
        )


@dataclass
class ApiResponse:
    """Generic wrapper for responses that don't map to a specific model."""
    data: Any
    status_code: int = 200

    def __getitem__(self, key: str) -> Any:
        if isinstance(self.data, dict):
            return self.data[key]
        raise TypeError(f"ApiResponse.data is not a dict (got {type(self.data).__name__})")

    def get(self, key: str, default: Any = None) -> Any:
        if isinstance(self.data, dict):
            return self.data.get(key, default)
        return default
