from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class PageParams:
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


@dataclass
class PaginatedResponse(Generic[T]):
    items: list[T] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    pages: int = 0

    def __post_init__(self) -> None:
        if self.page_size > 0:
            self.pages = -(-self.total // self.page_size)
