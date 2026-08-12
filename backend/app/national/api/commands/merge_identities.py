from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MergeIdentitiesCommand:
    primary_citizen_id: str = ""
    secondary_citizen_id: str = ""
    reason: str = ""
    method: str = "manual"
    requested_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__
