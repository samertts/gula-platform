"""Base model imports — canonical shared.model mixins.

All SQLAlchemy models use shared mixins for Timestamp, SoftDelete,
Audit, Tenant, and OptimisticLock patterns.
"""

from shared.models import (
    AuditMixin,
    BaseEntityMixin,
    OptimisticLockMixin,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
    serialize_columns,
)

from ..database import Base

__all__ = [
    "AuditMixin",
    "Base",
    "BaseEntityMixin",
    "OptimisticLockMixin",
    "SoftDeleteMixin",
    "TenantMixin",
    "TimestampMixin",
    "serialize_columns",
]
