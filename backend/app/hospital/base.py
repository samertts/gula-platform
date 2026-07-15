from sqlalchemy import Boolean, Column, Integer

from shared.models import AuditMixin, OptimisticLockMixin, SoftDeleteMixin, TenantMixin, TimestampMixin

from ..database import Base


class HospitalBaseEntity(Base, AuditMixin, SoftDeleteMixin, TenantMixin, OptimisticLockMixin):
    __abstract__ = True

    is_active = Column(Boolean, default=True, nullable=False, index=True)
