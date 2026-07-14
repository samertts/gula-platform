from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class APIResponse:
    success: bool = True
    data: Any = None
    message: str = ""
    error: str = ""
    request_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"success": self.success}
        if self.data is not None:
            result["data"] = self.data
        if self.message:
            result["message"] = self.message
        if self.error:
            result["error"] = self.error
        if self.request_id:
            result["request_id"] = self.request_id
        return result


@dataclass
class PaginatedResponse(APIResponse):
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0

    def __post_init__(self) -> None:
        if self.total_pages == 0 and self.total > 0:
            self.total_pages = max(1, (self.total + self.page_size - 1) // self.page_size)

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update({"total": self.total, "page": self.page, "page_size": self.page_size, "total_pages": self.total_pages})
        return result


@dataclass
class APIError:
    code: int = 500
    message: str = "Internal Server Error"
    message_ar: str = "حدث خطأ داخلي"
    details: Any = None
    request_id: str = ""


__all__ = ["APIError", "APIResponse", "PaginatedResponse"]
