from __future__ import annotations

from app.national.exceptions import NationalDomainError


class SavedSearchNotFoundError(NationalDomainError):
    def __init__(self, search_id: str) -> None:
        self.search_id = search_id
        super().__init__(f"Saved search not found: {search_id}")


class SearchExecutionError(NationalDomainError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Search execution failed: {reason}")


class IndexAdapterError(NationalDomainError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Index adapter error: {reason}")


class InvalidSearchQueryError(NationalDomainError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Invalid search query: {reason}")
