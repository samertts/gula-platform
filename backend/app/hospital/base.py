from sqlalchemy import Boolean, Column
from sqlalchemy.orm import declarative_base

from shared.models import AuditMixin, OptimisticLockMixin, SoftDeleteMixin, TenantMixin

HospitalBase = declarative_base()


class HospitalBaseEntity(HospitalBase, AuditMixin, SoftDeleteMixin, TenantMixin, OptimisticLockMixin):
    __abstract__ = True

    is_active = Column(Boolean, default=True, nullable=False, index=True)
