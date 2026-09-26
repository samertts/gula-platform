from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, String
from sqlalchemy.orm import declarative_base

from app._compat import UTC
from app.orm_topology import SHARED_METADATA
from shared.models import AuditMixin, OptimisticLockMixin, SoftDeleteMixin, TenantMixin

#: NR-086 -- constructed against the one shared namespace so this base's
#: cross-base foreign keys resolve. See app/orm_topology.py.
NursingBase = declarative_base(metadata=SHARED_METADATA)


def _ulid() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:26]


class NursingBaseEntity(TenantMixin, AuditMixin, SoftDeleteMixin, OptimisticLockMixin, NursingBase):
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
