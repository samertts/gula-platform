from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from sqlalchemy.orm import Session

from app._compat import UTC
from app.services.audit_service import log_action, normalize_resource_id

T = TypeVar("T")


class OptimisticLockError(Exception):
    pass


class GovernanceRepository(Generic[T]):
    def __init__(self, db: Session, model_cls: type[T], audit_resource: str = "",
                 actor_user_id: int | None = None, actor_lab_id: int | None = None):
        self._db = db
        self._model = model_cls
        self._audit_resource = audit_resource or model_cls.__tablename__
        # NR-109. The actor, so an audit row can name who acted. The class had
        # no actor at all, which is why every row it wrote said "system".
        # Optional because no caller supplies one yet; a NULL actor is visibly
        # unattributed, which is honest, where "system" was a false claim.
        self._actor_user_id = actor_user_id
        self._actor_lab_id = actor_lab_id

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
                    f"version {current} != expected {expected_version}",
                )
            entity.version = current + 1 if current is not None else 1
        self._write_audit("update", str(getattr(entity, "id", "")))
        return entity

    def delete(self, entity: T, soft: bool = True) -> None:
        if soft and hasattr(entity, "is_deleted"):
            if isinstance(getattr(entity, "is_deleted", None), bool):
                entity.is_deleted = True
            entity.deleted_at = datetime.now(UTC)
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
        """Record the mutation in the canonical hash-chained audit log (NR-109).

        This wrote a HealthNumberAudit row instead, and it was wrong four ways
        at once, which is why it survived: it satisfied any reviewer and any
        detector looking for "does this package audit".

        1. WRONG TABLE, AND THE TABLE DOES NOT EXIST. gov_health_number_audit
           is mapped by the ORM and built by no migration. Proven by execution
           against PostgreSQL at 20260916_0001: adding a break-glass record and
           flushing raises
               ProgrammingError: relation "gov_health_number_audit" does not exist
           while gov_break_glass_accesses, gov_identity_records, gov_qr_codes,
           gov_recovery_requests, gov_guardians and gov_merge_proposals are all
           built. So EVERY create, update and delete through this class failed
           at flush -- including emergency break-glass access grants.
        2. WRONG RESOURCE. It put the entity's id in `health_number`, so a
           break-glass grant, an identity merge and a guardian record were all
           recorded as health-number events. Anyone querying a health number's
           history would have got them back, indistinguishable from real ones.
        3. WRONG ACTOR. changed_by was the literal "system" for every caller.
        4. NOT TAMPER-EVIDENT. It is not the SHA-256 chained audit_logs, so it
           evidenced nothing even where it did write.

        `audit_resource` was already being supplied correctly by the
        subclasses -- BreakGlassAccessRepository passes "gov_break_glass" --
        and then ignored. It is used now.
        """
        log_action(
            self._db,
            action=f"governance.{self._audit_resource}.{action}",
            resource_type=self._audit_resource,
            resource_id=normalize_resource_id(resource_id),
            user_id=self._actor_user_id,
            lab_id=self._actor_lab_id,
            details={"resource_id": str(resource_id), "entity": self._model.__name__},
        )
