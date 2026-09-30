from __future__ import annotations

from collections.abc import Callable, Container
from datetime import date, datetime
from typing import Any

from backend.app._compat import UTC
from sqlalchemy import Boolean, Column, DateTime, Integer
from sqlalchemy import inspect as sa_inspect


def serialize_columns(
    instance: Any,
    *,
    redact: Callable[[str], bool] | None = None,
    exclude: Container[str] = (),
    isoformat_dates: bool = False,
) -> dict[str, Any]:
    """Serialise a mapped instance's columns, keyed by **physical column name**.

    Resolving the value through the mapper rather than through ``col.name`` is not a
    stylistic choice. A declarative class already owns the attribute ``metadata`` —
    SQLAlchemy puts the base's :class:`~sqlalchemy.MetaData` registry there — so a
    model that needs a *column* called ``metadata`` must map it under a different
    Python name (``metadata_``, or ``extra_metadata``). ``getattr(self, col.name)``
    then returns the registry instead of the column value, and any JSON encoder walks
    that object graph until the stack is exhausted.

    The output key stays the physical column name, which is what every base has always
    emitted and what clients already consume. Only the lookup changes.

    Neither ``col.name`` nor ``col.key`` is the mapped attribute: for
    ``metadata_ = Column("metadata", ...)`` both are ``"metadata"``, and only the
    mapper knows the value lives under ``metadata_``. Route helpers that walked
    ``col.key`` were affected exactly as the bases were.

    ``redact`` receives the physical column name and, when it returns True, the value
    is replaced by ``"[REDACTED]"`` and never read into the payload. ``exclude`` drops
    columns from the payload entirely. ``isoformat_dates`` additionally renders plain
    ``date`` values as ISO strings, which the route helpers did and the bases did not;
    each caller keeps its own behaviour.
    """
    attr_by_column: dict[str, str] = {}
    for attr_key, column in sa_inspect(type(instance)).columns.items():
        attr_by_column.setdefault(column.name, attr_key)

    result: dict[str, Any] = {}
    for col in instance.__table__.columns:
        if col.name in exclude:
            continue
        if redact is not None and redact(col.name):
            result[col.name] = "[REDACTED]"
            continue
        attr_key = attr_by_column.get(col.name)
        # A column absent from the mapper has no value on the instance. Reading it by
        # its physical name is exactly the bug above, so report it as unset instead.
        val = getattr(instance, attr_key) if attr_key is not None else None
        if isinstance(val, datetime) or (isoformat_dates and isinstance(val, date)):
            val = val.isoformat()
        result[col.name] = val
    return result


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class AuditMixin(TimestampMixin):
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)


class TenantMixin:
    lab_id = Column(Integer, nullable=False, index=True)


class OptimisticLockMixin:
    version = Column(Integer, default=1, nullable=False)


class BaseEntityMixin:
    """Shared utility methods for SQLAlchemy model instances."""

    def to_dict(self) -> dict[str, Any]:
        return serialize_columns(self)

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
        return f"<{self.__class__.__name__} id={getattr(self, 'id', 'N/A')}>"
