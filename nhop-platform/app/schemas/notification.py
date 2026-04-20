"""Pydantic v2 schemas for the notifications API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..models.notification import NotificationPriority, NotificationType


class NotificationBase(BaseModel):
    type: NotificationType
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=2000)
    priority: NotificationPriority = NotificationPriority.medium
    related_type: Optional[str] = Field(default=None, max_length=40)
    related_id: Optional[str] = Field(default=None, max_length=80)


class NotificationCreate(NotificationBase):
    recipient_id: str = Field(..., min_length=1, max_length=80)
    recipient_role: str = Field(..., min_length=1, max_length=40)


class NotificationRead(NotificationBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    recipient_id: str
    recipient_role: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None


class NotificationListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[NotificationRead]


class NotificationUnreadCount(BaseModel):
    unread: int
