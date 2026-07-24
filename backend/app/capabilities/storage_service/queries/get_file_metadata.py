from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Get_file_metadataQuery:
    """get_file_metadata query for storage_service capability."""

    filters: dict = field(default_factory=dict)
    skip: int = 0
    limit: int = 100
