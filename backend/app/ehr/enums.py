from __future__ import annotations

from app._compat import StrEnum


class ProblemStatus(StrEnum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    INACTIVE = "inactive"
    ENTERED_IN_ERROR = "entered_in_error"


class AllergySeverity(StrEnum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    LIFE_THREATENING = "life_threatening"


class AllergyStatus(StrEnum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    ENTERED_IN_ERROR = "entered_in_error"


class ClinicalNoteType(StrEnum):
    SOAP = "soap"
    PROGRESS = "progress"
    NURSING = "nursing"
    OPERATIVE = "operative"
    CONSULTATION = "consultation"
    EMERGENCY = "emergency"
    DISCHARGE_SUMMARY = "discharge_summary"


class MedicationOrderStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    DISCONTINUED = "discontinued"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered_in_error"


class MedicationAdministrationStatus(StrEnum):
    COMPLETED = "completed"
    NOT_DONE = "not_done"
    IN_PROGRESS = "in_progress"
    STOPPED = "stopped"


class CarePlanStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    REVISED = "revised"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered_in_error"


class TimelineEventType(StrEnum):
    VISIT = "visit"
    LAB_RESULT = "lab_result"
    RADIOLOGY = "radiology"
    MEDICATION = "medication"
    DIAGNOSIS = "diagnosis"
    PROCEDURE = "procedure"
    DOCUMENT = "document"
    NOTIFICATION = "notification"
    AUDIT = "audit"
    IMMUNIZATION = "immunization"
    ALLERGY = "allergy"
    CARE_PLAN = "care_plan"


class SmokingStatus(StrEnum):
    CURRENT = "current"
    FORMER = "former"
    NEVER = "never"
    PASSIVE = "passive"
    UNKNOWN = "unknown"


class AlcoholStatus(StrEnum):
    CURRENT = "current"
    FORMER = "former"
    NEVER = "never"
    OCCASIONAL = "occasional"
    UNKNOWN = "unknown"


class DisabilityType(StrEnum):
    PHYSICAL = "physical"
    VISUAL = "visual"
    HEARING = "hearing"
    SPEECH = "speech"
    COGNITIVE = "cognitive"
    MENTAL = "mental"
    MULTIPLE = "multiple"
    NONE = "none"


class RiskLevel(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class DiagnosisType(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    COMORBIDITY = "comorbidity"
    COMPLICATION = "complication"


class ConsentType(StrEnum):
    PATIENT_CARE = "patient_care"
    RESEARCH = "research"
    DATA_SHARING = "data_sharing"
    TELEMEDICINE = "telemedicine"
    EMERGENCY = "emergency"
