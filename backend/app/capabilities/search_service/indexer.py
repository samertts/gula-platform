from __future__ import annotations

from typing import Any


class DefaultSearchIndexer:
    def __init__(self) -> None:
        self._index: dict[str, dict] = {}
        self._text_index: list[dict] = []

    async def index_document(self, document, text: str, entities) -> str:
        doc_id = str(document.id)
        self._index[doc_id] = {
            "document_id": doc_id,
            "filename": document.filename,
            "text": text[:10000],
            "mime_type": document.mime_type,
            "page_count": document.page_count,
            "created_at": document.created_at.isoformat(),
            "entities": [
                {"type": str(e.entity_type), "value": e.value, "confidence": e.confidence}
                for e in entities[:50]
            ],
            "metadata": document.metadata,
            "tags": document.tags,
        }
        self._text_index.append(
            {
                "id": doc_id,
                "text": text,
                "filename": document.filename,
            },
        )
        return doc_id

    async def get(self, document_id: Any) -> dict | None:
        return self._index.get(str(document_id))

    async def search(self, query: str, filters: dict | None = None) -> list[dict]:
        query_lower = query.lower()
        results = []
        for _doc_id, entry in self._index.items():
            if query_lower in entry["text"].lower() or query_lower in entry["filename"].lower():
                if filters:
                    if "category" in filters and entry.get("category") != filters["category"]:
                        continue
                    if "patient_id" in filters:
                        meta_patient = entry.get("metadata", {}).get("patient_id", "")
                        if meta_patient != filters["patient_id"]:
                            continue
                results.append(entry)

        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        limit = (filters or {}).get("limit", 50)
        return results[:limit]

    async def hybrid_search(
        self, query: str, query_vector: list | None = None, limit: int = 50,
    ) -> list[dict]:
        return await self.search(query, {"limit": limit})

    async def semantic_search(self, query: str, limit: int = 50) -> list[dict]:
        return await self.search(query, {"limit": limit})

    async def delete_index(self, document_id: Any) -> None:
        self._index.pop(str(document_id), None)
        self._text_index = [e for e in self._text_index if e["id"] != str(document_id)]

    async def rebuild_index(self) -> None:
        self._index.clear()
        self._text_index.clear()
