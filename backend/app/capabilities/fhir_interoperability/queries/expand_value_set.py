from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Expand_value_setQuery:
    """expand_value_set query for fhir_interoperability capability."""
    filters: dict = field(default_factory=dict)
    skip: int = 0
    limit: int = 100
