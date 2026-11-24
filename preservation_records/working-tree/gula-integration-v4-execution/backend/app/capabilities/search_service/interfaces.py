"""Contracts for the canonical search service provider.

These dataclasses mirror the field names consumed by the promoted search
implementations so the canonical provider stays self-contained (no import of
any domain package). Consumers pass structurally-compatible objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class SemanticQuery:
    query_text: str = ""
    query_vector: list[float] = field(default_factory=list)
    category_filter: list[Any] = field(default_factory=list)
    entity_filter: dict[str, str] = field(default_factory=dict)
    date_range: tuple[datetime | None, datetime | None] = (None, None)
    confidentiality_filter: list[Any] = field(default_factory=list)
    limit: int = 20
    offset: int = 0
    hybrid_search: bool = True
    arabic_boost: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticSearchResult:
    document_id: UUID | None = None
    score: float = 0.0
    text_snippet: str = ""
    category: Any = None
    entities: list[Any] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchableDocument:
    id: UUID | None = None
    filename: str = ""
    mime_type: str = "application/octet-stream"
    page_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
