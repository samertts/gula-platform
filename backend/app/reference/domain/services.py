from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import UTC, date, datetime
from decimal import Decimal

from .exceptions import (
    CriticalResultError,
    DuplicatePatientError,
    InvalidOrderError,
    InvalidPatientDataError,
    PatientNotFoundError,
)
from .interfaces import OrderRepository, PatientRepository
from .models import (
    Gender,
    LabOrderDomain,
    LabResultDomain,
    OrderStatus,
    PatientDomain,
    Priority,
)

_NAME_NORMALIZATION_PATTERN = re.compile(r"[^\u0600-\u06FF\s]")


class PatientValidationService:
    """Pure domain logic for patient validation — zero framework deps."""

    MIN_NAME_LENGTH = 2
    MAX_NAME_LENGTH = 200
    PHONE_PATTERN = re.compile(r"^\+?[0-9]{7,15}$")
    NATIONAL_ID_PATTERN = re.compile(r"^\d{4,16}$")

    def validate_new_patient(
        self,
        patient: PatientDomain,
        repository: PatientRepository,
    ) -> PatientDomain:
        errors: list[str] = []

        name = patient.name.strip()
        if len(name) < self.MIN_NAME_LENGTH:
            errors.append("اسم المريض قصير جدًا")
        if len(name) > self.MAX_NAME_LENGTH:
            errors.append("اسم المريض طويل جدًا")

        if patient.gender not in (Gender.MALE, Gender.FEMALE):
            errors.append("الجنس غير صالح")

        phone = patient.phone.strip()
        if phone and not self.PHONE_PATTERN.match(phone):
            errors.append("رقم الهاتف غير صالح")

        if patient.national_id and not self.NATIONAL_ID_PATTERN.match(
            patient.national_id,
        ):
            errors.append("الرقم الوطني غير صالح")

        if patient.date_of_birth and patient.date_of_birth > date.today():
            errors.append("تاريخ الميلاد لا يمكن أن يكون في المستقبل")

        if errors:
            raise InvalidPatientDataError("; ".join(errors))

        patient.name = name
        patient.phone = phone

        return patient

    async def check_duplicate(
        self,
        patient: PatientDomain,
        repository: PatientRepository,
    ) -> None:
        existing = await repository.find_duplicate(
            name=patient.name,
            phone=patient.phone,
            lab_id=patient.lab_id,
        )
        if existing is not None and existing.name.strip() == patient.name.strip():
            raise DuplicatePatientError("name", patient.name)

    @staticmethod
    def normalize_name(raw: str) -> str:
        normalized = _NAME_NORMALIZATION_PATTERN.sub("", raw)
        return " ".join(normalized.split())

    @staticmethod
    def compute_age(date_of_birth: date | None) -> int | None:
        if date_of_birth is None:
            return None
        today = date.today()
        return (
            today.year
            - date_of_birth.year
            - (
                (today.month, today.day)
                < (date_of_birth.month, date_of_birth.day)
            )
        )


class OrderProcessingService:
    """Pure domain logic for lab order processing."""

    REQUIRED_FIELDS = {"patient_id", "test_type", "lab_id"}
    VALID_PRIORITIES = {Priority.ROUTINE, Priority.URGENT, Priority.STAT}

    async def validate_new_order(
        self,
        order: LabOrderDomain,
        patient_repo: PatientRepository,
    ) -> LabOrderDomain:
        missing = self.REQUIRED_FIELDS - {
            k
            for k, v in {
                "patient_id": order.patient_id,
                "test_type": order.test_type,
                "lab_id": order.lab_id,
            }.items()
            if v
        }
        if missing:
            raise InvalidOrderError(
                f"الحقول المطلوبة مفقودة: {', '.join(sorted(missing))}",
            )

        patient = await patient_repo.get_by_id(order.patient_id)
        if patient is None:
            raise PatientNotFoundError(order.patient_id)

        if order.priority not in self.VALID_PRIORITIES:
            order.priority = Priority.ROUTINE

        if not order.created_at:
            order.created_at = datetime.now(UTC)

        return order

    @staticmethod
    def determine_priority(order: LabOrderDomain) -> Priority:
        if order.priority == Priority.STAT:
            return Priority.STAT
        if order.priority == Priority.URGENT:
            return Priority.URGENT
        return Priority.ROUTINE

    @staticmethod
    def can_cancel(order: LabOrderDomain) -> bool:
        return order.status in (OrderStatus.PENDING, OrderStatus.RECEIVED)


class ResultValidationService:
    """Pure domain logic for result validation and critical flagging."""

    CRITICAL_FLAG = "حرج"
    HIGH_FLAG = "مرتفع"
    LOW_FLAG = "منخفض"
    NORMAL_FLAG = "طبيعي"

    async def validate_result(
        self,
        result: LabResultDomain,
        order_repo: OrderRepository,
    ) -> LabResultDomain:
        order = await order_repo.get_by_id(result.order_id)
        if order is None:
            raise InvalidOrderError(
                f"الطلب {result.order_id} غير موجود — لا يمكن إضافة نتيجة",
            )

        if result.value < Decimal(0):
            raise InvalidOrderError("قيمة النتيجة لا يمكن أن تكون سالبة")

        if not result.analyte.strip():
            raise InvalidOrderError("اسم التحليل مطلوب")

        if not result.unit.strip():
            raise InvalidOrderError("وحدة القياس مطلوبة")

        return result

    def flag_critical(
        self,
        result: LabResultDomain,
    ) -> bool:
        """Set is_critical and flagged fields on the result.

        Returns True if the result is critical, False otherwise.
        Does NOT raise — caller decides how to handle the critical state.
        """
        if result.reference_range is None:
            result.flagged = ResultValidationService.NORMAL_FLAG
            result.is_critical = False
            return False

        rr = result.reference_range
        flag = ResultValidationService.NORMAL_FLAG
        is_critical = False

        if (rr.min_critical is not None and result.value <= rr.min_critical) or (rr.max_critical is not None and result.value >= rr.max_critical):
            is_critical = True
            flag = ResultValidationService.CRITICAL_FLAG
        elif rr.min_value is not None and result.value < rr.min_value:
            flag = ResultValidationService.LOW_FLAG
        elif rr.max_value is not None and result.value > rr.max_value:
            flag = ResultValidationService.HIGH_FLAG

        result.flagged = flag
        result.is_critical = is_critical
        return is_critical

    def check_critical(
        self,
        result: LabResultDomain,
    ) -> LabResultDomain:
        """Deprecated: flags critical and raises if critical.

        Prefer flag_critical() which separates detection from control flow.
        """
        is_critical = self.flag_critical(result)
        if is_critical:
            raise CriticalResultError(
                analyte=result.analyte,
                value=f"{result.value}",
                unit=result.unit,
            )
        return result

    @staticmethod
    def bulk_check_critical(
        results: Sequence[LabResultDomain],
    ) -> list[LabResultDomain]:
        flagged: list[LabResultDomain] = []
        for r in results:
            if r.reference_range:
                rr = r.reference_range
                if (
                    rr.min_critical is not None and r.value <= rr.min_critical
                ) or (
                    rr.max_critical is not None and r.value >= rr.max_critical
                ):
                    r.is_critical = True
                    r.flagged = ResultValidationService.CRITICAL_FLAG
                    flagged.append(r)
        return flagged
