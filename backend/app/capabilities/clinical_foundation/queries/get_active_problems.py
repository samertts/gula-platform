from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Get_active_problemsQuery:
    """get_active_problems query for clinical_foundation capability."""

    filters: dict = field(default_factory=dict)
    skip: int = 0
    limit: int = 100
