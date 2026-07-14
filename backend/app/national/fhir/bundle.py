from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app._compat import UTC


@dataclass
class FHIRBundleEntry:
    full_url: str = ""
    resource: dict | None = None
    search: dict | None = None
    request: dict | None = None
    response: dict | None = None


class FHIRBundle:
    def __init__(self, bundle_type: str = "searchset") -> None:
        self.resource_type = "Bundle"
        self.id = ""
        self.type = bundle_type
        self.timestamp = datetime.now(UTC).isoformat()
        self.total: int = 0
        self.entries: list[FHIRBundleEntry] = []
        self.link: list[dict] = []

    def add_entry(self, entry: FHIRBundleEntry) -> None:
        self.entries.append(entry)
        self.total = len(self.entries)

    def to_dict(self) -> dict[str, Any]:
        result = {
            "resourceType": self.resource_type,
            "id": self.id,
            "type": self.type,
            "timestamp": self.timestamp,
            "total": self.total,
            "entry": [],
        }
        for entry in self.entries:
            entry_dict: dict = {}
            if entry.full_url:
                entry_dict["fullUrl"] = entry.full_url
            if entry.resource:
                entry_dict["resource"] = entry.resource
            if entry.search:
                entry_dict["search"] = entry.search
            result["entry"].append(entry_dict)
        if self.link:
            result["link"] = self.link
        return result
