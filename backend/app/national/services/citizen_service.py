from __future__ import annotations

from typing import Any

from app.national.domain.citizen import Citizen
from app.national.exceptions import CitizenNotFoundError, DuplicateHealthNumberError
from app.national.repositories.citizen_repository import CitizenRepository
from shared.events import events


class CitizenService:
    def __init__(self, repo: CitizenRepository) -> None:
        self.repo = repo

    async def register_citizen(self, data: dict[str, Any]) -> Citizen:
        health_number = await self._generate_health_number()
        existing = await self.repo.get_by_health_number(health_number)
        if existing:
            raise DuplicateHealthNumberError(health_number)
        citizen = Citizen(**{k: v for k, v in data.items() if hasattr(Citizen, k)})
        citizen.health_number = health_number
        result = await self.repo.create(citizen)
        events.emit("national.citizen.created", {"citizen_id": result.id, **data})
        events.emit("national.health_number.assigned", {"citizen_id": result.id, "health_number": health_number})
        return result

    async def get_citizen(self, citizen_id: str) -> Citizen:
        citizen = await self.repo.get(citizen_id)
        if not citizen:
            raise CitizenNotFoundError(citizen_id)
        return citizen

    async def update_citizen(self, citizen_id: str, data: dict[str, Any]) -> Citizen:
        citizen = await self.get_citizen(citizen_id)
        for key, value in data.items():
            if hasattr(citizen, key) and value is not None:
                setattr(citizen, key, value)
        result = await self.repo.update(citizen)
        events.emit("national.citizen.updated", {"citizen_id": result.id, **data})
        return result

    async def search_citizens(self, query: str, skip: int = 0, limit: int = 20) -> list[Citizen]:
        return await self.repo.list(skip=skip, limit=limit)

    async def _generate_health_number(self) -> str:
        import random
        return f"IQ{random.randint(10000000, 99999999)}"
