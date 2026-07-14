from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Search_fhirQuery:
    """search_fhir query for fhir_interoperability capability."""
    filters: dict = field(default_factory=dict)
    skip: int = 0
    limit: int = 100
