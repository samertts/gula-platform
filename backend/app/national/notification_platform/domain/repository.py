from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from .entities import (
    DeliveryReport,
    Notification,
    NotificationBatch,
    NotificationPreference,
    NotificationTemplate,
)
from .enums import NotificationCategory, NotificationChannel, NotificationStatus


class NotificationRepository(ABC):
    @abstractmethod
    async def save(self, notification: Notification) -> Notification: ...

    @abstractmethod
    async def get(self, notification_id: str) -> Notification | None: ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[Notification]: ...

    @abstractmethod
    async def find_by_status(
        self,
        status: NotificationStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Notification]: ...

    @abstractmethod
    async def find_by_channel(
        self,
        channel: NotificationChannel,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Notification]: ...

    @abstractmethod
    async def find_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Notification]: ...

    @abstractmethod
    async def find_by_correlation_id(
        self,
        correlation_id: str,
    ) -> list[Notification]: ...

    @abstractmethod
    async def count_by_status(self, status: NotificationStatus) -> int: ...

    @abstractmethod
    async def count_by_channel(self, channel: NotificationChannel) -> int: ...

    @abstractmethod
    async def get_stats(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> dict[str, Any]: ...


class NotificationTemplateRepository(ABC):
    @abstractmethod
    async def save(self, template: NotificationTemplate) -> NotificationTemplate: ...

    @abstractmethod
    async def get(self, template_id: str) -> NotificationTemplate | None: ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[NotificationTemplate]: ...

    @abstractmethod
    async def find_by_channel(
        self,
        channel: NotificationChannel,
        skip: int = 0,
        limit: int = 100,
    ) -> list[NotificationTemplate]: ...

    @abstractmethod
    async def find_by_category(
        self,
        category: NotificationCategory,
        skip: int = 0,
        limit: int = 100,
    ) -> list[NotificationTemplate]: ...

    @abstractmethod
    async def find_by_language(
        self,
        language: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[NotificationTemplate]: ...

    @abstractmethod
    async def delete(self, template_id: str) -> None: ...


class DeliveryReportRepository(ABC):
    @abstractmethod
    async def save(self, report: DeliveryReport) -> DeliveryReport: ...

    @abstractmethod
    async def get(self, report_id: str) -> DeliveryReport | None: ...

    @abstractmethod
    async def find_by_notification(
        self,
        notification_id: str,
    ) -> list[DeliveryReport]: ...


class NotificationPreferenceRepository(ABC):
    @abstractmethod
    async def save(self, preference: NotificationPreference) -> NotificationPreference: ...

    @abstractmethod
    async def get(
        self, user_id: str, channel: NotificationChannel,
    ) -> NotificationPreference | None: ...

    @abstractmethod
    async def find_by_user(self, user_id: str) -> list[NotificationPreference]: ...

    @abstractmethod
    async def find_by_user_and_channel(
        self,
        user_id: str,
        channel: NotificationChannel,
    ) -> NotificationPreference | None: ...


class NotificationBatchRepository(ABC):
    @abstractmethod
    async def save(self, batch: NotificationBatch) -> NotificationBatch: ...

    @abstractmethod
    async def get(self, batch_id: str) -> NotificationBatch | None: ...

    @abstractmethod
    async def find_by_status(
        self,
        status: NotificationStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> list[NotificationBatch]: ...
