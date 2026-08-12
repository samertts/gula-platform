from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PaginatedResponse:
    items: list[dict[str, Any]] = field(default_factory=list)
    total: int = 0
    skip: int = 0
    limit: int = 100


@dataclass
class APIResponse:
    success: bool = True
    data: Any = None
    error: str | None = None
    message: str = ""
