from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import declared_attr


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class AuditMixin(TimestampMixin):
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)


class TenantMixin:
    lab_id = Column(Integer, nullable=False, index=True)


class OptimisticLockMixin:
    version = Column(Integer, default=1, nullable=False)
