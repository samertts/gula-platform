from __future__ import annotations

from enum import Enum


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class IdentityType(Enum):
    IRAQI_CITIZEN = "iraqi_citizen"
    NEWBORN = "newborn"
    FOREIGNER = "foreigner"
    RESIDENT = "resident"
    VISITOR = "visitor"
    UNKNOWN_PATIENT = "unknown_patient"


class IdentityStatus(Enum):
    ACTIVE = "active"
    MERGED = "merged"
    DECEASED = "deceased"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    PENDING_MERGE = "pending_merge"


class GuardianType(Enum):
    FATHER = "father"
    MOTHER = "mother"
    LEGAL_GUARDIAN = "legal_guardian"
    GRANDPARENT = "grandparent"
    SIBLING = "sibling"
    OTHER = "other"


class FamilyRelationshipType(Enum):
    PARENT = "parent"
    CHILD = "child"
    SPOUSE = "spouse"
    DEPENDENT = "dependent"
    SIBLING = "sibling"
    EMERGENCY_CONTACT = "emergency_contact"
    OTHER = "other"


class OrganizationType(Enum):
    MINISTRY = "ministry"
    DIRECTORATE = "directorate"
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    LABORATORY = "laboratory"
    PHARMACY = "pharmacy"
    INSURANCE = "insurance"
    RESEARCH = "research"
    OTHER = "other"


class FacilityType(Enum):
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    LABORATORY = "laboratory"
    PHARMACY = "pharmacy"
    WARD = "ward"
    EMERGENCY = "emergency"
    OPERATING_ROOM = "operating_room"
    RADIOLOGY = "radiology"
    OTHER = "other"


class PractitionerRole(Enum):
    DOCTOR = "doctor"
    NURSE = "nurse"
    TECHNICIAN = "technician"
    PHARMACIST = "pharmacist"
    ADMINISTRATOR = "administrator"
    SPECIALIST = "specialist"
    CONSULTANT = "consultant"
    RESIDENT = "resident"
    INTERN = "intern"
    OTHER = "other"


class EncounterType(Enum):
    OUTPATIENT = "outpatient"
    INPATIENT = "inpatient"
    EMERGENCY = "emergency"
    HOME_HEALTH = "home_health"
    FIELD = "field"
    TELEHEALTH = "telehealth"
    VIRTUAL = "virtual"
    FOLLOW_UP = "follow_up"
    CONSULTATION = "consultation"
    OTHER = "other"


class EncounterStatus(Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    DISCHARGED = "discharged"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered_in_error"
    UNKNOWN = "unknown"


class EpisodeOfCareStatus(Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    DISCHARGED = "discharged"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered_in_error"


class VisitType(Enum):
    ROUTINE = "routine"
    EMERGENCY = "emergency"
    FOLLOW_UP = "follow_up"
    CONSULTATION = "consultation"
    PRE_OPERATIVE = "pre_operative"
    POST_OPERATIVE = "post_operative"
    HOME = "home"
    TELEHEALTH = "telehealth"
    FIELD = "field"
    OTHER = "other"


class VisitStatus(Enum):
    PENDING = "pending"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    ENTERED_IN_ERROR = "entered_in_error"


class AppointmentStatus(Enum):
    PROPOSED = "proposed"
    PENDING = "pending"
    BOOKED = "booked"
    ARRIVED = "arrived"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    ENTERED_IN_ERROR = "entered_in_error"


class AdmissionStatus(Enum):
    PENDING = "pending"
    ADMITTED = "admitted"
    TRANSFERRED = "transferred"
    DISCHARGED = "discharged"
    CANCELLED = "cancelled"


class DischargeType(Enum):
    HOME = "home"
    TRANSFER = "transfer"
    AGAINST_MEDICAL_ADVICE = "against_medical_advice"
    DECEASED = "deceased"
    OTHER = "other"


class ReferralStatus(Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReferralPriority(Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"
    ASAP = "asap"


class ConsentStatus(Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    PENDING = "pending"
    ENTERED_IN_ERROR = "entered_in_error"


class ConsentScope(Enum):
    PATIENT_CARE = "patient_care"
    RESEARCH = "research"
    SHARING = "sharing"
    EMERGENCY = "emergency"
    INSURANCE = "insurance"
    MARKETING = "marketing"
    GENERAL = "general"


class InsuranceType(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    SOCIAL = "social"
    EMPLOYER = "employer"
    TRAVEL = "travel"
    OTHER = "other"


class CoverageStatus(Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    DRAFT = "draft"
    ENTERED_IN_ERROR = "entered_in_error"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class HealthCardStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class MergeStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_MERGED = "auto_merged"
    COMPLETED = "completed"


class MergeMethod(Enum):
    NID_EXACT = "nid_exact"
    PROBABILISTIC = "probabilistic"
    MANUAL = "manual"
    BIOMETRIC = "biometric"
    FAMILY = "family"
    AUTO = "auto"


class PurposeOfUse(Enum):
    TREATMENT = "treatment"
    PAYMENT = "payment"
    OPERATIONS = "operations"
    RESEARCH = "research"
    PUBLIC_HEALTH = "public_health"
    QUALITY_IMPROVEMENT = "quality_improvement"
    EMERGENCY = "emergency"
    FRAUD_DETECTION = "fraud_detection"
    DISCLOSURE = "disclosure"
    OTHER = "other"


class BreakGlassReason(Enum):
    EMERGENCY = "emergency"
    PATIENT_CONSENT = "patient_consent"
    PUBLIC_SAFETY = "public_safety"
    LEGAL = "legal"
    OTHER = "other"


class WorkflowStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"
    COMPENSATED = "compensated"


class WorkflowType(Enum):
    PATIENT_REGISTRATION = "patient_registration"
    APPOINTMENT = "appointment"
    ADMISSION = "admission"
    ENCOUNTER = "encounter"
    REFERRAL = "referral"
    SPECIMEN_COLLECTION = "specimen_collection"
    LAB_ORDER = "lab_order"
    RADIOLOGY_ORDER = "radiology_order"
    MEDICATION = "medication"
    DISCHARGE = "discharge"
    DEATH_REGISTRATION = "death_registration"
    MERGE_IDENTITY = "merge_identity"
    VERIFICATION = "verification"
    APPROVAL = "approval"
    CANCELLATION = "cancellation"
    CORRECTION = "correction"


class BloodGroup(Enum):
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"
    UNKNOWN = "unknown"


class BiometricType(Enum):
    FACE = "face"
    FINGERPRINT = "fingerprint"
    IRIS = "iris"
    PALM = "palm"
    VOICE = "voice"
    SIGNATURE = "signature"
    OTHER = "other"


class MaritalStatus(Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"
    UNKNOWN = "unknown"
