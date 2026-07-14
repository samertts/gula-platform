from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class List_document_versionsQuery:
    """list_document_versions query for document_management capability."""
    filters: dict = field(default_factory=dict)
    skip: int = 0
    limit: int = 100
