import uuid

from sqlalchemy import JSON, Column, String
from sqlalchemy.orm import declarative_base

from shared.models import AuditMixin, OptimisticLockMixin, SoftDeleteMixin, TenantMixin

NHDWBase = declarative_base()


def _nhdw_ulid() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:26]


class NHDWBaseEntity(NHDWBase, AuditMixin, SoftDeleteMixin, TenantMixin, OptimisticLockMixin):
    __abstract__ = True

    id = Column(String(26), primary_key=True, default=_nhdw_ulid)
    fhir_id = Column(String(64), nullable=True, index=True)
    fhir_resource_type = Column(String(32), nullable=True)
    extension = Column(JSON, nullable=True)
