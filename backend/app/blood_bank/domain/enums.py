from __future__ import annotations

from enum import Enum


class ABOGroup(Enum):
    A = "A"
    B = "B"
    AB = "AB"
    O = "O"
    UNKNOWN = "unknown"


class RhFactor(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    UNKNOWN = "unknown"


class DonorStatus(Enum):
    ACTIVE = "active"
    DEFERRED = "deferred"
    INACTIVE = "inactive"
    PERMANENTLY_DEFERRED = "permanently_deferred"
    EXPIRED = "expired"


class DeferralType(Enum):
    TEMPORARY = "temporary"
    PERMANENT = "permanent"


class DeferralReason(Enum):
    LOW_HEMOGLOBIN = "low_hemoglobin"
    LOW_WEIGHT = "low_weight"
    HIGH_RISK_BEHAVIOR = "high_risk_behavior"
    TRAVEL = "travel"
    MEDICAL_CONDITION = "medical_condition"
    MEDICATION = "medication"
    RECENT_VACCINATION = "recent_vaccination"
    PREGNANCY = "pregnancy"
    TATTOO_PIERCING = "tattoo_piercing"
    SURGERY = "surgery"
    MALARIA_RISK = "malaria_risk"
    OTHER = "other"


class DonationType(Enum):
    WHOLE_BLOOD = "whole_blood"
    PLATELET = "platelet"
    PLASMA = "plasma"
    DOUBLE_RED_CELL = "double_red_cell"
    AUTOLOGOUS = "autologous"
    DIRECTED = "directed"


class DonationStatus(Enum):
    REGISTERED = "registered"
    SCREENED = "screened"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    DISCARDED = "discarded"


class CollectionMethod(Enum):
    MANUAL = "manual"
    APHERESIS = "apheresis"


class BloodComponent(Enum):
    WHOLE_BLOOD = "whole_blood"
    PACKED_RBC = "packed_rbc"
    FRESH_FROZEN_PLASMA = "ffp"
    PLATELET_CONCENTRATE = "platelet_concentrate"
    CRYOPRECIPITATE = "cryoprecipitate"
    CRYOSUPERNATANT = "cryosupernatant"
    GRANULOCYTES = "granulocytes"
    WASHED_RBC = "washed_rbc"
    IRRADIATED_RBC = "irradiated_rbc"
    LEUKOCYTE_REDUCED = "leukocyte_reduced"


class ComponentStatus(Enum):
    PENDING_PROCESSING = "pending_processing"
    PROCESSING = "processing"
    AVAILABLE = "available"
    QUARANTINED = "quarantined"
    RESERVED = "reserved"
    ISSUED = "issued"
    TRANSFUSED = "transfused"
    DISCARDED = "discarded"
    EXPIRED = "expired"
    RECALLED = "recalled"


class CrossmatchStatus(Enum):
    PENDING = "pending"
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    PARTIALLY_COMPATIBLE = "partially_compatible"
    WAIVED = "waived"


class CrossmatchType(Enum):
    FULL = "full"
    ELECTRONIC = "electronic"
    EMERGENCY = "emergency"


class TransfusionStatus(Enum):
    ORDERED = "ordered"
    DISPENSED = "dispensed"
    VERIFIED = "verified"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REACTED = "reacted"
    CANCELLED = "cancelled"


class TransfusionReactionSeverity(Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    LIFE_THREATENING = "life_threatening"
    FATAL = "fatal"


class TransfusionReactionType(Enum):
    FEBRILE_NON_HEMOLYTIC = "febrile_non_hemolytic"
    ALLERGIC = "allergic"
    ACUTE_HEMOLYTIC = "acute_hemolytic"
    DELAYED_HEMOLYTIC = "delayed_hemolytic"
    BACTERIAL_CONTAMINATION = "bacterial_contamination"
    TRANSFUSION_RELATED_ALI = "trali"
    TRANSFUSION_CIRCULATORY_OVERLOAD = "taco"
    TRANSFUSION_ASSOCIATED_GVHD = "tagvhd"
    POST_TRANSFUSION_PURPURA = "post_transfusion_purpura"
    OTHER = "other"


class ScreeningTest(Enum):
    HIV = "hiv"
    HEPATITIS_B = "hepatitis_b"
    HEPATITIS_C = "hepatitis_c"
    SYPHILIS = "syphilis"
    HTLV = "htlv"
    MALARIA = "malaria"
    WEST_NILE = "west_nile"
    CHAGAS = "chagas"
    ZIKA = "zika"
    ALT = "alt"


class ScreeningResult(Enum):
    NEGATIVE = "negative"
    POSITIVE = "positive"
    INDETERMINATE = "indeterminate"
    PENDING = "pending"
    NOT_TESTED = "not_tested"


class StorageCondition(Enum):
    ROOM_TEMPERATURE = "room_temperature"
    REFRIGERATED = "refrigerated"
    FROZEN = "frozen"
    CRYO_FROZEN = "cryo_frozen"
    AGITATED = "agitaded"


class InventoryMovementType(Enum):
    RECEIVED = "received"
    ISSUED = "issued"
    TRANSFERRED = "transferred"
    RETURNED = "returned"
    DISCARDED = "discarded"
    EXPIRED = "expired"
    RECALLED = "recalled"
    RESERVED = "reserved"
    UNRESERVED = "unreserved"
