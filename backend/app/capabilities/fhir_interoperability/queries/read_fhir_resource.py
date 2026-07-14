from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Read_fhir_resourceQuery:
    """read_fhir_resource query for fhir_interoperability capability."""
    filters: dict = field(default_factory=dict)
    skip: int = 0
    limit: int = 100
