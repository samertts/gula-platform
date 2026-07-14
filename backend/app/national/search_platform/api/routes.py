from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.national.search_platform.application.interfaces import PostgresFullTextSearch
from app.national.search_platform.application.service import SearchPlatformService
from app.national.search_platform.exceptions import (
    IndexAdapterError,
    SavedSearchNotFoundError,
    SearchExecutionError,
)
from app.national.search_platform.infrastructure.repository import (
    SQLAlchemySavedSearchRepository,
    SQLAlchemySearchResultRepository,
)

router = APIRouter(prefix="/national/search", tags=["National Search Platform"])


def _get_service(db: Session = Depends(get_db)) -> SearchPlatformService:
    from app.kernel.event_bus.bus import EventBus
    from app.kernel import Kernel

    kernel = Kernel.get_instance()
    event_bus = kernel.event_bus if hasattr(kernel, "event_bus") else EventBus(kernel)
    index_adapter = PostgresFullTextSearch(db)
    return SearchPlatformService(
        index_adapter=index_adapter,
        saved_search_repository=SQLAlchemySavedSearchRepository(db),
        search_result_repository=SQLAlchemySearchResultRepository(db),
        event_bus=event_bus,
    )


@router.post("/search")
async def search_post(
    body: dict[str, Any],
    service: SearchPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        response = await service.search(
            query_text=body.get("query", ""),
            filters=body.get("filters"),
            index_types=body.get("index_types"),
            page=body.get("page", 1),
            page_size=body.get("page_size", 20),
            sort_by=body.get("sort_by", ""),
            sort_order=body.get("sort_order", "desc"),
            mode=body.get("mode", "exact"),
            operator=body.get("operator", "and"),
        )
        return _search_response_to_dict(response)
    except SearchExecutionError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/search")
async def search_get(
    q: str = Query(""),
    index_types: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query(""),
    sort_order: str = Query("desc"),
    mode: str = Query("exact"),
    service: SearchPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        parsed_index_types = index_types.split(",") if index_types else None
        response = await service.search(
            query_text=q,
            index_types=parsed_index_types,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            mode=mode,
        )
        return _search_response_to_dict(response)
    except SearchExecutionError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/fhir/search")
async def fhir_search(
    body: dict[str, Any],
    service: SearchPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        response = await service.search_fhir(
            resource_type=body.get("resourceType", "Patient"),
            params=body.get("params", {}),
            page=body.get("page", 1),
            page_size=body.get("_count", 20),
        )
        return _search_response_to_dict(response)
    except SearchExecutionError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/suggest")
async def suggest(
    q: str = Query("", min_length=1),
    index_types: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    service: SearchPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    parsed_index_types = index_types.split(",") if index_types else None
    suggestions = await service.suggest(
        query_text=q,
        index_types=parsed_index_types,
        limit=limit,
    )
    return [
        {
            "text": s.text,
            "score": s.score,
            "type": s.type,
        }
        for s in suggestions
    ]


@router.get("/facets")
async def get_facets(
    q: str = Query(""),
    index_types: str | None = Query(None),
    service: SearchPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    parsed_index_types = index_types.split(",") if index_types else None
    facets = await service.get_facets(
        query_text=q,
        index_types=parsed_index_types,
    )
    return [
        {
            "field": f.field,
            "values": [{"value": v.value, "count": v.count} for v in f.values],
        }
        for f in facets
    ]


@router.post("/saved", status_code=status.HTTP_201_CREATED)
async def save_search(
    body: dict[str, Any],
    service: SearchPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    saved = await service.save_search(
        name=body.get("name", ""),
        description=body.get("description", ""),
        query=body.get("query"),
        index_types=body.get("index_types"),
        created_by=body.get("created_by", ""),
        scheduled=body.get("scheduled", False),
        schedule_cron=body.get("schedule_cron", ""),
    )
    return _saved_search_to_dict(saved)


@router.get("/saved")
async def list_saved_searches(
    created_by: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: SearchPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    saved = await service.list_saved_searches(
        created_by=created_by,
        skip=skip,
        limit=limit,
    )
    return [_saved_search_to_dict(s) for s in saved]


@router.get("/saved/{search_id}")
async def get_saved_search(
    search_id: str,
    service: SearchPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        saved = await service.get_saved_search(search_id)
        return _saved_search_to_dict(saved)
    except SavedSearchNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/saved/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(
    search_id: str,
    service: SearchPlatformService = Depends(_get_service),
) -> None:
    try:
        await service.delete_saved_search(search_id)
    except SavedSearchNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/index/rebuild")
async def rebuild_index(
    body: dict[str, Any],
    service: SearchPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return await service.rebuild_index(
            index_type=body.get("index_type"),
        )
    except IndexAdapterError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/index/document", status_code=status.HTTP_201_CREATED)
async def index_document(
    body: dict[str, Any],
    service: SearchPlatformService = Depends(_get_service),
) -> dict[str, str]:
    try:
        await service.index_document(
            index_type=body.get("index_type", ""),
            document_id=body.get("document_id", ""),
            data=body.get("data", {}),
        )
        return {"status": "indexed"}
    except IndexAdapterError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/index/document/{index_type}/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_index(
    index_type: str,
    document_id: str,
    service: SearchPlatformService = Depends(_get_service),
) -> None:
    try:
        await service.remove_from_index(index_type, document_id)
    except IndexAdapterError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/stats")
async def get_search_stats(
    service: SearchPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    return await service.get_search_stats()


@router.get("/health")
async def health(
    service: SearchPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    return await service.health()


def _search_response_to_dict(response: Any) -> dict[str, Any]:
    return {
        "results": [
            {
                "id": r.id,
                "query_id": r.query_id,
                "index_type": r.index_type.value,
                "resource_id": r.resource_id,
                "resource_type": r.resource_type,
                "score": r.score,
                "title": r.title,
                "description": r.description,
                "highlights": r.highlights,
                "matched_fields": r.matched_fields,
                "metadata": r.metadata,
                "url": r.url,
            }
            for r in response.results
        ],
        "total": response.total,
        "page": response.page,
        "page_size": response.page_size,
        "facets": [
            {
                "field": f.field,
                "values": [{"value": v.value, "count": v.count} for v in f.values],
            }
            for f in response.facets
        ],
        "suggestions": [
            {"text": s.text, "score": s.score, "type": s.type}
            for s in response.suggestions
        ],
        "took_ms": response.took_ms,
    }


def _saved_search_to_dict(s: Any) -> dict[str, Any]:
    return {
        "id": s.id,
        "name": s.name,
        "description": s.description,
        "query": s.query,
        "index_types": [t.value for t in s.index_types],
        "created_by": s.created_by,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        "scheduled": s.scheduled,
        "schedule_cron": s.schedule_cron,
    }
