from enum import Enum


class GovernanceNodeType(Enum):
    REPUBLIC = "republic"
    MINISTRY = "ministry"
    DIRECTORATE = "directorate"
    HOSPITAL = "hospital"
    PRIMARY_HEALTHCARE_CENTER = "primary_healthcare_center"
    SPECIALIZED_CENTER = "specialized_center"
    LABORATORY = "laboratory"
    DEPARTMENT = "department"
    UNIT = "unit"
    EMPLOYEE = "employee"


class DelegationType(Enum):
    FULL = "full"
    LIMITED = "limited"
    EMERGENCY = "emergency"
    TEMPORARY = "temporary"


class DelegationStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


class ActingRoleStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class AdministrationType(Enum):
    REGIONAL = "regional"
    EMERGENCY = "emergency"
    TEMPORARY = "temporary"


class HealthNumberStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LOST = "lost"
    REPLACED = "replaced"
    MERGED = "merged"
    RETIRED = "retired"


class HealthCardType(Enum):
    CITIZEN = "citizen"
    DIGITAL = "digital"
    LABORATORY = "laboratory"
    RADIOLOGY = "radiology"
    HOSPITAL = "hospital"
    INSURANCE = "insurance"


class CardLifecycleEvent(Enum):
    ISSUED = "issued"
    LOST = "lost"
    REISSUED = "reissued"
    SUSPENDED = "suspended"
    ACTIVATED = "activated"
    EXPIRED = "expired"
    RETIRED = "retired"


class IdentityMergeAction(Enum):
    MERGED = "merged"
    SPLIT = "split"
    HISTORICAL_LINK = "historical_link"


class ConnectorType(Enum):
    NATIONAL_ID = "national_id"
    BIRTH_REGISTRY = "birth_registry"
    DEATH_REGISTRY = "death_registry"
    CIVIL_STATUS = "civil_status"
    PASSPORT = "passport"
    RESIDENCE = "residence"
    VISA = "visa"
    FAMILY_REGISTRY = "family_registry"
    RATION_CARD = "ration_card"


class ConnectorMode(Enum):
    STUB = "stub"
    LIVE = "live"
    SHADOW = "shadow"


class LicenseStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    PENDING = "pending"


class BoardStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class CompetencyLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"


class ProductivityPeriod(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class LabType(Enum):
    PRIVATE = "private"
    GOVERNMENT = "government"
    MILITARY = "military"
    UNIVERSITY = "university"
    VETERINARY = "veterinary"
    FOOD = "food"
    ENVIRONMENTAL = "environmental"
    FORENSIC = "forensic"
    REFERENCE = "reference"


class EquipmentStatus(Enum):
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    CALIBRATION_DUE = "calibration_due"
    OUT_OF_SERVICE = "out_of_service"
    RETIRED = "retired"


class QCStatus(Enum):
    IN_CONTROL = "in_control"
    OUT_OF_CONTROL = "out_of_control"
    WARNING = "warning"
    NOT_RUN = "not_run"


class EQAResult(Enum):
    ACCEPTABLE = "acceptable"
    BORDERLINE = "borderline"
    UNACCEPTABLE = "unacceptable"
    NOT_SUBMITTED = "not_submitted"


class ClinicalPolicyType(Enum):
    CLINICAL = "clinical"
    LABORATORY = "laboratory"
    RADIOLOGY = "radiology"
    MEDICATION = "medication"
    INFECTION_CONTROL = "infection_control"
    PATIENT_SAFETY = "patient_safety"


class PolicyStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    UNDER_REVIEW = "under_review"
    SUPERSEDED = "superseded"
    RETIRED = "retired"


class WestgardRule(Enum):
    ONE_2S = "1_2s"
    ONE_3S = "1_3s"
    TWO_2S = "2_2s"
    R_4S = "r_4s"
    FOUR_1S = "4_1s"
    TEN_X = "10x"


class SecurityPolicyCategory(Enum):
    ACCESS_CONTROL = "access_control"
    DATA_PROTECTION = "data_protection"
    NETWORK_SECURITY = "network_security"
    INCIDENT_RESPONSE = "incident_response"
    AUDIT = "audit"
    COMPLIANCE = "compliance"
    ENCRYPTION = "encryption"
    BREAK_GLASS = "break_glass"


class DataClassificationLevel(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


class ThreatSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(Enum):
    DETECTED = "detected"
    ANALYZING = "analyzing"
    CONTAINING = "containing"
    RESOLVED = "resolved"
    CLOSED = "closed"


class InteropProtocolType(Enum):
    FHIR = "fhir"
    HL7 = "hl7"
    DICOM = "dicom"
    OPENAPI = "openapi"
    GRAPHQL = "graphql"
    REST = "rest"
    GRPC = "grpc"
    MQTT = "mqtt"
    AMQP = "amqp"
    EVENT_BUS = "event_bus"
    IHE = "ihe"


class InteropProtocolStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class AIRiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AIGuardrailType(Enum):
    PROMPT_INJECTION = "prompt_injection"
    HALLUCINATION = "hallucination"
    BIAS = "bias"
    SAFETY = "safety"
    PRIVACY = "privacy"
    CLINICAL_VALIDATION = "clinical_validation"


class AIAuditAction(Enum):
    INFERENCE = "inference"
    TRAINING = "training"
    EVALUATION = "evaluation"
    DEPLOYMENT = "deployment"
    HUMAN_OVERRIDE = "human_override"
    GUARDRAIL_TRIGGERED = "guardrail_triggered"


class AnalyticsScope(Enum):
    NATIONAL = "national"
    GOVERNORATE = "governorate"
    DIRECTORATE = "directorate"
    HOSPITAL = "hospital"
    LABORATORY = "laboratory"


class CertificateStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"
