from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class Gender(str, Enum):
    MALE = "ذكر"
    FEMALE = "أنثى"


class OrderStatus(str, Enum):
    PENDING = "قيد_الانتظار"
    RECEIVED = "تم_الاستلام"
    IN_PROGRESS = "قيد_التنفيذ"
    COMPLETED = "مكتمل"
    CANCELLED = "ملغي"


class Priority(str, Enum):
    ROUTINE = "روتيني"
    URGENT = "عاجل"
    STAT = "فوري"


@dataclass
class PatientDomain:
    patient_id: Optional[str] = None
    name: str = ""
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    phone: str = ""
    lab_id: str = ""
    national_id: Optional[str] = None
    address: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def age(self) -> Optional[int]:
        if self.date_of_birth is None:
            return None
        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )


@dataclass
class LabOrderDomain:
    order_id: Optional[str] = None
    patient_id: str = ""
    lab_id: str = ""
    test_type: str = ""
    status: OrderStatus = OrderStatus.PENDING
    priority: Priority = Priority.ROUTINE
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    performed_by: Optional[str] = None


@dataclass
class ReferenceRange:
    analyte: str = ""
    unit: str = ""
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    min_critical: Optional[Decimal] = None
    max_critical: Optional[Decimal] = None


@dataclass
class LabResultDomain:
    result_id: Optional[str] = None
    order_id: str = ""
    analyte: str = ""
    value: Decimal = Decimal("0")
    unit: str = ""
    reference_range: Optional[ReferenceRange] = None
    is_critical: bool = False
    flagged: str = ""
    notes: str = ""
    created_at: Optional[datetime] = None
    performed_by: Optional[str] = None


@dataclass
class TestPanelDomain:
    panel_id: Optional[str] = None
    name: str = ""
    component_tests: list[str] = field(default_factory=list)
    lab_id: str = ""
    is_active: bool = True
