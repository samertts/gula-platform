from __future__ import annotations

from enum import Enum


class BedStatus(Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"


class WardType(Enum):
    GENERAL = "general"
    ICU = "icu"
    NICU = "nicu"
    PICU = "picu"
    CCU = "ccu"
    SURGICAL = "surgical"
    MEDICAL = "medical"
    MATERNITY = "maternity"
    PEDIATRIC = "pediatric"
    PSYCHIATRIC = "psychiatric"
    ISOLATION = "isolation"
    REHABILITATION = "rehabilitation"


class RoomType(Enum):
    PRIVATE = "private"
    SEMI_PRIVATE = "semi_private"
    GENERAL = "general"
    ICU = "icu"
    ISOLATION = "isolation"
    NEGATIVE_PRESSURE = "negative_pressure"
    OPERATING_THEATRE = "operating_theatre"
    RECOVERY = "recovery"
    LABOR_DELIVERY = "labor_delivery"
    EXAMINATION = "examination"
    TREATMENT = "treatment"


class OperatingTheatreStatus(Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    SCHEDULED = "scheduled"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"


class TriageLevel(Enum):
    RESUSCITATION = "resuscitation"
    EMERGENT = "emergent"
    URGENT = "urgent"
    LESS_URGENT = "less_urgent"
    NON_URGENT = "non_urgent"


class TriageCategory(Enum):
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    BLACK = "black"
    WHITE = "white"


class DietType(Enum):
    REGULAR = "regular"
    DIABETIC = "diabetic"
    LOW_SALT = "low_salt"
    LOW_FAT = "low_fat"
    LIQUID = "liquid"
    SOFT = "soft"
    PUREE = "puree"
    TUBE_FEEDING = "tube_feeding"
    NPO = "npo"
    PEDIATRIC = "pediatric"
    RENAL = "renal"
    LIVER = "liver"
    CARDIAC = "cardiac"


class IsolationType(Enum):
    CONTACT = "contact"
    DROPLET = "droplet"
    AIRBORNE = "airborne"
    PROTECTIVE = "protective"
    STRICT = "strict"
    NONE = "none"


class AssetStatus(Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    DECOMMISSIONED = "decommissioned"
    STORED = "stored"
    LOST = "lost"


class ServiceCatalogType(Enum):
    CONSULTATION = "consultation"
    PROCEDURE = "procedure"
    SURGERY = "surgery"
    INVESTIGATION = "investigation"
    THERAPY = "therapy"
    ACCOMMODATION = "accommodation"
    OTHER = "other"


class InvoiceStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class AdmissionType(Enum):
    ELECTIVE = "elective"
    EMERGENCY = "emergency"
    URGENT = "urgent"
    TRANSFER = "transfer"


class DischargeDisposition(Enum):
    HOME = "home"
    TRANSFER = "transfer"
    AGAINST_ADVICE = "against_advice"
    DECEASED = "deceased"
    LEFT_WITHOUT_TREATMENT = "left_without_treatment"
    HOSPICE = "hospice"
