from sqlalchemy import Boolean, Column
from sqlalchemy.orm import declarative_base

from app.orm_topology import SHARED_METADATA
from shared.models import AuditMixin, OptimisticLockMixin, SoftDeleteMixin, TenantMixin

#: NR-086 -- constructed against the one shared namespace so this base's
#: cross-base foreign keys resolve. See app/orm_topology.py.
HospitalBase = declarative_base(metadata=SHARED_METADATA)


class HospitalBaseEntity(HospitalBase, AuditMixin, SoftDeleteMixin, TenantMixin, OptimisticLockMixin):
    __abstract__ = True

    is_active = Column(Boolean, default=True, nullable=False, index=True)
