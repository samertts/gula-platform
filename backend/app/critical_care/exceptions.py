from __future__ import annotations


class CriticalCareException(Exception):
    pass


class ICUAdmissionNotFoundError(CriticalCareException):
    pass


class PatientNotFoundError(CriticalCareException):
    pass


class BedNotFoundError(CriticalCareException):
    pass


class BedNotAvailableError(CriticalCareException):
    pass


class ICUAssessmentNotFoundError(CriticalCareException):
    pass


class MonitoringRecordNotFoundError(CriticalCareException):
    pass


class VentilatorSettingNotFoundError(CriticalCareException):
    pass


class InfusionNotFoundError(CriticalCareException):
    pass


class InvalidScoreError(CriticalCareException):
    pass


class DeviceIntegrationNotFoundError(CriticalCareException):
    pass


class CarePlanNotFoundError(CriticalCareException):
    pass


class RoundNotFoundError(CriticalCareException):
    pass


class ICUWorkflowError(CriticalCareException):
    """Raised when a safety-critical ICU state transition is not permitted."""


class ICUValidationError(CriticalCareException):
    """Raised when a safety-critical ICU command lacks required clinical data."""
