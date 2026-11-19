from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import declarative_base

from app._compat import UTC
from app.models.base import OptimisticLockMixin, SoftDeleteMixin, TimestampMixin, serialize_columns

ClinicalBase = declarative_base()


def _ulid() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:26]


class BaseEntity(TimestampMixin, SoftDeleteMixin, OptimisticLockMixin, ClinicalBase):
    __abstract__ = True

    id = Column(String(26), primary_key=True, default=_ulid)
    fhir_id = Column(String(64), nullable=True, index=True)
    fhir_resource_type = Column(String(32), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return serialize_columns(self)

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
        return f"<{self.__class__.__name__} id={self.id}>"
