from __future__ import annotations

from app._compat import StrEnum


class CitizenNotificationType(StrEnum):
    APPOINTMENT_REMINDER = "appointment_reminder"
    LAB_RESULT = "lab_result"
    MEDICATION_ALERT = "medication_alert"
    HEALTH_TIP = "health_tip"
    EMERGENCY_ALERT = "emergency_alert"
    CAMPAIGN = "campaign"


class AppointmentType(StrEnum):
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    LAB = "lab"
    RADIOLOGY = "radiology"
    TELEMEDICINE = "telemedicine"


class HealthCardStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"
    PENDING = "pending"


class ConsentScope(StrEnum):
    VIEW_RECORDS = "view_records"
    SHARE_DATA = "share_data"
    EMERGENCY_ACCESS = "emergency_access"
    RESEARCH = "research"
    INSURANCE = "insurance"


class FamilyRole(StrEnum):
    SELF = "self"
    SPOUSE = "spouse"
    CHILD = "child"
    PARENT = "parent"
    GUARDIAN = "guardian"
    DEPENDENT = "dependent"


class DocumentType(StrEnum):
    LAB_REPORT = "lab_report"
    RADIOLOGY_IMAGE = "radiology_image"
    PRESCRIPTION = "prescription"
    INSURANCE_DOCUMENT = "insurance_document"
    EXTERNAL_REPORT = "external_report"
    MEDICAL_CERTIFICATE = "medical_certificate"
    OTHER = "other"


class TelemedicineStatus(StrEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class ScreeningStatus(StrEnum):
    DUE = "due"
    OVERDUE = "overdue"
    COMPLETED = "completed"
    SCHEDULED = "scheduled"
    DECLINED = "declined"
    NOT_APPLICABLE = "not_applicable"


class CertificateType(StrEnum):
    VACCINATION = "vaccination"
    FITNESS = "fitness"
    MEDICAL_LEAVE = "medical_leave"
    HEALTH = "health"
    BIRTH = "birth"
    DEATH = "death"
    REFERRAL = "referral"
