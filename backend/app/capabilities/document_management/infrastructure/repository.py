from __future__ import annotations

from sqlalchemy import select

from app.capabilities.document_management.domain.entities import Document_management
from app.capabilities.document_management.domain.repository import (
    Document_managementRepository,
)


class SQLAlchemyDocument_managementRepository(Document_managementRepository):
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get(self, id: str) -> Document_management | None:
        async with self._session_factory() as session:
            return await session.get(Document_management, id)

    async def list(self, skip: int = 0, limit: int = 100) -> list[Document_management]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(Document_management).offset(skip).limit(limit)
            )
            return list(result.scalars().all())

    async def create(self, entity: Document_management) -> Document_management:
        async with self._session_factory() as session:
            session.add(entity)
            await session.commit()
            return entity

    async def update(self, entity: Document_management) -> Document_management:
        async with self._session_factory() as session:
            session.add(entity)
            await session.commit()
            return entity

    async def delete(self, id: str) -> bool:
        async with self._session_factory() as session:
            entity = await session.get(Document_management, id)
            if not entity:
                return False
            await session.delete(entity)
            await session.commit()
            return True

    async def count(self) -> int:
        async with self._session_factory() as session:
            result = await session.execute(select(Document_management))
            return len(result.scalars().all())
