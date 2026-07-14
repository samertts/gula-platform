from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from app._compat import UTC
from app.kernel.event_bus.bus import EventBus
from app.kernel.event_bus.events import Event
from app.national.search_platform.application.interfaces import IndexAdapter
from app.national.search_platform.domain.entities import (
    SavedSearch,
    SearchFacet,
    SearchFilter,
    SearchQuery,
    SearchResponse,
    SearchResult,
    SearchSuggestion,
)
from app.national.search_platform.domain.enums import (
    FilterOperator,
    SearchIndexType,
    SearchMode,
    SearchOperator,
    SortOrder,
)
from app.national.search_platform.domain.events import (
    DocumentIndexed,
    IndexRebuilt,
    SavedSearchCreated,
    SearchPerformed,
)
from app.national.search_platform.domain.repository import (
    SavedSearchRepository,
    SearchResultRepository,
)
from app.national.search_platform.exceptions import (
    IndexAdapterError,
    SavedSearchNotFoundError,
    SearchExecutionError,
)

logger = logging.getLogger("gula.national.search_platform")


class SearchPlatformService:

    def __init__(
        self,
        index_adapter: IndexAdapter,
        saved_search_repository: SavedSearchRepository,
        search_result_repository: SearchResultRepository,
        event_bus: EventBus,
    ) -> None:
        self.index_adapter = index_adapter
        self.saved_search_repository = saved_search_repository
        self.search_result_repository = search_result_repository
        self.event_bus = event_bus

    async def search(
        self,
        query_text: str,
        filters: list[dict[str, Any]] | None = None,
        index_types: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "",
        sort_order: str = "desc",
        mode: str = "exact",
        operator: str = "and",
    ) -> SearchResponse:
        start = time.monotonic()

        parsed_filters = []
        if filters:
            for f in filters:
                parsed_filters.append(SearchFilter(
                    field=f.get("field", ""),
                    operator=FilterOperator(f.get("operator", "eq")),
                    value=f.get("value"),
                ))

        search_query = SearchQuery(
            id=str(uuid.uuid4()),
            query_text=query_text,
            filters=parsed_filters,
            index_types=[SearchIndexType(t) for t in index_types] if index_types else list(SearchIndexType),
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=SortOrder(sort_order),
            mode=SearchMode(mode),
            operator=SearchOperator(operator),
        )

        try:
            results, total = await self.index_adapter.search(search_query)
        except Exception as exc:
            raise SearchExecutionError(str(exc))

        suggestions = await self.index_adapter.suggest(query_text, index_types)
        facets = await self.index_adapter.get_facets(search_query)

        took_ms = (time.monotonic() - start) * 1000

        result_records = []
        for r in results:
            r.id = str(uuid.uuid4())
            r.query_id = search_query.id
            result_records.append(r)

        if result_records:
            await self.search_result_repository.save_results(result_records)

        self._publish_event(SearchPerformed(
            query_id=search_query.id,
            query_text=query_text,
            result_count=total,
            aggregate_id=search_query.id,
            payload={
                "query_text": query_text,
                "result_count": total,
                "took_ms": took_ms,
            },
        ))

        return SearchResponse(
            results=result_records,
            total=total,
            page=page,
            page_size=page_size,
            facets=facets,
            suggestions=suggestions,
            took_ms=took_ms,
        )

    async def search_fhir(
        self,
        resource_type: str,
        params: dict[str, Any],
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResponse:
        query_text = params.get("_query", "") or params.get("name", "") or params.get("identifier", "")
        filters = []
        for key, value in params.items():
            if key.startswith("_") or key in ("name", "identifier", "query"):
                continue
            if isinstance(value, list):
                filters.append({"field": key, "operator": "in", "value": value})
            else:
                filters.append({"field": key, "operator": "eq", "value": value})

        index_map = {
            "Patient": ["patient", "citizen"],
            "Encounter": ["encounter"],
            "Observation": ["lab_result"],
            "Organization": ["organization"],
            "Practitioner": ["practitioner"],
            "Appointment": ["appointment"],
        }
        index_types = index_map.get(resource_type, [resource_type.lower()])

        return await self.search(
            query_text=query_text,
            filters=filters,
            index_types=index_types,
            page=page,
            page_size=page_size,
        )

    async def suggest(
        self,
        query_text: str,
        index_types: list[str] | None = None,
        limit: int = 10,
    ) -> list[SearchSuggestion]:
        return await self.index_adapter.suggest(query_text, index_types, limit)

    async def get_facets(
        self,
        query_text: str = "",
        index_types: list[str] | None = None,
    ) -> list[SearchFacet]:
        search_query = SearchQuery(
            id=str(uuid.uuid4()),
            query_text=query_text,
            index_types=[SearchIndexType(t) for t in index_types] if index_types else list(SearchIndexType),
        )
        return await self.index_adapter.get_facets(search_query)

    async def save_search(
        self,
        name: str,
        description: str = "",
        query: dict[str, Any] | None = None,
        index_types: list[str] | None = None,
        created_by: str = "",
        scheduled: bool = False,
        schedule_cron: str = "",
    ) -> SavedSearch:
        saved = SavedSearch(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            query=query or {},
            index_types=[SearchIndexType(t) for t in index_types] if index_types else [],
            created_by=created_by,
            scheduled=scheduled,
            schedule_cron=schedule_cron,
        )
        result = await self.saved_search_repository.save(saved)

        self._publish_event(SavedSearchCreated(
            saved_search_id=result.id,
            name=name,
            aggregate_id=result.id,
            payload={"name": name, "scheduled": scheduled},
        ))

        return result

    async def list_saved_searches(
        self,
        created_by: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[SavedSearch]:
        return await self.saved_search_repository.list(
            created_by=created_by,
            skip=skip,
            limit=limit,
        )

    async def get_saved_search(self, search_id: str) -> SavedSearch:
        saved = await self.saved_search_repository.get(search_id)
        if not saved:
            raise SavedSearchNotFoundError(search_id)
        return saved

    async def delete_saved_search(self, search_id: str) -> None:
        saved = await self.saved_search_repository.get(search_id)
        if not saved:
            raise SavedSearchNotFoundError(search_id)
        await self.saved_search_repository.delete(search_id)

    async def rebuild_index(self, index_type: str | None = None) -> dict[str, Any]:
        types_to_rebuild = [index_type] if index_type else [t.value for t in SearchIndexType]
        total = 0
        results: dict[str, int] = {}
        for t in types_to_rebuild:
            try:
                count = await self.index_adapter.rebuild_index(t)
                results[t] = count
                total += count
            except Exception as exc:
                raise IndexAdapterError(f"Failed to rebuild index {t}: {exc}")

        self._publish_event(IndexRebuilt(
            index_type=index_type or "all",
            documents_indexed=total,
            aggregate_id="index_rebuild",
            payload={"index_type": index_type, "documents_indexed": total},
        ))

        return {"index_type": index_type or "all", "documents_indexed": results, "total": total}

    async def index_document(
        self,
        index_type: str,
        document_id: str,
        data: dict[str, Any],
    ) -> None:
        try:
            await self.index_adapter.index_document(index_type, document_id, data)
        except Exception as exc:
            raise IndexAdapterError(f"Failed to index document {index_type}/{document_id}: {exc}")

        self._publish_event(DocumentIndexed(
            resource_type=index_type,
            resource_id=document_id,
            aggregate_id=document_id,
            payload={"index_type": index_type, "document_id": document_id},
        ))

    async def remove_from_index(self, index_type: str, document_id: str) -> None:
        try:
            await self.index_adapter.remove_document(index_type, document_id)
        except Exception as exc:
            raise IndexAdapterError(f"Failed to remove document {index_type}/{document_id}: {exc}")

    async def get_search_stats(self) -> dict[str, Any]:
        return await self.search_result_repository.get_stats()

    async def health(self) -> dict[str, Any]:
        adapter_health = await self.index_adapter.health()
        return {
            "status": "ok",
            "module": "national_search_platform",
            "version": "1.0.0",
            "adapter": adapter_health,
        }

    def _publish_event(self, domain_event: Any) -> None:
        try:
            event = Event(
                name=domain_event.event_type,
                data=domain_event.payload if hasattr(domain_event, "payload") else {},
                correlation_id=getattr(domain_event, "correlation_id", ""),
                tenant_id=getattr(domain_event, "tenant_id", ""),
            )
            self.event_bus.publish(event)
        except Exception as exc:
            logger.error(
                "Failed to publish event %s: %s",
                getattr(domain_event, "event_type", "unknown"),
                exc,
            )
