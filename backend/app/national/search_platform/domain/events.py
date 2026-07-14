from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.national.events.base import NationalDomainEvent


@dataclass
class SearchPerformed(NationalDomainEvent):
    event_type: str = "national.search.performed"
    aggregate_type: str = "SearchQuery"
    query_id: str = ""
    query_text: str = ""
    result_count: int = 0


@dataclass
class IndexRebuilt(NationalDomainEvent):
    event_type: str = "national.search.index.rebuilt"
    aggregate_type: str = "SearchIndex"
    index_type: str = ""
    documents_indexed: int = 0


@dataclass
class DocumentIndexed(NationalDomainEvent):
    event_type: str = "national.search.document.indexed"
    aggregate_type: str = "SearchDocument"
    resource_type: str = ""
    resource_id: str = ""


@dataclass
class SavedSearchCreated(NationalDomainEvent):
    event_type: str = "national.search.saved_search.created"
    aggregate_type: str = "SavedSearch"
    saved_search_id: str = ""
    name: str = ""
