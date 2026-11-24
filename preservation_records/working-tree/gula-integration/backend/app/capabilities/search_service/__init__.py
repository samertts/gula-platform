"""search_service Capability: Unified search platform: full-text search across patients, orders, results, documents with filters, ranking, suggestions, indexing, permissions-aware

Domain: infrastructure
Layer: application
Version: 1.0.0
"""

from .capability import Search_serviceCapability
from .exceptions import IndexingError, SearchError
from .indexer import DefaultSearchIndexer
from .interfaces import SearchableDocument, SemanticQuery, SemanticSearchResult
from .search import DefaultSearchService
from .semantic import InfrastructureSemanticSearchService

__all__ = [
    "DefaultSearchIndexer",
    "DefaultSearchService",
    "IndexingError",
    "InfrastructureSemanticSearchService",
    "SearchError",
    "Search_serviceCapability",
    "SearchableDocument",
    "SemanticQuery",
    "SemanticSearchResult",
]
