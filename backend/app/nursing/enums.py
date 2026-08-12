from app._compat import StrEnum


class ShiftType(StrEnum):
    MORNING = "morning"
    EVENING = "evening"
    NIGHT = "night"
    ROTATING = "rotating"


class NursingTaskType(StrEnum):
    VITAL_SIGNS = "vital_signs"
    MEDICATION_ADMIN = "medication_admin"
    WOUND_CARE = "wound_care"
    CATHETER_CARE = "catheter_care"
    FEEDING = "feeding"
    HYGIENE = "hygiene"
    MOBILIZATION = "mobilization"
    OBSERVATION = "observation"
    ASSESSMENT = "assessment"
    PATIENT_EDUCATION = "patient_education"
    OTHER = "other"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class PainLevel(StrEnum):
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class FallRiskLevel(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class PressureInjuryStage(StrEnum):
    STAGE1 = "stage1"
    STAGE2 = "stage2"
    STAGE3 = "stage3"
    STAGE4 = "stage4"
    UNSTAGEABLE = "unstageable"
    SUSPECTED_DEEP_TISSUE = "suspected_deep_tissue"
    DEVICE_RELATED = "device_related"


class FluidCategory(StrEnum):
    INTAKE_ORAL = "intake_oral"
    INTAKE_IV = "intake_iv"
    INTAKE_NG_TUBE = "intake_ng_tube"
    INTAKE_TPN = "intake_tpn"
    OUTPUT_URINE = "output_urine"
    OUTPUT_STOOL = "output_stool"
    OUTPUT_VOMIT = "output_vomit"
    OUTPUT_DRAIN = "output_drain"
    OUTPUT_BLOOD_LOSS = "output_blood_loss"
    NET = "net"


class NutritionStatus(StrEnum):
    WELL_NOURISHED = "well_nourished"
    AT_RISK = "at_risk"
    MODERATELY_MALNOURISHED = "moderately_malnourished"
    SEVERELY_MALNOURISHED = "severely_malnourished"


class HandoverType(StrEnum):
    SHIFT_CHANGE = "shift_change"
    TRANSFER = "transfer"
    DISCHARGE = "discharge"
    REFERRAL = "referral"
    ESCALATION = "escalation"


class AssessmentType(StrEnum):
    ADMISSION = "admission"
    DAILY = "daily"
    WEEKLY = "weekly"
    CHANGE_IN_CONDITION = "change_in_condition"
    PRE_OP = "pre_op"
    POST_OP = "post_op"
    DISCHARGE = "discharge"
    TRANSFER = "transfer"


class DelegationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COMPLETED = "completed"


class AssignmentType(StrEnum):
    PRIMARY = "primary"
    ASSOCIATE = "associate"
    FLOAT = "float"
    CHARGE_NURSE = "charge_nurse"
