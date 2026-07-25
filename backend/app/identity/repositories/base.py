from typing import TypeVar

from sqlalchemy import delete, select, update

T = TypeVar("T", bound="IdentityBaseEntity")
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.base import IdentityBaseEntity


class IdentityRepositoryBase[T: "IdentityBaseEntity"]:
    model_class: type[T]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get_by_id(self, entity_id: str) -> T | None:
        stmt = select(self.model_class).where(
            self.model_class.id == entity_id,
            self.model_class.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_uuid(self, uuid: str) -> T | None:
        stmt = select(self.model_class).where(
            self.model_class.uuid == uuid,
            self.model_class.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def soft_delete(self, entity_id: str) -> None:
        stmt = (
            update(self.model_class).where(self.model_class.id == entity_id).values(is_active=False)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def hard_delete(self, entity_id: str) -> None:
        stmt = delete(self.model_class).where(self.model_class.id == entity_id)
        await self.session.execute(stmt)
        await self.session.flush()

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.is_active.is_(True))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self) -> int:
        from sqlalchemy.func import count

        stmt = (
            select(count())
            .select_from(self.model_class)
            .where(
                self.model_class.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
