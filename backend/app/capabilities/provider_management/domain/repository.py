from __future__ import annotations

from .entities import Provider_management


class Provider_managementRepository:
    async def get(self, id: str) -> Provider_management | None:
        raise NotImplementedError

    async def list(self, skip: int = 0, limit: int = 100) -> list[Provider_management]:
        raise NotImplementedError

    async def create(self, entity: Provider_management) -> Provider_management:
        raise NotImplementedError

    async def update(self, entity: Provider_management) -> Provider_management:
        raise NotImplementedError

    async def delete(self, id: str) -> bool:
        raise NotImplementedError

    async def count(self) -> int:
        raise NotImplementedError
