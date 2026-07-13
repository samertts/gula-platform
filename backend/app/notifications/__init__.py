from __future__ import annotations

from .telegram import TelegramGateway, send_telegram
from .service import NotificationResult, NotificationService, get_service

__all__ = [
    "TelegramGateway",
    "send_telegram",
    "NotificationResult",
    "NotificationService",
    "get_service",
]
