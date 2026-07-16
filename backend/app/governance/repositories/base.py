from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Type, TypeVar

from sqlalchemy import Column, Integer
from sqlalchemy.orm import Session

from app._compat import UTC
from app.governance.models.health_number import HealthNumberAudit

T = TypeVar("T")


class OptimisticLockError(Exception):
    pass


class GovernanceRepository(Generic[T]):
    def __init__(self, db: Session, model_cls: Type[T], audit_resource: str = ""):
        self._db = db
        self._model = model_cls
        self._audit_resource = audit_resource or model_cls.__tablename__

    def get(self, id: Any) -> T | None:
        return self._db.query(self._model).filter(self._model.id == id).first()

    def list(self, skip: int = 0, limit: int = 100, **filters: Any) -> list[T]:
        q = self._db.query(self._model)
        for k, v in filters.items():
            if hasattr(self._model, k) and v is not None:
                q = q.filter(getattr(self._model, k) == v)
        return q.offset(skip).limit(limit).all()

    def add(self, entity: T) -> T:
        self._db.add(entity)
        self._write_audit("create", str(getattr(entity, "id", "")))
        return entity

    def update(self, entity: T, expected_version: int | None = None) -> T:
        if expected_version is not None:
            current = getattr(entity, "version", None)
            if current is not None and current != expected_version:
                raise OptimisticLockError(
                    f"{self._model.__name__} id={getattr(entity, 'id', '?')} "
                    f"version {current} != expected {expected_version}"
                )
            setattr(entity, "version", current + 1 if current is not None else 1)
        self._write_audit("update", str(getattr(entity, "id", "")))
        return entity

    def delete(self, entity: T, soft: bool = True) -> None:
        if soft and hasattr(entity, "is_deleted"):
            if isinstance(getattr(entity, "is_deleted", None), bool):
                entity.is_deleted = True
            setattr(entity, "deleted_at", datetime.now(UTC))
        elif soft and hasattr(entity, "is_active"):
            entity.is_active = False
        else:
            self._db.delete(entity)
        self._write_audit("delete", str(getattr(entity, "id", "")))

    def count(self, **filters: Any) -> int:
        q = self._db.query(self._model)
        for k, v in filters.items():
            if hasattr(self._model, k) and v is not None:
                q = q.filter(getattr(self._model, k) == v)
        return q.count()

    def _write_audit(self, action: str, resource_id: str) -> None:
        audit = HealthNumberAudit(
            health_number=resource_id,
            event=action,
            changed_by="system",
        )
        self._db.add(audit)
