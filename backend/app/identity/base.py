from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import declarative_base

from app._compat import UTC
from app.orm_topology import SHARED_METADATA

IdentityBase = declarative_base(metadata=SHARED_METADATA)


def _ulid() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:26]


_SENSITIVE_SERIALIZATION_TERMS = frozenset(
    {
        "password",
        "token",
        "secret",
        "credential",
        "private_key",
        "encrypted",
        "lookup",
        "fingerprint",
    },
)


def _is_sensitive_column(name: str) -> bool:
    normalized = name.lower()
    return any(term in normalized for term in _SENSITIVE_SERIALIZATION_TERMS)


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
            if _is_sensitive_column(col.name):
                result[col.name] = "[REDACTED]"
                continue
            if isinstance(val, datetime):
                val = val.isoformat()
            result[col.name] = val
        return result

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"


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
