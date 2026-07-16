from app.national.search_platform.application.interfaces import (
    ElasticsearchAdapter,
    FHIRSearchAdapter,
    IndexAdapter,
    InMemoryIndex,
    PostgresFullTextSearch,
)
from app.national.search_platform.application.service import SearchPlatformService
from app.national.search_platform.domain.entities import (
    FacetValue,
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
    InvalidSearchQueryError,
    SavedSearchNotFoundError,
    SearchExecutionError,
)
from app.national.search_platform.infrastructure.models import (
    NationalSavedSearch,
    NationalSearchResult,
)
from app.national.search_platform.infrastructure.repository import (
    SQLAlchemySavedSearchRepository,
    SQLAlchemySearchResultRepository,
)

__all__ = [
    "DocumentIndexed",
    "ElasticsearchAdapter",
    "FHIRSearchAdapter",
    "FacetValue",
    "FilterOperator",
    "InMemoryIndex",
    "IndexAdapter",
    "IndexAdapterError",
    "IndexRebuilt",
    "InvalidSearchQueryError",
    "NationalSavedSearch",
    "NationalSearchResult",
    "PostgresFullTextSearch",
    "SQLAlchemySavedSearchRepository",
    "SQLAlchemySearchResultRepository",
    "SavedSearch",
    "SavedSearchCreated",
    "SavedSearchNotFoundError",
    "SavedSearchRepository",
    "SearchExecutionError",
    "SearchFacet",
    "SearchFilter",
    "SearchIndexType",
    "SearchMode",
    "SearchOperator",
    "SearchPerformed",
    "SearchPlatformService",
    "SearchQuery",
    "SearchResponse",
    "SearchResult",
    "SearchResultRepository",
    "SearchSuggestion",
    "SortOrder",
]
