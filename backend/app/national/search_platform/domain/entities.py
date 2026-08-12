from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.national.search_platform.domain.enums import (
    FilterOperator,
    SearchIndexType,
    SearchMode,
    SearchOperator,
    SortOrder,
)


@dataclass
class SearchFilter:
    field: str
    operator: FilterOperator = FilterOperator.EQ
    value: Any = None


@dataclass
class SearchQuery:
    id: str
    query_text: str = ""
    filters: list[SearchFilter] = field(default_factory=list)
    index_types: list[SearchIndexType] = field(default_factory=lambda: list(SearchIndexType))
    page: int = 1
    page_size: int = 20
    sort_by: str = ""
    sort_order: SortOrder = SortOrder.DESC
    mode: SearchMode = SearchMode.EXACT
    operator: SearchOperator = SearchOperator.AND
    search_id: str = ""

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


@dataclass
class SearchResult:
    id: str
    query_id: str = ""
    index_type: SearchIndexType = SearchIndexType.PATIENT
    resource_id: str = ""
    resource_type: str = ""
    score: float = 0.0
    title: str = ""
    description: str = ""
    highlights: dict[str, str] = field(default_factory=dict)
    matched_fields: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    url: str = ""


@dataclass
class SearchResponse:
    results: list[SearchResult] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    facets: list[SearchFacet] = field(default_factory=list)
    suggestions: list[SearchSuggestion] = field(default_factory=list)
    took_ms: float = 0.0


@dataclass
class SavedSearch:
    id: str
    name: str
    description: str = ""
    query: dict[str, Any] = field(default_factory=dict)
    index_types: list[SearchIndexType] = field(default_factory=list)
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    scheduled: bool = False
    schedule_cron: str = ""


@dataclass
class SearchFacet:
    field: str
    values: list[FacetValue] = field(default_factory=list)


@dataclass
class FacetValue:
    value: str
    count: int = 0


@dataclass
class SearchSuggestion:
    text: str
    score: float = 0.0
    type: str = "query"
