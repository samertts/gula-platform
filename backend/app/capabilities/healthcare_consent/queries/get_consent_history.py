from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Get_consent_historyQuery:
    """get_consent_history query for healthcare_consent capability."""
    filters: dict = field(default_factory=dict)
    skip: int = 0
    limit: int = 100
