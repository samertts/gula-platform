from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy import text

from app.national.search_platform.domain.entities import (
    FacetValue,
    SearchFacet,
    SearchQuery,
    SearchResult,
    SearchSuggestion,
)
from app.national.search_platform.domain.enums import SearchIndexType


class IndexAdapter(ABC):

    @abstractmethod
    async def search(self, query: SearchQuery) -> tuple[list[SearchResult], int]: ...

    @abstractmethod
    async def suggest(self, query_text: str, index_types: list[str] | None = None, limit: int = 10) -> list[SearchSuggestion]: ...

    @abstractmethod
    async def get_facets(self, query: SearchQuery) -> list[SearchFacet]: ...

    @abstractmethod
    async def index_document(self, index_type: str, document_id: str, data: dict[str, Any]) -> None: ...

    @abstractmethod
    async def remove_document(self, index_type: str, document_id: str) -> None: ...

    @abstractmethod
    async def rebuild_index(self, index_type: str) -> int: ...

    @abstractmethod
    async def health(self) -> dict[str, Any]: ...


class PostgresFullTextSearch(IndexAdapter):

    def __init__(self, db: Any) -> None:
        self.db = db

    async def search(self, query: SearchQuery) -> tuple[list[SearchResult], int]:
        if not query.query_text:
            return [], 0
        tsquery = " & ".join(query.query_text.strip().split())
        sql = """
            SELECT * FROM (
                SELECT id AS resource_id, 'patient' AS index_type,
                       name AS title, name AS description,
                       ts_rank(to_tsvector('simple', name || ' ' || COALESCE(phone, '') || ' ' || COALESCE(national_id, '')), to_tsquery('simple', :q)) AS score
                FROM patients
                WHERE to_tsvector('simple', name || ' ' || COALESCE(phone, '') || ' ' || COALESCE(national_id, '')) @@ to_tsquery('simple', :q)
                UNION ALL
                SELECT id AS resource_id, 'citizen' AS index_type,
                       full_name_ar AS title, full_name_en AS description,
                       ts_rank(to_tsvector('simple', COALESCE(full_name_ar, '') || ' ' || COALESCE(full_name_en, '') || ' ' || COALESCE(national_id, '')), to_tsquery('simple', :q)) AS score
                FROM national_citizens
                WHERE to_tsvector('simple', COALESCE(full_name_ar, '') || ' ' || COALESCE(full_name_en, '') || ' ' || COALESCE(national_id, '')) @@ to_tsquery('simple', :q)
            ) AS combined
            ORDER BY score DESC
            LIMIT :limit OFFSET :offset
        """
        rows = self.db.execute(sql, {"q": tsquery, "limit": query.limit, "offset": query.offset}).fetchall()
        count_sql = """
            SELECT COUNT(*) FROM (
                SELECT id FROM patients WHERE to_tsvector('simple', name || ' ' || COALESCE(phone, '') || ' ' || COALESCE(national_id, '')) @@ to_tsquery('simple', :q)
                UNION ALL
                SELECT id FROM national_citizens WHERE to_tsvector('simple', COALESCE(full_name_ar, '') || ' ' || COALESCE(full_name_en, '') || ' ' || COALESCE(national_id, '')) @@ to_tsquery('simple', :q)
            ) AS combined
        """
        total = self.db.execute(count_sql, {"q": tsquery}).scalar() or 0
        results = []
        for row in rows:
            results.append(SearchResult(
                id="",
                index_type=row.index_type,
                resource_id=row.resource_id,
                title=row.title,
                description=row.description,
                score=float(row.score) if hasattr(row, "score") and row.score else 0.0,
            ))
        return results, total

    async def suggest(self, query_text: str, index_types: list[str] | None = None, limit: int = 10) -> list[SearchSuggestion]:
        pattern = f"{query_text}%"
        rows = self.db.execute(
            "SELECT name AS text, 1.0 AS score FROM patients WHERE name ILIKE :p LIMIT :limit",
            {"p": pattern, "limit": limit},
        ).fetchall()
        return [SearchSuggestion(text=r.text, score=float(r.score), type="patient") for r in rows]

    async def get_facets(self, query: SearchQuery) -> list[SearchFacet]:
        if not query.query_text:
            return []
        tsquery = " & ".join(query.query_text.strip().split())
        facets: list[FacetValue] = []
        allowed = {item.value for item in query.index_types}
        if "patient" in allowed:
            count = self.db.execute(
                text("""
                    SELECT COUNT(*)
                    FROM patients
                    WHERE to_tsvector('simple', name || ' ' || COALESCE(phone, '') || ' ' || COALESCE(national_id, ''))
                      @@ to_tsquery('simple', :q)
                """),
                {"q": tsquery},
            ).scalar() or 0
            facets.append(FacetValue(value="patient", count=int(count)))
        if "citizen" in allowed:
            count = self.db.execute(
                text("""
                    SELECT COUNT(*)
                    FROM national_citizens
                    WHERE to_tsvector('simple', COALESCE(full_name_ar, '') || ' ' || COALESCE(full_name_en, '') || ' ' || COALESCE(national_id, ''))
                      @@ to_tsquery('simple', :q)
                """),
                {"q": tsquery},
            ).scalar() or 0
            facets.append(FacetValue(value="citizen", count=int(count)))
        return [SearchFacet(field="index_type", values=facets)]

    async def index_document(self, index_type: str, document_id: str, data: dict[str, Any]) -> None:
        raise NotImplementedError("PostgreSQL full-text search does not support document indexing")

    async def remove_document(self, index_type: str, document_id: str) -> None:
        raise NotImplementedError("PostgreSQL full-text search does not support document removal")

    async def rebuild_index(self, index_type: str) -> int:
        raise NotImplementedError("PostgreSQL full-text search does not provide a rebuild operation")

    async def health(self) -> dict[str, Any]:
        return {"status": "ok", "backend": "postgres_full_text_search"}


