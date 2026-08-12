from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SearchQuery:
    """search query for search_service capability."""

    filters: dict = field(default_factory=dict)
    skip: int = 0
    limit: int = 100
