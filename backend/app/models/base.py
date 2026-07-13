"""Base model imports — canonical shared.model mixins.

All SQLAlchemy models use shared mixins for Timestamp, SoftDelete,
Audit, Tenant, and OptimisticLock patterns.
"""

from shared.models import (
    AuditMixin,
    OptimisticLockMixin,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)

from ..database import Base

__all__ = [
    "AuditMixin",
    "Base",
    "OptimisticLockMixin",
    "SoftDeleteMixin",
    "TenantMixin",
    "TimestampMixin",
]
