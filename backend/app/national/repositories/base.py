from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeVar

T = TypeVar("T")


class Repository[T](ABC):
    @abstractmethod
    async def get(self, id: str) -> T | None: ...

    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100, **filters: Any) -> list[T]: ...

    @abstractmethod
    async def create(self, entity: T) -> T: ...

    @abstractmethod
    async def update(self, entity: T) -> T: ...

    @abstractmethod
    async def delete(self, id: str, soft: bool = True) -> None: ...

    @abstractmethod
    async def count(self, **filters: Any) -> int: ...
