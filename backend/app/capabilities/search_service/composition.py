from __future__ import annotations

from .indexer import DefaultSearchIndexer
from .search import DefaultSearchService

_indexer: DefaultSearchIndexer | None = None
_search_service: DefaultSearchService | None = None


def get_search_indexer() -> DefaultSearchIndexer:
    global _indexer
    if _indexer is None:
        _indexer = DefaultSearchIndexer()
    return _indexer


def get_search_service() -> DefaultSearchService:
    global _search_service
    if _search_service is None:
        _search_service = DefaultSearchService(get_search_indexer())
    return _search_service
