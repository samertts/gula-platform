from datetime import datetime

from app._compat import UTC
from sqlalchemy import Boolean, Column, DateTime, Integer

from app.database import Base


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class DataPlatformBase:
    __abstract__ = True


class BaseEntity(TimestampMixin, SoftDeleteMixin, DataPlatformBase, Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)

    def restore(self) -> None:
        self.is_deleted = False
        self.deleted_at = None

    @property
    def is_active(self) -> bool:
        return not self.is_deleted
