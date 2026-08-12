from __future__ import annotations

from enum import Enum


class ModalityType(Enum):
    MRI = "mri"
    CT = "ct"
    XR = "xr"
    US = "us"
    MG = "mg"
    FL = "fl"
    NM = "nm"
    PET = "pet"
    SPECT = "spect"
    DXA = "dxa"
    OTHER = "other"


class ExamStatus(Enum):
    SCHEDULED = "scheduled"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CANCELLED = "cancelled"
    REPORTED = "reported"
    APPROVED = "approved"


class ProtocolType(Enum):
    STANDARD = "standard"
    CONTRAST = "contrast"
    NON_CONTRAST = "non_contrast"
    DYNAMIC = "dynamic"
    INTERVENTIONAL = "interventional"
    EMERGENCY = "emergency"


class ContrastType(Enum):
    IODINATED = "iodinated"
    GADOLINIUM = "gadolinium"
    BARIUM = "barium"
    AIR = "air"
    SALINE = "saline"
    MICROBUBBLE = "microbubble"
    NONE = "none"


class FindingCriticality(Enum):
    NON_CRITICAL = "non_critical"
    CRITICAL = "critical"
    CRITICAL_RED = "critical_red"
    ACTIONABLE = "actionable"


class ReportStatus(Enum):
    DRAFT = "draft"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"
    CANCELLED = "cancelled"


class ImageQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    NON_DIAGNOSTIC = "non_diagnostic"


class SharingStatus(Enum):
    PRIVATE = "private"
    HOSPITAL = "hospital"
    NATIONAL = "national"
    RESEARCH = "research"


class ArchiveTier(Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    DEEP_ARCHIVE = "deep_archive"


class AnnotationType(Enum):
    TEXT = "text"
    MEASUREMENT = "measurement"
    REGION = "region"
    ARROW = "arrow"
    FREEHAND = "freehand"
    ELLIPSE = "ellipse"
    LINE = "line"
    MARKER = "marker"


class SharingType(Enum):
    DIRECT = "direct"
    LINK = "link"
    QR = "qr"


class DeviceStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class StorageCompressionType(Enum):
    NONE = "none"
    LOSSLESS = "lossless"
    LOSSLESS_JPEG_LS = "lossless_jpeg_ls"
    LOSSLESS_JPEG_2000 = "lossless_jpeg_2000"
    LOSSY_JPEG = "lossy_jpeg"
    LOSSY_JPEG_2000 = "lossy_jpeg_2000"


class CriticalFindingStatus(Enum):
    PENDING = "pending"
    NOTIFIED = "notified"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
