from __future__ import annotations

from typing import Any
from uuid import UUID

from .interfaces import SemanticQuery, SemanticSearchResult


class InfrastructureSemanticSearchService:
    def __init__(self, doc_repo: Any) -> None:
        self._doc_repo = doc_repo

    async def search(self, query: SemanticQuery) -> list[SemanticSearchResult]:
        docs, _ = await self._doc_repo.search(query.query_text, limit=query.limit)
        return [
            SemanticSearchResult(document_id=d.id, score=1.0, text_snippet=d.filename) for d in docs
        ]

    async def hybrid_search(
        self, query_text: str, query_vector: list[float] | None = None,
    ) -> list[SemanticSearchResult]:
        docs, _ = await self._doc_repo.search(query_text, limit=20)
        return [
            SemanticSearchResult(document_id=d.id, score=1.0, text_snippet=d.filename) for d in docs
        ]

    async def arabic_search(self, query: str) -> list[SemanticSearchResult]:
        return await self.hybrid_search(query)

    async def natural_language_query(self, query: str) -> list[SemanticSearchResult]:
        return await self.hybrid_search(query)

    async def similar_documents(
        self, document_id: UUID, limit: int = 10,
    ) -> list[SemanticSearchResult]:
        return []

    async def search_by_entity(self, entity_type: Any, value: str) -> list[SemanticSearchResult]:
        return []

    async def suggest_queries(self, partial: str) -> list[str]:
        return [f"{partial}_1", f"{partial}_2"]
