from app._compat import StrEnum


class AlertLevel(StrEnum):
    INFORMATION = "information"
    SURVEILLANCE = "surveillance"
    WARNING = "warning"
    OUTBREAK = "outbreak"
    CRITICAL = "critical"


class OutbreakStatus(StrEnum):
    MONITORING = "monitoring"
    INVESTIGATING = "investigating"
    CONFIRMED = "confirmed"
    CONTAINED = "contained"
    DECLARED_OVER = "declared_over"


class TransmissionType(StrEnum):
    PERSON_TO_PERSON = "person_to_person"
    AIRBORNE = "airborne"
    FOODBORNE = "foodborne"
    WATERBORNE = "waterborne"
    VECTOR_BORNE = "vector_borne"
    ZOONOTIC = "zoonotic"
    NOSOCOMIAL = "nosocomial"
    UNKNOWN = "unknown"


class DiseaseCategory(StrEnum):
    NOTIFIABLE = "notifiable"
    REPORTABLE = "reportable"
    SENTINEL = "sentinel"
    CHRONIC = "chronic"
    EMERGING = "emerging"
    ERADICATED = "eradicated"


class SurveillanceType(StrEnum):
    PASSIVE = "passive"
    ACTIVE = "active"
    SENTINEL = "sentinel"
    SYNDROMIC = "syndromic"
    LABORATORY = "laboratory"
    EVENT_BASED = "event_based"


class ImmunizationStatus(StrEnum):
    SCHEDULED = "scheduled"
    ADMINISTERED = "administered"
    OVERDUE = "overdue"
    REFUSED = "refused"
    CONTRAINDICATED = "contraindicated"
    PARTIAL = "partial"
    COMPLETE = "complete"


class TrendDirection(StrEnum):
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    UNKNOWN = "unknown"


class SeverityLevel(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ReportingSource(StrEnum):
    LABORATORY = "laboratory"
    CLINIC = "clinic"
    HOSPITAL = "hospital"
    COMMUNITY = "community"
    PHARMACY = "pharmacy"
    SCHOOL = "school"
    OTHER = "other"
