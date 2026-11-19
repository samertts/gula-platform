from __future__ import annotations

import uuid

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

from app.orm_topology import SHARED_METADATA
from shared.models import BaseEntityMixin, OptimisticLockMixin, SoftDeleteMixin, TimestampMixin

#: NR-086 -- constructed against the one shared namespace so this base's
#: cross-base foreign keys resolve. See app/orm_topology.py.
EHRBase = declarative_base(metadata=SHARED_METADATA)

# Backward-compatible aliases for the old EHR-prefixed mixin names.
# New code should import TimestampMixin, SoftDeleteMixin from shared.models.
EHRTimestampMixin = TimestampMixin
EHRSoftDeleteMixin = SoftDeleteMixin


def _ulid() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:26]


class EHRBaseEntity(TimestampMixin, SoftDeleteMixin, BaseEntityMixin, OptimisticLockMixin, EHRBase):
    __abstract__ = True

    id = Column(String(26), primary_key=True, default=_ulid)
    fhir_id = Column(String(64), nullable=True, index=True)
    fhir_resource_type = Column(String(32), nullable=True)
    version = Column(Integer, default=1, nullable=False)
