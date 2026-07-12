from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("gula.search")


class Document:
    def __init__(self, doc_id: str, fields: dict[str, str], boost: float = 1.0) -> None:
        self.id = doc_id
        self.fields = fields
        self.boost = boost

    def __repr__(self) -> str:
        return f"Document(id={self.id!r}, fields={list(self.fields)})"


class SearchEngine:
    def __init__(self) -> None:
        self._documents: dict[str, Document] = {}

    def index(self, doc: Document) -> None:
        self._documents[doc.id] = doc

    def bulk_index(self, docs: list[Document]) -> None:
        for doc in docs:
            self.index(doc)

    def remove(self, doc_id: str) -> None:
        self._documents.pop(doc_id, None)

    def search(self, query: str, fields: list[str] | None = None, limit: int = 20) -> list[tuple[Document, float]]:
        query_terms = query.lower().split()
        results: list[tuple[Document, float]] = []
        for doc in self._documents.values():
            score = 0.0
            search_fields = fields or list(doc.fields.keys())
            for field in search_fields:
                value = doc.fields.get(field, "").lower()
                for term in query_terms:
                    if term in value:
                        score += doc.boost * (len(term) / max(len(value), 1))
                        if value.startswith(term):
                            score += doc.boost
            if score > 0:
                results.append((doc, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def count(self) -> int:
        return len(self._documents)

    def clear(self) -> None:
        self._documents.clear()


class Searchable:
    def to_document(self) -> Document:
        raise NotImplementedError


engine = SearchEngine()

__all__ = ["Document", "SearchEngine", "Searchable", "engine"]
