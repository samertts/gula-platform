from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Lookup_codeQuery:
    """lookup_code query for fhir_interoperability capability."""
    filters: dict = field(default_factory=dict)
    skip: int = 0
    limit: int = 100
