from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class APIResponse(Generic[T]):
    success: bool = True
    data: T | None = None
    message: str = ""
    request_id: str = ""


@dataclass
class ErrorResponse:
    detail: str
    error_code: str = "UNKNOWN_ERROR"
    request_id: str = ""
    errors: list[dict[str, Any]] = field(default_factory=list)
