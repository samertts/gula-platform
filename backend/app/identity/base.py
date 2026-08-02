from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, String, event
from sqlalchemy.orm import declarative_base

from app._compat import UTC

IdentityBase = declarative_base()


def _ulid() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:26]


class IdentityBaseEntity(IdentityBase):
    __abstract__ = True

    id = Column(String(26), primary_key=True, default=_ulid)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

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


@event.listens_for(IdentityBaseEntity, "before_insert", propagate=True)
def _ensure_identity_id(mapper, connection, target) -> None:
    """Normalize the ellipsis placeholder used by NIAM call sites.

    Many identity call sites construct entities with ``id=...`` (Ellipsis) as
    a placeholder for the ULID default. SQLAlchemy's column default only
    fires when the attribute is left unset, so the placeholder must be
    resolved here — otherwise psycopg2 fails with "can't adapt type
    'ellipsis'".
    """
    if target.id is Ellipsis or target.id is None:
        target.id = _ulid()


class IdentitySoftDeleteEntity(IdentityBaseEntity):
    __abstract__ = True

    is_deleted = Column("is_deleted", default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)

    def restore(self) -> None:
        self.is_deleted = False
        self.deleted_at = None
