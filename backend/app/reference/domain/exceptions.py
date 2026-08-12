from __future__ import annotations


class DomainError(Exception):
    """Base exception for all domain-level errors."""

    def __init__(self, message: str = "", code: str = "DOMAIN_ERROR") -> None:
        self.code = code
        super().__init__(message)


class PatientNotFoundError(DomainError):
    def __init__(self, patient_id: str) -> None:
        super().__init__(
            message=f"المريض {patient_id} غير موجود",
            code="PATIENT_NOT_FOUND",
        )
        self.patient_id = patient_id


class DuplicatePatientError(DomainError):
    def __init__(self, field: str, value: str) -> None:
        super().__init__(
            message=f"مريض مكرر — {field}: {value}",
            code="DUPLICATE_PATIENT",
        )
        self.field = field
        self.value = value


class InvalidPatientDataError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="INVALID_PATIENT_DATA")


class InvalidOrderError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="INVALID_ORDER")


class OrderNotFoundError(DomainError):
    def __init__(self, order_id: str) -> None:
        super().__init__(
            message=f"الطلب {order_id} غير موجود",
            code="ORDER_NOT_FOUND",
        )
        self.order_id = order_id


class CriticalResultError(DomainError):
    def __init__(self, analyte: str, value: str, unit: str) -> None:
        super().__init__(
            message=f"نتيجة حرجة — {analyte}: {value} {unit}",
            code="CRITICAL_RESULT",
        )
        self.analyte = analyte
        self.value = value
        self.unit = unit


class ResultNotFoundError(DomainError):
    def __init__(self, result_id: str) -> None:
        super().__init__(
            message=f"النتيجة {result_id} غير موجودة",
            code="RESULT_NOT_FOUND",
        )
        self.result_id = result_id
