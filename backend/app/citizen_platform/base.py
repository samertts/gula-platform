from __future__ import annotations

import uuid

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, declared_attr

from shared.models import BaseEntityMixin, OptimisticLockMixin, SoftDeleteMixin, TimestampMixin

CitizenPlatformBase = declarative_base()


def _ulid() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:26]


class CitizenAuditMixin:
    created_by = Column(String(64), nullable=True)
    updated_by = Column(String(64), nullable=True)


class CitizenEntity(
    TimestampMixin, SoftDeleteMixin, BaseEntityMixin, OptimisticLockMixin, CitizenPlatformBase,
):
    __abstract__ = True

    id = Column(String(26), primary_key=True, default=_ulid)
    fhir_id = Column(String(64), nullable=True, index=True)
    fhir_resource_type = Column(String(32), nullable=True)
    version = Column(Integer, default=1, nullable=False)


class CitizenAuditEntity(CitizenAuditMixin, CitizenEntity):
    __abstract__ = True


class CitizenTenantAuditEntity(CitizenAuditMixin, CitizenEntity):
    __abstract__ = True

    @declared_attr
    def lab_id(self):
        return Column(String(26), nullable=True, index=True)
