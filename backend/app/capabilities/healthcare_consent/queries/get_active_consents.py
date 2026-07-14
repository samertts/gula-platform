from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Get_active_consentsQuery:
    """get_active_consents query for healthcare_consent capability."""
    filters: dict = field(default_factory=dict)
    skip: int = 0
    limit: int = 100
