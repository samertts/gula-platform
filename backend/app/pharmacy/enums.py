from __future__ import annotations

from app._compat import StrEnum


class DrugCategory(StrEnum):
    GENERIC = "generic"
    BRAND = "brand"
    BIOLOGIC = "biologic"
    BIOSIMILAR = "biosimilar"
    VACCINE = "vaccine"
    CONTRAST = "contrast"
    RADIOPHARMACEUTICAL = "radiopharmaceutical"
    OTHER = "other"


class DosageForm(StrEnum):
    TABLET = "tablet"
    CAPSULE = "capsule"
    INJECTION = "injection"
    INFUSION = "infusion"
    SYRUP = "syrup"
    SUSPENSION = "suspension"
    CREAM = "cream"
    OINTMENT = "ointment"
    DROPS = "drops"
    INHALER = "inhaler"
    SUPPOSITORY = "suppository"
    PATCH = "patch"
    POWDER = "powder"
    SOLUTION = "solution"
    OTHER = "other"


class RouteOfAdministration(StrEnum):
    ORAL = "oral"
    IV = "iv"
    IM = "im"
    SC = "sc"
    TOPICAL = "topical"
    INHALATION = "inhalation"
    RECTAL = "rectal"
    VAGINAL = "vaginal"
    SUBLINGUAL = "sublingual"
    BUCCAL = "buccal"
    INTRATHECAL = "intrathecal"
    EPIDURAL = "epidural"
    NASAL = "nasal"
    OPHTHALMIC = "ophthalmic"
    OTIC = "otic"
    OTHER = "other"


class DispenseStatus(StrEnum):
    PENDING = "pending"
    PREPARED = "prepared"
    VERIFIED = "verified"
    DISPENSED = "dispensed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class PrescriptionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    ON_HOLD = "on_hold"
    SUSPENDED = "suspended"


class StockMovementType(StrEnum):
    RECEIVED = "received"
    DISPENSED = "dispensed"
    TRANSFERRED = "transferred"
    RETURNED = "returned"
    ADJUSTED = "adjusted"
    EXPIRED = "expired"
    DAMAGED = "damaged"
    WASTED = "wasted"


class StorageCondition(StrEnum):
    ROOM_TEMPERATURE = "room_temperature"
    REFRIGERATED = "refrigerated"
    FROZEN = "frozen"
    CONTROLLED_ROOM_TEMP = "controlled_room_temp"
    COLD_CHAIN = "cold_chain"


class InteractionSeverity(StrEnum):
    CONTRAINDICATED = "contraindicated"
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"
    NOTE = "note"
