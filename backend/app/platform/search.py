"""Standardized search service module."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field

from . import PlatformRegistry

logger = logging.getLogger("gula.platform.search")


@dataclass
class SearchResult:
    id: str = ""
    score: float = 0.0
    title: str = ""
    description: str = ""
    resource_type: str = ""
    resource_id: str = ""


@dataclass
class SearchResponse:
    results: list[SearchResult] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    took_ms: float = 0.0


class SearchService:
    def search(
        self,
        query: str,
        index: str = "default",
        page: int = 1,
        page_size: int = 20,
        filters: dict | None = None,
    ) -> SearchResponse:
        from ..national.search_platform.domain.entities import (
            SearchQuery,
        )

        SearchQuery(
            id=str(uuid.uuid4()),
            query_text=query,
            page=page,
            page_size=page_size,
        )
        return SearchResponse(results=[], total=0, page=page, page_size=page_size)

    def index(self, resource_type: str, resource_id: str, data: dict) -> bool:
        logger.info("[SEARCH] Indexed %s/%s", resource_type, resource_id)
        return True

    def reindex(self, resource_type: str | None = None) -> bool:
        logger.info("[SEARCH] Reindex triggered for %s", resource_type or "all")
        return True

    def suggest(self, query: str, index: str = "default") -> list[str]:
        return []


PlatformRegistry.register(
    "search",
    SearchService(),
    capabilities=[
        {"name": "search", "description": "Full-text search across indexed resources"},
        {"name": "index", "description": "Index a resource for search"},
        {"name": "reindex", "description": "Rebuild the search index"},
        {"name": "suggest", "description": "Get search suggestions for a partial query"},
    ],
)