class ElasticsearchAdapter(IndexAdapter):

    def __init__(self, hosts: list[str] | None = None) -> None:
        self.hosts = hosts or ["http://localhost:9200"]

    async def search(self, query: SearchQuery) -> tuple[list[SearchResult], int]:
        raise NotImplementedError("Elasticsearch adapter is not configured")

    async def suggest(self, query_text: str, index_types: list[str] | None = None, limit: int = 10) -> list[SearchSuggestion]:
        raise NotImplementedError("Elasticsearch adapter is not configured")

    async def get_facets(self, query: SearchQuery) -> list[SearchFacet]:
        raise NotImplementedError("Elasticsearch adapter is not configured")

    async def index_document(self, index_type: str, document_id: str, data: dict[str, Any]) -> None:
        raise NotImplementedError("Elasticsearch adapter is not configured")

    async def remove_document(self, index_type: str, document_id: str) -> None:
        raise NotImplementedError("Elasticsearch adapter is not configured")

    async def rebuild_index(self, index_type: str) -> int:
        raise NotImplementedError("Elasticsearch adapter is not configured")

    async def health(self) -> dict[str, Any]:
        return {"status": "unavailable", "backend": "elasticsearch", "hosts": self.hosts}


class FHIRSearchAdapter(IndexAdapter):

    def __init__(self, base_url: str = "") -> None:
        self.base_url = base_url

    async def search(self, query: SearchQuery) -> tuple[list[SearchResult], int]:
        raise NotImplementedError("FHIR search adapter is not configured")

    async def suggest(self, query_text: str, index_types: list[str] | None = None, limit: int = 10) -> list[SearchSuggestion]:
        raise NotImplementedError("FHIR search adapter is not configured")

    async def get_facets(self, query: SearchQuery) -> list[SearchFacet]:
        raise NotImplementedError("FHIR search adapter is not configured")

    async def index_document(self, index_type: str, document_id: str, data: dict[str, Any]) -> None:
        raise NotImplementedError("FHIR search adapter is not configured")

    async def remove_document(self, index_type: str, document_id: str) -> None:
        raise NotImplementedError("FHIR search adapter is not configured")

    async def rebuild_index(self, index_type: str) -> int:
        raise NotImplementedError("FHIR search adapter is not configured")

    async def health(self) -> dict[str, Any]:
        return {"status": "unavailable", "backend": "fhir_search", "base_url": self.base_url}


class InMemoryIndex(IndexAdapter):

    def __init__(self) -> None:
        self.documents: dict[str, list[dict[str, Any]]] = {}

    async def search(self, query: SearchQuery) -> tuple[list[SearchResult], int]:
        if not query.query_text:
            return [], 0
        q = query.query_text.lower()
        results: list[SearchResult] = []
        for idx_type, docs in self.documents.items():
            if query.index_types and SearchIndexType(idx_type) not in query.index_types:
                continue
            for doc in docs:
                text = f"{doc.get('title', '')} {doc.get('description', '')} {doc.get('content', '')}"
                if q in text.lower():
                    results.append(SearchResult(
                        id="",
                        index_type=SearchIndexType(idx_type),
                        resource_id=doc.get("id", ""),
                        title=doc.get("title", ""),
                        description=doc.get("description", ""),
                        score=1.0,
                    ))
        total = len(results)
        paged = results[query.offset:query.offset + query.limit]
        return paged, total

    async def suggest(self, query_text: str, index_types: list[str] | None = None, limit: int = 10) -> list[SearchSuggestion]:
        pattern = query_text.lower()
        suggestions: list[SearchSuggestion] = []
        for idx_type, docs in self.documents.items():
            for doc in docs:
                title = doc.get("title", "").lower()
                if title.startswith(pattern):
                    suggestions.append(SearchSuggestion(text=doc["title"], score=1.0, type=idx_type))
        return suggestions[:limit]

    async def get_facets(self, query: SearchQuery) -> list[SearchFacet]:
        q = query.query_text.lower()
        counts: dict[str, int] = {}
        for idx_type, docs in self.documents.items():
            if query.index_types and SearchIndexType(idx_type) not in query.index_types:
                continue
            matched = [
                doc for doc in docs
                if not q or q in f"{doc.get('title', '')} {doc.get('description', '')} {doc.get('content', '')}".lower()
            ]
            if matched:
                counts[idx_type] = len(matched)
        return [
            SearchFacet(
                field="index_type",
                values=[FacetValue(value=key, count=value) for key, value in sorted(counts.items())],
            )
        ] if counts else []

    async def index_document(self, index_type: str, document_id: str, data: dict[str, Any]) -> None:
        if index_type not in self.documents:
            self.documents[index_type] = []
        self.documents[index_type] = [
            doc for doc in self.documents[index_type] if doc.get("id") != document_id
        ]
        self.documents[index_type].append({"id": document_id, **data})

    async def remove_document(self, index_type: str, document_id: str) -> None:
        if index_type in self.documents:
            self.documents[index_type] = [
                d for d in self.documents[index_type] if d.get("id") != document_id
            ]

    async def rebuild_index(self, index_type: str) -> int:
        raise NotImplementedError("In-memory adapter cannot rebuild an external index")

    async def health(self) -> dict[str, Any]:
        return {"status": "ok", "backend": "in_memory", "document_count": sum(len(d) for d in self.documents.values())}
