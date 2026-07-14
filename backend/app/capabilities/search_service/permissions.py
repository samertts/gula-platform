from __future__ import annotations

from enum import Enum


class Search_servicePermission(Enum):
    SEARCH.EXECUTE = "search_service:search.execute"
    SEARCH.ADMIN = "search_service:search.admin"

    def describe(self) -> str:
        descriptions = {        "search_service:search.execute": "Search.Execute",
                "search_service:search.admin": "Search.Admin"}
        return descriptions.get(self, self.value)
