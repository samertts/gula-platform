from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session


class SyncSessionAsyncFacade:
    """Small compatibility boundary for async NIAM services over the sync app DB.

    The legacy application owns a synchronous SQLAlchemy engine. The identity
    services are async-shaped, so the gateway uses this explicit boundary rather
    than duplicating authorization or audit logic. Gateway endpoints remain sync
    routes, keeping blocking DB work out of the event loop.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    async def execute(self, statement: Any):
        return self._session.execute(statement)

    async def scalar(self, statement: Any):
        return self._session.scalar(statement)

    async def get(self, entity: Any, identity: Any):
        return self._session.get(entity, identity)

    def add(self, instance: Any) -> None:
        self._session.add(instance)

    async def flush(self) -> None:
        self._session.flush()
