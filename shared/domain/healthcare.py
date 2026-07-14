from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"


class OrderStatus(Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    COLLECTED = "collected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class ResultFlag(Enum):
    NORMAL = "normal"
    HIGH = "high"
    LOW = "low"
    CRITICAL_HIGH = "critical_high"
    CRITICAL_LOW = "critical_low"
    PANIC = "panic"


class SampleType(Enum):
    BLOOD = "blood"
    URINE = "urine"
    STOOL = "stool"
    TISSUE = "tissue"
    SWAB = "swab"
    CSF = "csf"
    OTHER = "other"


class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Citizen:
    id: int = 0
    first_name: str = ""
    last_name: str = ""
    father_name: str = ""
    mother_name: str = ""
    national_id: str = ""
    sndhs_health_id: str = ""
    date_of_birth: str = ""
    gender: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    governorate: str = ""
    lab_id: int = 0
    created_at: str = ""

    def full_name(self) -> str:
        return " ".join(p for p in [self.first_name, self.father_name, self.last_name] if p)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "full_name": self.full_name(),
            "first_name": self.first_name, "last_name": self.last_name,
            "father_name": self.father_name, "national_id": self.national_id,
            "sndhs_health_id": self.sndhs_health_id, "date_of_birth": self.date_of_birth,
            "gender": self.gender, "phone": self.phone, "city": self.city,
            "governorate": self.governorate, "lab_id": self.lab_id,
        }


@dataclass
class LabOrder:
    id: int = 0
    patient_id: int = 0
    lab_id: int = 0
    doctor_name: str = ""
    test_types: list[str] = field(default_factory=list)
    status: OrderStatus = OrderStatus.PENDING
    priority: str = "routine"
    visit_id: int | None = None
    notes: str = ""
    created_by: int = 0
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "patient_id": self.patient_id, "lab_id": self.lab_id,
            "doctor_name": self.doctor_name, "test_types": self.test_types,
            "status": self.status.value, "priority": self.priority,
            "visit_id": self.visit_id, "notes": self.notes, "created_at": self.created_at,
        }


@dataclass
class LabResult:
    id: int = 0
    order_id: int = 0
    patient_id: int = 0
    lab_id: int = 0
    test_name: str = ""
    value: float = 0.0
    unit: str = ""
    reference_low: float = 0.0
    reference_high: float = 0.0
    flag: ResultFlag = ResultFlag.NORMAL
    is_critical: bool = False
    interpretation: str = ""
    validated_by: int | None = None
    validated_at: str | None = None
    created_at: str = ""
    version: int = 1

    def compute_flag(self) -> ResultFlag:
        if self.value < self.reference_low:
            return ResultFlag.CRITICAL_LOW if self.value < self.reference_low * 0.5 else ResultFlag.LOW
        if self.value > self.reference_high:
            return ResultFlag.CRITICAL_HIGH if self.value > self.reference_high * 1.5 else ResultFlag.HIGH
        return ResultFlag.NORMAL

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "order_id": self.order_id, "test_name": self.test_name,
            "value": self.value, "unit": self.unit,
            "reference_range": {"low": self.reference_low, "high": self.reference_high},
            "flag": self.flag.value, "is_critical": self.is_critical,
            "interpretation": self.interpretation, "validated_by": self.validated_by, "version": self.version,
        }


@dataclass
class Visit:
    id: int = 0
    patient_id: int = 0
    lab_id: int = 0
    visit_type: str = "routine"
    visit_date: str = ""
    diagnosis: str = ""
    doctor_name: str = ""
    notes: str = ""
    created_at: str = ""


@dataclass
class QualityControl:
    id: int = 0
    lab_id: int = 0
    test_name: str = ""
    lot_number: str = ""
    value: float = 0.0
    expected: float = 0.0
    sd: float = 0.0
    status: str = "in_range"
    checked_by: int = 0
    checked_at: str = ""


__all__ = [
    "Citizen",
    "Gender",
    "LabOrder",
    "LabResult",
    "OrderStatus",
    "QualityControl",
    "ResultFlag",
    "SampleType",
    "TestStatus",
    "Visit",
]
