from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Get_encounterQuery:
    """get_encounter query for encounter_management capability."""

    filters: dict = field(default_factory=dict)
    skip: int = 0
    limit: int = 100
