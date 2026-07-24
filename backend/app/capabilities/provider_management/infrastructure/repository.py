from __future__ import annotations

from sqlalchemy import select

from app.capabilities.provider_management.domain.entities import Provider_management
from app.capabilities.provider_management.domain.repository import (
    Provider_managementRepository,
)


class SQLAlchemyProvider_managementRepository(Provider_managementRepository):
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get(self, id: str) -> Provider_management | None:
        async with self._session_factory() as session:
            return await session.get(Provider_management, id)

    async def list(self, skip: int = 0, limit: int = 100) -> list[Provider_management]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(Provider_management).offset(skip).limit(limit),
            )
            return list(result.scalars().all())

    async def create(self, entity: Provider_management) -> Provider_management:
        async with self._session_factory() as session:
            session.add(entity)
            await session.commit()
            return entity

    async def update(self, entity: Provider_management) -> Provider_management:
        async with self._session_factory() as session:
            session.add(entity)
            await session.commit()
            return entity

    async def delete(self, id: str) -> bool:
        async with self._session_factory() as session:
            entity = await session.get(Provider_management, id)
            if not entity:
                return False
            await session.delete(entity)
            await session.commit()
            return True

    async def count(self) -> int:
        async with self._session_factory() as session:
            result = await session.execute(select(Provider_management))
            return len(result.scalars().all())
