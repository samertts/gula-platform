from __future__ import annotations

from typing import Optional

from backend.app.capabilities.encounter_management.domain.entities import Encounter_management
from backend.app.capabilities.encounter_management.domain.repository import Encounter_managementRepository


class SQLAlchemyEncounter_managementRepository(Encounter_managementRepository):
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get(self, id: str) -> Optional[Encounter_management]:
        async with self._session_factory() as session:
            return await session.get(Encounter_management, id)

    async def list(self, skip: int = 0, limit: int = 100) -> list[Encounter_management]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(Encounter_management).offset(skip).limit(limit)
            )
            return list(result.scalars().all())

    async def create(self, entity: Encounter_management) -> Encounter_management:
        async with self._session_factory() as session:
            session.add(entity)
            await session.commit()
            return entity

    async def update(self, entity: Encounter_management) -> Encounter_management:
        async with self._session_factory() as session:
            session.add(entity)
            await session.commit()
            return entity

    async def delete(self, id: str) -> bool:
        async with self._session_factory() as session:
            entity = await session.get(Encounter_management, id)
            if not entity:
                return False
            await session.delete(entity)
            await session.commit()
            return True

    async def count(self) -> int:
        async with self._session_factory() as session:
            result = await session.execute(select(Encounter_management))
            return len(result.scalars().all())
