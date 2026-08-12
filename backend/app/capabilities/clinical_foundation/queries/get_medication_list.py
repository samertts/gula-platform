from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Get_medication_listQuery:
    """get_medication_list query for clinical_foundation capability."""

    filters: dict = field(default_factory=dict)
    skip: int = 0
    limit: int = 100
