"""Base classes for the Trust platform.

NOTE: Uses DateTime-based soft-delete pattern (is_deleted is DateTime, nullable).
This differs from the canonical Boolean-based SoftDeleteMixin in shared.models.
Consolidation requires schema migration — deferred to Phase 3.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_base

from app._compat import UTC
from app.orm_topology import SHARED_METADATA

TrustBase = declarative_base(metadata=SHARED_METADATA)


class TrustTimestampMixin:
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class TrustSoftDeleteMixin:
    is_deleted = Column(DateTime(timezone=True), nullable=True, default=None)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def soft_delete(self) -> None:
        self.is_deleted = datetime.now(UTC)
        self.deleted_at = datetime.now(UTC)

    def restore(self) -> None:
        self.is_deleted = None
        self.deleted_at = None

    @property
    def is_active(self) -> bool:
        return self.is_deleted is None


class TrustBaseEntity(TrustTimestampMixin, TrustSoftDeleteMixin, TrustBase):
    __abstract__ = True

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for col in self.__table__.columns:
            val = getattr(self, col.name)
            if isinstance(val, datetime):
                val = val.isoformat()
            result[col.name] = val
        return result

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={getattr(self, 'id', 'N/A')}>"
