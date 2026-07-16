from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, String

from app._compat import UTC
from app.database import Base
from shared.models import AuditMixin, OptimisticLockMixin, SoftDeleteMixin, TenantMixin


def _ulid() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:26]


class NursingBaseEntity(TenantMixin, AuditMixin, SoftDeleteMixin, OptimisticLockMixin, Base):
    __abstract__ = True

    id = Column(String(26), primary_key=True, default=_ulid)
    fhir_extension = Column("fhir_extension", JSON, nullable=True)

    def to_dict(self) -> dict[str, Any]:
        result = {}
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
        return f"<{self.__class__.__name__} id={self.id}>"
