from __future__ import annotations

from app._compat import StrEnum


class NotificationChannel(StrEnum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBSOCKET = "websocket"
    IN_APP = "in_app"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    GOVERNMENT_GATEWAY = "government_gateway"
    WEBHOOK = "webhook"
    FAX = "fax"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    READ = "read"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class NotificationPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class NotificationCategory(StrEnum):
    APPOINTMENT = "appointment"
    LAB_RESULT = "lab_result"
    PRESCRIPTION = "prescription"
    ALERT = "alert"
    REMINDER = "reminder"
    PROMOTIONAL = "promotional"
    SYSTEM = "system"
    ADMINISTRATIVE = "administrative"
    EMERGENCY = "emergency"
    COMPLIANCE = "compliance"


class TemplateEngine(StrEnum):
    JINJA2 = "jinja2"
    MUSTACHE = "mustache"
    HANDLEBARS = "handlebars"
    FREEMARKER = "freemarker"
    CUSTOM = "custom"


class DeliveryReportStatus(StrEnum):
    SENT_TO_PROVIDER = "sent_to_provider"
    DELIVERED_TO_DEVICE = "delivered_to_device"
    READ_BY_USER = "read_by_user"
    FAILED_PERMANENT = "failed_permanent"
    FAILED_TEMPORARY = "failed_temporary"
    EXPIRED = "expired"
