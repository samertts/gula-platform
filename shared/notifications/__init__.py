from .resend import (
    EmailSendResult,
    ResendEmailClient,
    get_email_client,
)
from .resend import (
    send_email as send_email_resend,
)
from .sender import (
    NotificationSender,
    send_email,
    send_push,
    send_sms,
    send_telegram,
    send_whatsapp,
)
from .telegram import (
    TelegramNotificationService,
    TelegramSendResult,
    get_telegram_service,
)
from .telegram import (
    send_telegram as send_telegram_msg,
)
from .template import (
    NotificationTemplate,
    get_template,
    register_template,
    render_template,
)

__all__ = [
    "EmailSendResult",
    "NotificationSender",
    "NotificationTemplate",
    "ResendEmailClient",
    "TelegramNotificationService",
    "TelegramSendResult",
    "get_email_client",
    "get_telegram_service",
    "get_template",
    "register_template",
    "render_template",
    "send_email",
    "send_email_resend",
    "send_push",
    "send_sms",
    "send_telegram",
    "send_telegram_msg",
    "send_whatsapp",
]
