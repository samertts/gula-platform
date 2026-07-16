from __future__ import annotations

from app.capabilities.document_management.domain.entities import Document_management
from app.capabilities.document_management.domain.repository import Document_managementRepository


class Document_managementService:
    def __init__(self, repository: Document_managementRepository):
        self._repository = repository

    async def get(self, id: str) -> Document_management | None:
        return await self._repository.get(id)

    async def list(self, skip: int = 0, limit: int = 100) -> list[Document_management]:
        return await self._repository.list(skip=skip, limit=limit)

    async def create(self, data: Document_management) -> Document_management:
        return await self._repository.create(data)

    async def update(self, data: Document_management) -> Document_management:
        return await self._repository.update(data)

    async def delete(self, id: str) -> bool:
        return await self._repository.delete(id)
