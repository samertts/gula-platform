from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from app._compat import StrEnum


class Gender(StrEnum):
    MALE = "ذكر"
    FEMALE = "أنثى"


class OrderStatus(StrEnum):
    PENDING = "قيد_الانتظار"
    RECEIVED = "تم_الاستلام"
    IN_PROGRESS = "قيد_التنفيذ"
    COMPLETED = "مكتمل"
    CANCELLED = "ملغي"


class Priority(StrEnum):
    ROUTINE = "روتيني"
    URGENT = "عاجل"
    STAT = "فوري"


@dataclass
class PatientDomain:
    patient_id: str | None = None
    name: str = ""
    date_of_birth: date | None = None
    gender: Gender | None = None
    phone: str = ""
    lab_id: str = ""
    national_id: str | None = None
    address: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def age(self) -> int | None:
        if self.date_of_birth is None:
            return None
        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )


@dataclass
class LabOrderDomain:
    order_id: str | None = None
    patient_id: str = ""
    lab_id: str = ""
    test_type: str = ""
    status: OrderStatus = OrderStatus.PENDING
    priority: Priority = Priority.ROUTINE
    notes: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    performed_by: str | None = None


@dataclass
class ReferenceRange:
    analyte: str = ""
    unit: str = ""
    min_value: Decimal | None = None
    max_value: Decimal | None = None
    min_critical: Decimal | None = None
    max_critical: Decimal | None = None


@dataclass
class LabResultDomain:
    result_id: str | None = None
    order_id: str = ""
    analyte: str = ""
    value: Decimal = Decimal(0)
    unit: str = ""
    reference_range: ReferenceRange | None = None
    is_critical: bool = False
    flagged: str = ""
    notes: str = ""
    created_at: datetime | None = None
    performed_by: str | None = None


@dataclass
class TestPanelDomain:
    panel_id: str | None = None
    name: str = ""
    component_tests: list[str] = field(default_factory=list)
    lab_id: str = ""
    is_active: bool = True
