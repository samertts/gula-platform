from app._compat import StrEnum


class AdmissionType(StrEnum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    ELECTIVE = "elective"
    MATERNITY = "maternity"
    NEWBORN = "newborn"
    TRANSFER = "transfer"


class DischargeType(StrEnum):
    HOME = "home"
    TRANSFER = "transfer"
    AMA = "against_medical_advice"
    DECEASED = "deceased"
    LEFT_WITHOUT_TREATMENT = "left_without_treatment"
    HOSPICE = "hospice"
    OTHER = "other"


class QueuePriority(StrEnum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    FOLLOW_UP = "follow_up"


class QueueStatus(StrEnum):
    WAITING = "waiting"
    SEEN = "seen"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class ClinicalTaskStatus(StrEnum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"


class ShiftType(StrEnum):
    MORNING = "morning"
    EVENING = "evening"
    NIGHT = "night"


class RoomStatus(StrEnum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    CLEANING = "cleaning"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"


class AlertSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"
