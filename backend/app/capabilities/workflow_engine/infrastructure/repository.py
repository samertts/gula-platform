from __future__ import annotations

from sqlalchemy import select

from app.capabilities.workflow_engine.domain.entities import Workflow_engine
from app.capabilities.workflow_engine.domain.repository import Workflow_engineRepository


class SQLAlchemyWorkflow_engineRepository(Workflow_engineRepository):
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get(self, id: str) -> Workflow_engine | None:
        async with self._session_factory() as session:
            return await session.get(Workflow_engine, id)

    async def list(self, skip: int = 0, limit: int = 100) -> list[Workflow_engine]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(Workflow_engine).offset(skip).limit(limit),
            )
            return list(result.scalars().all())

    async def create(self, entity: Workflow_engine) -> Workflow_engine:
        async with self._session_factory() as session:
            session.add(entity)
            await session.commit()
            return entity

    async def update(self, entity: Workflow_engine) -> Workflow_engine:
        async with self._session_factory() as session:
            session.add(entity)
            await session.commit()
            return entity

    async def delete(self, id: str) -> bool:
        async with self._session_factory() as session:
            entity = await session.get(Workflow_engine, id)
            if not entity:
                return False
            await session.delete(entity)
            await session.commit()
            return True

    async def count(self) -> int:
        async with self._session_factory() as session:
            result = await session.execute(select(Workflow_engine))
            return len(result.scalars().all())
