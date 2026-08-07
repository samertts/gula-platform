from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends

from app.security.dependencies import get_current_user

from .composition import get_search_indexer
from .interfaces import SearchableDocument

router = APIRouter(prefix="/search-service", tags=["Search Service"])


@router.get("/")
async def list_search_service(
    skip: int = 0,
    limit: int = 100,
    current_user: Any = Depends(get_current_user),
) -> dict:
    indexer = get_search_indexer()
    items = await indexer.search("", {"limit": max(1, limit) + skip})
    return {"items": items[skip:], "total": len(items), "skip": skip, "limit": limit}


@router.get("/{id}")
async def get_search_service(
    id: str,
    current_user: Any = Depends(get_current_user),
) -> dict:
    indexer = get_search_indexer()
    entry = await indexer.get(id)
    return {"id": id, **entry} if entry else {"id": id}


@router.post("/")
async def create_search_service(
    data: dict,
    current_user: Any = Depends(get_current_user),
) -> dict:
    indexer = get_search_indexer()
    doc = SearchableDocument(
        id=uuid4(),
        filename=data.get("filename", ""),
        mime_type=data.get("mime_type", "application/octet-stream"),
        page_count=int(data.get("page_count", 0)),
        created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
        metadata=data.get("metadata", {}),
        tags=list(data.get("tags", [])),
    )
    doc_id = await indexer.index_document(doc, data.get("text", ""), data.get("entities", []))
    return {"success": True, "id": doc_id}


@router.put("/{id}")
async def update_search_service(
    id: str,
    data: dict,
    current_user: Any = Depends(get_current_user),
) -> dict:
    indexer = get_search_indexer()
    await indexer.delete_index(id)
    doc = SearchableDocument(
        id=id,
        filename=data.get("filename", ""),
        mime_type=data.get("mime_type", "application/octet-stream"),
        page_count=int(data.get("page_count", 0)),
        created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
        metadata=data.get("metadata", {}),
        tags=list(data.get("tags", [])),
    )
    doc_id = await indexer.index_document(doc, data.get("text", ""), data.get("entities", []))
    return {"success": True, "id": doc_id}


@router.delete("/{id}")
async def delete_search_service(
    id: str,
    current_user: Any = Depends(get_current_user),
) -> dict:
    indexer = get_search_indexer()
    await indexer.delete_index(id)
    return {"success": True}
