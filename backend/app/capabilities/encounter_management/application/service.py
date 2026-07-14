from __future__ import annotations

from typing import Optional


class Encounter_managementService:
    def __init__(self, repository: Encounter_managementRepository):
        self._repository = repository

    async def get(self, id: str) -> Optional[Encounter_management]:
        return await self._repository.get(id)

    async def list(self, skip: int = 0, limit: int = 100) -> list[Encounter_management]:
        return await self._repository.list(skip=skip, limit=limit)

    async def create(self, data: Encounter_management) -> Encounter_management:
        return await self._repository.create(data)

    async def update(self, data: Encounter_management) -> Encounter_management:
        return await self._repository.update(data)

    async def delete(self, id: str) -> bool:
        return await self._repository.delete(id)
