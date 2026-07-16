from __future__ import annotations

from app.capabilities.workflow_engine.domain.entities import Workflow_engine
from app.capabilities.workflow_engine.domain.repository import Workflow_engineRepository


class Workflow_engineService:
    def __init__(self, repository: Workflow_engineRepository):
        self._repository = repository

    async def get(self, id: str) -> Workflow_engine | None:
        return await self._repository.get(id)

    async def list(self, skip: int = 0, limit: int = 100) -> list[Workflow_engine]:
        return await self._repository.list(skip=skip, limit=limit)

    async def create(self, data: Workflow_engine) -> Workflow_engine:
        return await self._repository.create(data)

    async def update(self, data: Workflow_engine) -> Workflow_engine:
        return await self._repository.update(data)

    async def delete(self, id: str) -> bool:
        return await self._repository.delete(id)
