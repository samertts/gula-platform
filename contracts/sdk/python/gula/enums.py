from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    pass


class Role(StrEnum):
    MASTER_ADMIN = "master_admin"
    MINISTRY_ADMIN = "ministry_admin"
    PROVINCE_ADMIN = "province_admin"
    LAB_ADMIN = "lab_admin"
    ADMIN = "admin"
    DOCTOR = "doctor"
    TECHNICIAN = "technician"
    STAFF = "staff"
    LAB_STAFF = "lab_staff"
    CITIZEN = "citizen"
    NURSE = "nurse"
    PATHOLOGIST = "pathologist"
    RECEPTIONIST = "receptionist"
    RESEARCHER = "researcher"
    SUPER_ADMIN = "super_admin"
    MINISTRY = "ministry"
    LAB_TECH = "lab_tech"


class Permission(StrEnum):
    READ_PATIENTS = "read:patients"
    WRITE_PATIENTS = "write:patients"
    READ_ORDERS = "read:orders"
    WRITE_ORDERS = "write:orders"
    READ_RESULTS = "read:results"
    WRITE_RESULTS = "write:results"
    READ_SAMPLES = "read:samples"
    WRITE_SAMPLES = "write:samples"
    MANAGE_USERS = "manage:users"
    MANAGE_LABS = "manage:labs"
    VIEW_AUDIT = "view:audit"
    MANAGE_SYSTEM = "manage:system"
    VIEW_ANALYTICS = "view:analytics"
    PATIENTS_READ = "patients:read"
    PATIENTS_WRITE = "patients:write"
    PATIENTS_DELETE = "patients:delete"
    ORDERS_READ = "orders:read"
    ORDERS_WRITE = "orders:write"
    RESULTS_READ = "results:read"
    RESULTS_WRITE = "results:write"
    STAFF_MANAGE = "staff:manage"
    LAB_READ = "lab:read"
    LAB_MANAGE = "lab:manage"
    DASHBOARD_READ = "dashboard:read"
    AUDIT_READ = "audit:read"
    PLATFORM_MANAGE_LABS = "platform:manage_labs"
    PLATFORM_MANAGE_USERS = "platform:manage_users"
    PLATFORM_VIEW_STATS = "platform:view_stats"
    SYSTEM_ADMIN = "system:admin"


class OrderStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    VALIDATED = "validated"
    CANCELLED = "cancelled"


class TestResultStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ClaimStatus(StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PAID = "paid"


class DeviceStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    QUARANTINED = "quarantined"
    REVOKED = "revoked"
    OFFLINE = "offline"


class TaskStatus(StrEnum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    DONE = "done"
    DEAD = "dead"


class LabType(StrEnum):
    PRIVATE = "private"
    GOVERNMENT = "government"
    HOSPITAL = "hospital"
    CLINIC = "clinic"


class DeploymentMode(StrEnum):
    SINGLE = "single"
    MULTI_BRANCH = "multi_branch"
    GOVERNMENT = "government"


class SecurityLevel(StrEnum):
    STANDARD = "standard"
    HIGH_SECURITY = "high_security"
    AIR_GAPPED = "air_gapped"


class Tier(StrEnum):
    STARTER = "starter"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"


class SampleType(StrEnum):
    BLOOD = "blood"
    URINE = "urine"
    STOOL = "stool"
    SWAB = "swab"
    SERUM = "serum"
    PLASMA = "plasma"
    CSF = "csf"
    SPUTUM = "sputum"
    TISSUE = "tissue"
    OTHER = "other"


class SpecimenStatus(StrEnum):
    COLLECTED = "collected"
    RECEIVED = "received"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    REJECTED = "rejected"


class InstrumentStatus(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    CALIBRATING = "calibrating"
    ERROR = "error"


class Gender(StrEnum):
    MALE = "M"
    FEMALE = "F"


class Modality(StrEnum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"
    IN_APP = "in_app"


class Action(StrEnum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    VERIFY = "verify"
    APPROVE = "approve"
    REJECT = "reject"
    VALIDATE = "validate"
    SUBMIT = "submit"
    CANCEL = "cancel"


class Channel(StrEnum):
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"


class FeatureKey(StrEnum):
    PATIENT_MANAGEMENT = "patient_management"
    BASIC_RESULTS = "basic_results"
    SAMPLE_TRACKING = "sample_tracking"
    PDF_REPORTS = "pdf_reports"
    QR_CODES = "qr_codes"
    NOTIFICATIONS = "notifications"
    AUDIT_LOG = "audit_log"
    MOBILE_ACCESS = "mobile_access"
    QUALITY_CONTROL = "quality_control"
    BATCH_IMPORT = "batch_import"
    BATCH_EXPORT = "batch_export"
    EHR_INTEGRATION = "ehr_integration"
    ADVANCED_ANALYTICS = "advanced_analytics"
    CRITICAL_ALERTS = "critical_alerts"
    INSURANCE_INTEGRATION = "insurance_integration"
    NATIONAL_ID_LOOKUP = "national_id_lookup"
    DEVICE_RESULTS = "device_results"
    MULTI_BRANCH = "multi_branch"
    GOVERNMENT_REPORTING = "government_reporting"
    AI_INTERPRETATION = "ai_interpretation"
    AI_ANOMALY_DETECTION = "ai_anomaly_detection"
    AI_EPIDEMIOLOGY = "ai_epidemiology"
    CUSTOM_BRANDING = "custom_branding"
    API_ACCESS = "api_access"
    SLA_GUARANTEE = "sla_guarantee"
    WHITE_LABEL = "white_label"
    PRIORITY_SUPPORT = "priority_support"
    CROSS_BRANCH_REPORTS = "cross_branch_reports"
    COMPLIANCE_DASHBOARD = "compliance_dashboard"
    MINISTRY_INTEGRATION = "ministry_integration"
    TWO_FACTOR_REQUIRED = "two_factor_required"
    AUDIT_CHAIN = "audit_chain"
    SESSION_TIMEOUT_SHORT = "session_timeout_short"
    AIR_GAPPED_MODE = "air_gapped_mode"


class PrivacyLevel(StrEnum):
    STANDARD = "standard"
    SENSITIVE = "sensitive"
    PHI = "phi"


class ModelStatus(StrEnum):
    DRAFT = "draft"
    CANARY = "canary"
    ACTIVE = "active"
    RETIRED = "retired"
    BLOCKED = "blocked"


class AppointmentStatus(StrEnum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class NodeType(StrEnum):
    COUNTRY = "country"
    GOVERNORATE = "governorate"
    DIRECTORATE = "directorate"
    PROVINCE = "province"
    DISTRICT = "district"
    FACILITY = "facility"
    DEPARTMENT = "department"


class Profession(StrEnum):
    DOCTOR = "doctor"
    NURSE = "nurse"
    TECHNICIAN = "technician"
    PHARMACIST = "pharmacist"
    ADMINISTRATOR = "administrator"
    LABORATORIAN = "laboratorian"
    RADIOLOGIST = "radiologist"
    OTHER = "other"


class BillingCycle(StrEnum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    QUARTERLY = "quarterly"
