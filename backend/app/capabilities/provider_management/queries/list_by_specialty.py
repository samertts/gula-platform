from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class List_by_specialtyQuery:
    """list_by_specialty query for provider_management capability."""
    filters: dict = field(default_factory=dict)
    skip: int = 0
    limit: int = 100
