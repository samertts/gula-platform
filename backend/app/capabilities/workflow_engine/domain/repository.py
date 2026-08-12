from __future__ import annotations

from .entities import Workflow_engine


class Workflow_engineRepository:
    async def get(self, id: str) -> Workflow_engine | None:
        raise NotImplementedError

    async def list(self, skip: int = 0, limit: int = 100) -> list[Workflow_engine]:
        raise NotImplementedError

    async def create(self, entity: Workflow_engine) -> Workflow_engine:
        raise NotImplementedError

    async def update(self, entity: Workflow_engine) -> Workflow_engine:
        raise NotImplementedError

    async def delete(self, id: str) -> bool:
        raise NotImplementedError

    async def count(self) -> int:
        raise NotImplementedError
