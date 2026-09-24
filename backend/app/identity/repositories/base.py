from typing import TypeVar

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.identity.base import IdentityBaseEntity

T = TypeVar("T", bound=IdentityBaseEntity)


class IdentityRepositoryBase[T: IdentityBaseEntity]:

    model_class: type[T]

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, entity: T) -> T:
        self.session.add(entity)
        self.session.flush()
        return entity

    def get_by_id(self, entity_id: str) -> T | None:
        stmt = select(self.model_class).where(
            self.model_class.id == entity_id,
            self.model_class.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_uuid(self, uuid: str) -> T | None:
        stmt = select(self.model_class).where(
            self.model_class.uuid == uuid,
            self.model_class.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def soft_delete(self, entity_id: str) -> None:
        stmt = (
            update(self.model_class)
            .where(self.model_class.id == entity_id)
            .values(is_active=False)
        )
        self.session.execute(stmt)
        self.session.flush()

    def hard_delete(self, entity_id: str) -> None:
        stmt = delete(self.model_class).where(self.model_class.id == entity_id)
        self.session.execute(stmt)
        self.session.flush()

    def list_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.is_active.is_(True))
            .offset(skip)
            .limit(limit)
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def count(self) -> int:
        # `from sqlalchemy.func import count` was written here and raises
        # ModuleNotFoundError: sqlalchemy.func is an attribute of the package,
        # not a module. It was invisible while this layer could not execute
        # (NR-044) and surfaced the moment it could.
        from sqlalchemy import func

        stmt = select(func.count()).select_from(self.model_class).where(
            self.model_class.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        return result.scalar() or 0
