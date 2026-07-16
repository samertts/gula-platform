from __future__ import annotations

from enum import Enum


class DeviceCategory(Enum):
    DIAGNOSTIC_IMAGING = "diagnostic_imaging"
    LABORATORY = "laboratory"
    PATIENT_MONITORING = "patient_monitoring"
    THERAPEUTIC = "therapeutic"
    SURGICAL = "surgical"
    LIFE_SUPPORT = "life_support"
    RESPIRATORY = "respiratory"
    INFUSION = "infusion"
    DIALYSIS = "dialysis"
    REHABILITATION = "rehabilitation"
    DENTAL = "dental"
    OPHTHALMIC = "ophthalmic"
    STERILIZATION = "sterilization"
    FURNITURE = "furniture"
    MOBILE = "mobile"
    OTHER = "other"


class DeviceStatus(Enum):
    IN_USE = "in_use"
    AVAILABLE = "available"
    UNDER_MAINTENANCE = "under_maintenance"
    CALIBRATION_DUE = "calibration_due"
    OUT_OF_SERVICE = "out_of_service"
    DECOMMISSIONED = "decommissioned"
    RESERVED = "reserved"
    QUARANTINED = "quarantined"
    LOST = "lost"
    STOLEN = "stolen"


class RiskClass(Enum):
    CLASS_I = "class_i"
    CLASS_IIA = "class_iia"
    CLASS_IIB = "class_iib"
    CLASS_III = "class_iii"


class MaintenanceType(Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    PREDICTIVE = "predictive"
    EMERGENCY = "emergency"
    ROUTINE = "routine"
    CONDITION_BASED = "condition_based"


class MaintenancePriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MaintenanceStatus(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"


class WorkOrderStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CANCELLED = "cancelled"


class CalibrationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    OUT_OF_TOLERANCE = "out_of_tolerance"
    DEFERRED = "deferred"


class VerificationResult(Enum):
    PASSED = "passed"
    FAILED = "failed"
    CONDITIONAL = "conditional"
    NOT_PERFORMED = "not_performed"


class SafetyInspectionResult(Enum):
    PASSED = "passed"
    FAILED = "failed"
    CONDITIONAL = "conditional"


class AssetLifecycleStage(Enum):
    PLANNING = "planning"
    PROCUREMENT = "procurement"
    INSTALLATION = "installation"
    COMMISSIONING = "commissioning"
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    DECOMMISSIONING = "decommissioning"
    DISPOSAL = "disposal"


class IncidentSeverity(Enum):
    NEAR_MISS = "near_miss"
    MINOR = "minor"
    MODERATE = "moderate"
    SERIOUS = "serious"
    CRITICAL = "critical"
    FATAL = "fatal"


class RecallClass(Enum):
    CLASS_I = "class_i"
    CLASS_II = "class_ii"
    CLASS_III = "class_iii"


class WarrantyStatus(Enum):
    ACTIVE = "active"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"
    EXTENDED = "extended"
    VOID = "void"
