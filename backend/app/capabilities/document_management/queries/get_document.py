from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Get_documentQuery:
    """get_document query for document_management capability."""

    filters: dict = field(default_factory=dict)
    skip: int = 0
    limit: int = 100
