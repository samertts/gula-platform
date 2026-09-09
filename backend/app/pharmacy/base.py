from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

from app._compat import UTC
from app.models.base import (
    AuditMixin,
    OptimisticLockMixin,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)

PharmacyBase = declarative_base()


def _ulid() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:26]


class BaseEntity(TimestampMixin, SoftDeleteMixin, OptimisticLockMixin, PharmacyBase):
    """LEGACY Generation B base — do not use for new or reconciled entities.

    The ``String(26)`` primary key below is the P0-2 identity defect: every
    physical Pharmacy table keys on ``INTEGER``, so a model inheriting this
    base cannot execute against the migration-built schema.  Seventeen tables
    still inherit it, down from twenty-three, and are reconciled milestone by
    milestone (M2 clinical rules and M3 sales/substitution are done; M4 covers
    inventory, batches, prescriptions and dispensing); this class is deleted
    once the last one moves off it.

    The two ``fhir_*`` columns are part of the same defect: they are declared
    here for every subclass, but only seven Pharmacy tables actually have them,
    so an ORM ``INSERT`` against any of the others fails with
    ``UndefinedColumn`` before a row is created.

    Reconciled entities inherit :class:`GlobalCatalogEntity` or
    :class:`TenantScopedEntity` instead.
    """

    __abstract__ = True

    id = Column(String(26), primary_key=True, default=_ulid)
    fhir_id = Column(String(64), nullable=True, index=True)
    fhir_resource_type = Column(String(32), nullable=True)

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


class TenantEntity(TenantMixin, BaseEntity):
    __abstract__ = True


class AuditEntity(AuditMixin, BaseEntity):
    __abstract__ = True


class CanonicalEntity(SoftDeleteMixin, OptimisticLockMixin, AuditMixin, PharmacyBase):
    """Canonical Pharmacy identity: the internal key is the relational one.

    ``id`` is ``INTEGER`` and database-assigned, matching every physical
    Pharmacy primary key. It is an internal key and is never the public
    identity of an entity (CANONICAL_DRUG_CONTRACT §3); an entity that has a
    public identity declares it as its own column.

    Deliberately absent, unlike the legacy Generation B base:

    * no ``String(26)`` ``_ulid()`` key,
    * no ``fhir_id`` / ``fhir_resource_type`` — those are separate external
      identifiers (contract §11) and are declared only where the physical
      table actually has them,
    * no tenant column — tenancy is declared per entity, never inherited,
      so a global table cannot silently acquire one.
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)

    def restore(self) -> None:
        self.is_deleted = False
        # deleted_at is contributed by the untyped SoftDeleteMixin, so mypy
        # reads it as a bare datetime and rejects clearing it.
        self.deleted_at = None  # type: ignore[assignment]

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for col in self.__table__.columns:
            val = getattr(self, col.name)
            if isinstance(val, datetime):
                val = val.isoformat()
            result[col.name] = val
        return result

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"


class TenantScopedEntity(CanonicalEntity):
    """A canonical entity that genuinely belongs to one tenant.

    Unlike the legacy ``TenantAuditEntity``, tenancy here is a deliberate
    declaration rather than something inherited by every model. ``lab_id`` is
    declared by the subclass so it can carry the foreign key its physical
    table actually has (contract §6).
    """

    __abstract__ = True


class GlobalCatalogEntity(CanonicalEntity):
    """A globally-scoped reference entity: national data, never tenant-scoped.

    Contract §6: an entity is either global or tenant-scoped, never both.
    Adding a tenant column to a subclass of this base is a contract
    violation, not a feature.
    """

    __abstract__ = True


class TenantAuditEntity(TenantMixin, AuditMixin, BaseEntity):
    __abstract__ = True
