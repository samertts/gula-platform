from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.national.search_platform.domain.entities import SavedSearch, SearchResult


class SavedSearchRepository(ABC):
    @abstractmethod
    async def save(self, saved: SavedSearch) -> SavedSearch: ...

    @abstractmethod
    async def get(self, search_id: str) -> SavedSearch | None: ...

    @abstractmethod
    async def list(
        self,
        created_by: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[SavedSearch]: ...

    @abstractmethod
    async def delete(self, search_id: str) -> None: ...

    @abstractmethod
    async def find_scheduled(self) -> list[SavedSearch]: ...


class SearchResultRepository(ABC):
    @abstractmethod
    async def save_result(self, result: SearchResult) -> SearchResult: ...

    @abstractmethod
    async def save_results(self, results: list[SearchResult]) -> list[SearchResult]: ...

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]: ...
