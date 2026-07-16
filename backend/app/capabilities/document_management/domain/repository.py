from __future__ import annotations

from .entities import Document_management


class Document_managementRepository:
    async def get(self, id: str) -> Document_management | None:
        raise NotImplementedError

    async def list(self, skip: int = 0, limit: int = 100) -> list[Document_management]:
        raise NotImplementedError

    async def create(self, entity: Document_management) -> Document_management:
        raise NotImplementedError

    async def update(self, entity: Document_management) -> Document_management:
        raise NotImplementedError

    async def delete(self, id: str) -> bool:
        raise NotImplementedError

    async def count(self) -> int:
        raise NotImplementedError
