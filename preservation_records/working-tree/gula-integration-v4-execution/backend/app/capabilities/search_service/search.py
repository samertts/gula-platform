from __future__ import annotations

from typing import Any

from .exceptions import IndexingError, SearchError


class DefaultSearchService:
    def __init__(self, indexer: Any) -> None:
        self._indexer = indexer

    async def index_document(
        self,
        document: Any,
        text: str,
        entities: list[Any],
    ) -> None:
        try:
            await self._indexer.index_document(document, text, entities)
        except Exception as exc:
            raise IndexingError(f"Search indexing failed: {exc}") from exc

    async def search(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        try:
            return await self._indexer.search(query, filters)
        except Exception as exc:
            raise SearchError(f"Search failed: {exc}") from exc

    async def advanced_search(
        self,
        query: str,
        document_type: Any | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        patient_id: Any | None = None,
        doctor_name: str | None = None,
        lab_name: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {"limit": limit}
        if document_type:
            filters["category"] = str(document_type)
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        if patient_id:
            filters["patient_id"] = str(patient_id)
        if doctor_name:
            filters["doctor_name"] = doctor_name
        if lab_name:
            filters["lab_name"] = lab_name
        try:
            return await self._indexer.search(query, filters)
        except Exception as exc:
            raise SearchError(f"Advanced search failed: {exc}") from exc
