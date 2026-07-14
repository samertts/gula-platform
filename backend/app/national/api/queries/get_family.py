from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GetFamilyQuery:
    family_id: str = ""
    family_hash: str | None = None
