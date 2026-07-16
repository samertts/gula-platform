from __future__ import annotations

from app.capabilities.provider_management.domain.entities import Provider_management
from app.capabilities.provider_management.domain.repository import Provider_managementRepository


class Provider_managementService:
    def __init__(self, repository: Provider_managementRepository):
        self._repository = repository

    async def get(self, id: str) -> Provider_management | None:
        return await self._repository.get(id)

    async def list(self, skip: int = 0, limit: int = 100) -> list[Provider_management]:
        return await self._repository.list(skip=skip, limit=limit)

    async def create(self, data: Provider_management) -> Provider_management:
        return await self._repository.create(data)

    async def update(self, data: Provider_management) -> Provider_management:
        return await self._repository.update(data)

    async def delete(self, id: str) -> bool:
        return await self._repository.delete(id)
