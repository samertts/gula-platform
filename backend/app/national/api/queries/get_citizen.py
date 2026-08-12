from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GetCitizenQuery:
    citizen_id: str = ""


@dataclass
class SearchCitizenQuery:
    query: str = ""
    skip: int = 0
    limit: int = 20
