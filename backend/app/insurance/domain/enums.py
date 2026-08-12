"""Insurance domain enumerations."""

from __future__ import annotations

from app._compat import StrEnum


class InsuranceType(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    SOCIAL = "social"
    EMPLOYER = "employer"
    TRAVEL = "travel"
    OTHER = "other"


class CoverageStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"
    TERMINATED = "terminated"


class PolicyStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class CoverageDetermination(StrEnum):
    COVERED = "covered"
    NOT_COVERED = "not_covered"
    PARTIAL = "partial"
    CONDITIONAL = "conditional"
    PENDING_REVIEW = "pending_review"
    ERROR = "error"


class ClaimStatus(StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    SUBMITTED = "submitted"
    ADJUDICATED = "adjudicated"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    DENIED = "denied"
    CANCELLED = "cancelled"
    REVERSED = "reversed"
    UNDER_REVIEW = "under_review"


class ClaimType(StrEnum):
    INSTITUTIONAL = "institutional"
    PROFESSIONAL = "professional"
    PHARMACY = "pharmacy"
    LABORATORY = "laboratory"
    RADIOLOGY = "radiology"
    DENTAL = "dental"
    VISION = "vision"


class AuthorizationStatus(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    DENIED = "denied"
    MODIFIED = "modified"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ReferralStatus(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    RECEIVED = "received"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"
    ON_HOLD = "on_hold"


class SettlementStatus(StrEnum):
    PENDING = "pending"
    RECONCILED = "reconciled"
    DISPUTED = "disputed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FraudSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FraudStatus(StrEnum):
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class AppealStatus(StrEnum):
    FILED = "filed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"
    ESCALATED = "escalated"


class ProviderContractStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    EXPIRED = "expired"


class ServiceCategory(StrEnum):
    CONSULTATION = "consultation"
    DIAGNOSTIC = "diagnostic"
    LABORATORY = "laboratory"
    RADIOLOGY = "radiology"
    SURGERY = "surgery"
    MEDICATION = "medication"
    HOSPITALIZATION = "hospitalization"
    REHABILITATION = "rehabilitation"
    PREVENTIVE = "preventive"
    EMERGENCY = "emergency"
    DENTAL = "dental"
    MENTAL_HEALTH = "mental_health"
    MATERNITY = "maternity"
    OTHER = "other"


class CardStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    STOLEN = "stolen"
    LOST = "lost"


class MemberStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"


class RelationType(StrEnum):
    SPOUSE = "spouse"
    CHILD = "child"
    PARENT = "parent"
    SIBLING = "sibling"
    OTHER = "other"


class ReferralType(StrEnum):
    DOCTOR = "doctor"
    LABORATORY = "laboratory"
    RADIOLOGY = "radiology"
    SPECIALIST = "specialist"


class ReferralPriority(StrEnum):
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class NetworkTier(StrEnum):
    TIER1 = "tier1"
    TIER2 = "tier2"
    TIER3 = "tier3"


class CoverageLevel(StrEnum):
    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"


class AccreditationStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    PENDING = "pending"


class ValidationMethod(StrEnum):
    QR_SCAN = "qr_scan"
    MANUAL = "manual"
    API = "api"
    BIOMETRIC = "biometric"
