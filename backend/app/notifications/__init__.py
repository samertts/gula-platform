from __future__ import annotations

from .service import NotificationResult, NotificationService, get_service
from .telegram import TelegramGateway, send_telegram

__all__ = [
    "NotificationResult",
    "NotificationService",
    "TelegramGateway",
    "get_service",
    "send_telegram",
]
