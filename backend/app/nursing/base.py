"""Nursing declarative base, reconciled to the schema Alembic builds.

The previous base keyed every Nursing entity on ``String(26)`` with a ``_ulid()``
default, while migration ``20260716_0002`` creates ``INTEGER`` serial primary
keys on all fifteen tables and every foreign key into ``labs``, ``lab_users``,
``patients``, ``nhdw_admissions`` and ``nursing_shifts`` is ``INTEGER`` to match.
The result was a domain that could not execute a plain ``SELECT`` (NR-026).

The physical schema is authoritative here, and it is internally consistent: the
identity strategy it already implements is an internal ``INTEGER`` key plus a
separate nullable ``sync_id VARCHAR(26)`` carried by all fifteen tables. That
answers the identity question without inventing a new scheme inside Nursing —
the internal key stays internal, and ``sync_id`` is the identifier that travels.

The tenant, audit, soft-delete and optimistic-lock mixins were already correct
and are unchanged; only the primary key and the FHIR/sync columns moved.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

from app._compat import UTC
from shared.models import AuditMixin, OptimisticLockMixin, SoftDeleteMixin, TenantMixin

NursingBase = declarative_base()


class NursingBaseEntity(TenantMixin, AuditMixin, SoftDeleteMixin, OptimisticLockMixin, NursingBase):
    """Columns every ``nursing_*`` table carries, and only those.

    ``sync_id`` is the domain's portable identifier: nullable, 26 characters,
    present on all fifteen tables. It is deliberately *not* the primary key —
    the physical key is a serial ``INTEGER`` and every inbound foreign key
    matches it.
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    sync_id = Column(String(26), nullable=True, unique=True)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for col in self.__table__.columns:
            val = getattr(self, col.name)
            result[col.name] = val.isoformat() if isinstance(val, datetime) else val
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


class NursingFHIREntity(NursingBaseEntity):
    """The twelve tables that also carry FHIR correlation columns.

    ``nursing_shifts``, ``nursing_delegations`` and ``nursing_shift_handovers``
    do not have them: those are workforce records rather than clinical
    resources, so they extend ``NursingBaseEntity`` directly.
    """

    __abstract__ = True

    fhir_id = Column(String(64), nullable=True)
    fhir_resource_type = Column(String(32), nullable=True)
