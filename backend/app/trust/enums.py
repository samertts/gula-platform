"""Enums for the Trust platform."""

import enum


class ConsentStatus(enum.Enum):
    PENDING = "pending"
    GRANTED = "granted"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class ConsentPurpose(enum.Enum):
    TREATMENT = "treatment"
    PAYMENT = "payment"
    OPERATIONS = "operations"
    PUBLIC_HEALTH = "public_health"
    RESEARCH = "research"
    NATIONAL_REPORTING = "national_reporting"
    EMERGENCY = "emergency"


class DataCategory(enum.Enum):
    CLINICAL = "clinical"
    LABORATORY = "laboratory"
    GENETIC = "genetic"
    MENTAL_HEALTH = "mental_health"
    REPRODUCTIVE = "reproductive"
    HIV_STATUS = "hiv_status"
    DEMOGRAPHIC = "demographic"
    FINANCIAL = "financial"
    AUDIT = "audit"


class RetentionPolicy(enum.Enum):
    CLINICAL_25_YEARS = "clinical_25_years"
    LAB_RESULTS_10_YEARS = "lab_results_10_years"
    AUDIT_LOGS_7_YEARS = "audit_logs_7_years"
    CONSENT_DURATION_PLUS_2 = "consent_duration_plus_2"
    SESSION_24_HOURS = "session_24_hours"
    BACKUP_30_DAYS = "backup_30_days"
    BACKUP_1_YEAR = "backup_1_year"


class SovereigntyLevel(enum.Enum):
    NATIONAL_ONLY = "national_only"
    NATIONAL_PRIMARY = "national_primary"
    REGIONAL = "regional"
    INTERNATIONAL = "international"


class TrustServiceType(enum.Enum):
    DIGITAL_SIGNATURE = "digital_signature"
    TIMESTAMPING = "timestamping"
    EVIDENCE_PRESERVATION = "evidence_preservation"
    CERTIFICATE_MANAGEMENT = "certificate_management"
    IDENTITY_VERIFICATION = "identity_verification"
    DOCUMENT_INTEGRITY = "document_integrity"


class ComplianceStatus(enum.Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING_REVIEW = "pending_review"
    EXEMPTED = "exempted"
    NOT_APPLICABLE = "not_applicable"


class MaskingLevel(enum.Enum):
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"
    ANONYMIZED = "anonymized"
    PSEUDONYMIZED = "pseudonymized"
