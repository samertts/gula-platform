from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Integer
from sqlalchemy.orm import declarative_base

# Single authoritative declarative metadata for the national/EHR bound
# contexts (PROGRAM-STABLE-002 shared-core extraction). Both the national
# domain and the EHR domain register their tables on this metadata so that
# cross-context foreign keys resolve; keeping it in Shared Core removes the
# `app.ehr <-> app.national` import cycle (ehr/base.py previously imported
# `app.national.base`, while `app.national.fhir.*` imports `app.ehr.models.*`).
SharedBase = declarative_base()


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


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


class BaseEntityMixin:
    """Shared utility methods for SQLAlchemy model instances."""

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for col in self.__table__.columns:
            val = getattr(self, col.name)
            if isinstance(val, datetime):
                val = val.isoformat()
            result[col.name] = val
        return result

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)

    def restore(self) -> None:
        self.is_deleted = False
        self.deleted_at = None

    @property
    def is_active(self) -> bool:
        return not self.is_deleted

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={getattr(self, 'id', 'N/A')}>"
