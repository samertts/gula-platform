from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FHIRSecurityLabel(str, Enum):
    UNRESTRICTED = "unrestricted"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    RESTRICTED = "restricted"
    VERY_RESTRICTED = "very-restricted"
    COMPILATION = "compilation"
    CLINICAL_RESEARCH = "clinical-research"
    RESEARCH = "research"
    HIV = "hiv"
    PSYCH = "psych"
    SEXUAL_HEALTH = "sexual-health"
    SUBSTANCE_ABUSE = "substance-abuse"
    GENETIC = "genetic"
    ETHNICITY = "ethnicity"
    GENDER = "gender"
    DISABILITY = "disability"
    SENSITIVE = "sensitive"
    PATIENT_REQUESTED = "patient-requested"


class FHIRConsentDirective(str, Enum):
    OPT_IN = "opt-in"
    OPT_OUT = "opt-out"
    OPT_IN_EXCEPT = "opt-in-except"
    OPT_OUT_EXCEPT = "opt-out-except"
    EMERGENCY_ONLY = "emergency-only"
    RESEARCH_ONLY = "research-only"
    NO_CONSENT = "no-consent"


class PurposeOfUse(str, Enum):
    TREATMENT = "treatment"
    PAYMENT = "payment"
    OPERATIONS = "operations"
    RESEARCH = "research"
    PUBLIC_HEALTH = "public-health"
    BREAK_GLASS = "break-glass"
    EMERGENCY = "emergency"
    DISASTER = "disaster"
    QUALITY_IMPROVEMENT = "quality-improvement"
    POPULATION_HEALTH = "population-health"
    GOVERNMENT = "government"
    COURT_ORDER = "court-order"
    FRAUD_DETECTION = "fraud-detection"
    MARKETING = "marketing"
    EMPLOYMENT = "employment"
    EDUCATION = "education"


class PatientConsent(BaseModel):
    patient_id: str
    consent_id: str
    status: str = "active"
    scope: FHIRConsentDirective = FHIRConsentDirective.OPT_IN
    purpose: list[PurposeOfUse] = Field(default_factory=list)
    effective_start: datetime
    effective_end: datetime | None = None
    restrictions: list[str] = Field(default_factory=list)
    provisions: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class BreakGlassAccess(BaseModel):
    accessor_id: str
    patient_id: str
    reason: str
    duration_minutes: int = 30
    approved_by: str = ""
    timestamp: datetime | None = None
    status: str = "pending"
    reviewed: bool = False
    review_notes: str = ""


class ClinicalAuditEvent(BaseModel):
    event_id: str
    user_id: str
    patient_id: str = ""
    resource_type: str = ""
    resource_id: str = ""
    action: str = ""
    outcome: str = "success"
    outcome_desc: str = ""
    timestamp: datetime | None = None
    signature: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
