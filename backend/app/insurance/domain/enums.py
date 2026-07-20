"""Insurance domain enumerations."""

from __future__ import annotations

from enum import Enum


class InsuranceType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    SOCIAL = "social"
    EMPLOYER = "employer"
    TRAVEL = "travel"
    OTHER = "other"


class CoverageStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"
    TERMINATED = "terminated"


class PolicyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class CoverageDetermination(str, Enum):
    COVERED = "covered"
    NOT_COVERED = "not_covered"
    PARTIAL = "partial"
    CONDITIONAL = "conditional"
    PENDING_REVIEW = "pending_review"
    ERROR = "error"


class ClaimStatus(str, Enum):
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


class ClaimType(str, Enum):
    INSTITUTIONAL = "institutional"
    PROFESSIONAL = "professional"
    PHARMACY = "pharmacy"
    LABORATORY = "laboratory"
    RADIOLOGY = "radiology"
    DENTAL = "dental"
    VISION = "vision"


class AuthorizationStatus(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    DENIED = "denied"
    MODIFIED = "modified"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ReferralStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    RECEIVED = "received"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"
    ON_HOLD = "on_hold"


class SettlementStatus(str, Enum):
    PENDING = "pending"
    RECONCILED = "reconciled"
    DISPUTED = "disputed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FraudSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FraudStatus(str, Enum):
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class AppealStatus(str, Enum):
    FILED = "filed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"
    ESCALATED = "escalated"


class ProviderContractStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    EXPIRED = "expired"


class ServiceCategory(str, Enum):
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


class CardStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    STOLEN = "stolen"
    LOST = "lost"


class MemberStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"


class RelationType(str, Enum):
    SPOUSE = "spouse"
    CHILD = "child"
    PARENT = "parent"
    SIBLING = "sibling"
    OTHER = "other"


class ReferralType(str, Enum):
    DOCTOR = "doctor"
    LABORATORY = "laboratory"
    RADIOLOGY = "radiology"
    SPECIALIST = "specialist"


class ReferralPriority(str, Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class NetworkTier(str, Enum):
    TIER1 = "tier1"
    TIER2 = "tier2"
    TIER3 = "tier3"


class CoverageLevel(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"


class AccreditationStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    PENDING = "pending"


class ValidationMethod(str, Enum):
    QR_SCAN = "qr_scan"
    MANUAL = "manual"
    API = "api"
    BIOMETRIC = "biometric"
