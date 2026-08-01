from __future__ import annotations

import uuid

from sqlalchemy import Column, Integer, String

from app.national.base import NationalBase
from shared.models import BaseEntityMixin, OptimisticLockMixin, SoftDeleteMixin, TimestampMixin

# EHR entities share the NationalBase metadata: every EHR foreign key targets
# national_* tables (patients, practitioners, encounters, facilities, ...),
# and SQLAlchemy resolves foreign keys only within the parent table's own
# metadata.  A separate declarative_base() here made those FKs unresolvable
# (NoReferencedTableError) at flush time — breaking every EHR insert.
EHRBase = NationalBase

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
