from enum import Enum


class CareContinuumEventType(Enum):
    PRIMARY_CARE = "primary_care"
    REFERRAL = "referral"
    FOLLOW_UP = "follow_up"
    HOME_VISIT = "home_visit"
    COMMUNITY_CARE = "community_care"
    TELEHEALTH = "telehealth"
    PROGRAM_ENROLLMENT = "program_enrollment"
    SCREENING = "screening"
    VACCINATION = "vaccination"
    HEALTH_EDUCATION = "health_education"


class ReferralDirection(Enum):
    OUTGOING = "outgoing"
    INCOMING = "incoming"
    REVERSE = "reverse"


class ChronicDiseaseType(Enum):
    DIABETES = "diabetes"
    HYPERTENSION = "hypertension"
    CKD = "ckd"
    COPD = "copd"
    ASTHMA = "asthma"
    HEART_FAILURE = "heart_failure"
    CANCER = "cancer"
    THYROID = "thyroid"
    ARTHRITIS = "arthritis"
    MENTAL_HEALTH = "mental_health"
    OTHER = "other"


class DiseaseSeverity(Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"
    REMISSION = "remission"
    CONTROLLED = "controlled"
    UNCONTROLLED = "uncontrolled"


class PregnancyStatus(Enum):
    NOT_PREGNANT = "not_pregnant"
    FIRST_TRIMESTER = "first_trimester"
    SECOND_TRIMESTER = "second_trimester"
    THIRD_TRIMESTER = "third_trimester"
    POSTPARTUM = "postpartum"


class VaccinationStatus(Enum):
    GIVEN = "given"
    NOT_GIVEN = "not_given"
    CONTRAINDICATED = "contraindicated"
    REFUSED = "refused"
    SCHEDULED = "scheduled"
    OVERDUE = "overdue"


class FollowUpStatus(Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    MISSED = "missed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class CareProgramStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"
    GRADUATED = "graduated"


class HealthProgramType(Enum):
    SCREENING = "screening"
    CAMPAIGN = "campaign"
    SCHOOL_HEALTH = "school_health"
    OCCUPATIONAL_HEALTH = "occupational_health"
    CHRONIC_DISEASE = "chronic_disease"
    MATERNAL_CHILD = "maternal_child"
    IMMUNIZATION = "immunization"
    NUTRITION = "nutrition"
    MENTAL_HEALTH = "mental_health"
