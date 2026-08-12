from __future__ import annotations

from .entities import Encounter_management


class Encounter_managementRepository:
    async def get(self, id: str) -> Encounter_management | None:
        raise NotImplementedError

    async def list(self, skip: int = 0, limit: int = 100) -> list[Encounter_management]:
        raise NotImplementedError

    async def create(self, entity: Encounter_management) -> Encounter_management:
        raise NotImplementedError

    async def update(self, entity: Encounter_management) -> Encounter_management:
        raise NotImplementedError

    async def delete(self, id: str) -> bool:
        raise NotImplementedError

    async def count(self) -> int:
        raise NotImplementedError
