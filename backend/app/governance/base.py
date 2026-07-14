from datetime import datetime
from typing import Any

from app._compat import UTC
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import declarative_base

GovernanceBase = declarative_base()


class GovernanceTimestampMixin:
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class GovernanceSoftDeleteMixin:
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


class GovernanceBaseEntity(GovernanceTimestampMixin, GovernanceBase):
    __abstract__ = True

    def to_dict(self) -> dict[str, Any]:
        result = {}
        for col in self.__table__.columns:
            val = getattr(self, col.name)
            if isinstance(val, datetime):
                val = val.isoformat()
            result[col.name] = val
        return result

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={getattr(self, 'id', 'N/A')}>"
