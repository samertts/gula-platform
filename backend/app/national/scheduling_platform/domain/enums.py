from __future__ import annotations

from app._compat import StrEnum


class AppointmentStatus(StrEnum):
    PROPOSED = "proposed"
    PENDING = "pending"
    BOOKED = "booked"
    ARRIVED = "arrived"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    ENTERED_IN_ERROR = "entered_in_error"


class ResourceType(StrEnum):
    ROOM = "room"
    DEVICE = "device"
    EQUIPMENT = "equipment"
    VEHICLE = "vehicle"
    PERSONNEL = "personnel"
    CONSUMABLE = "consumable"


class SlotStatus(StrEnum):
    AVAILABLE = "available"
    BOOKED = "booked"
    BLOCKED = "blocked"
    MAINTENANCE = "maintenance"


class RecurrencePattern(StrEnum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class ConflictLevel(StrEnum):
    NONE = "none"
    SOFT = "soft"
    HARD = "hard"
