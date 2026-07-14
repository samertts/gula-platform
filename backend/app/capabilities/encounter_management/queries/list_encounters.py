from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class List_encountersQuery:
    """list_encounters query for encounter_management capability."""
    filters: dict = field(default_factory=dict)
    skip: int = 0
    limit: int = 100
