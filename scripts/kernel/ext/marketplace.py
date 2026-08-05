"""GULA-KERNEL-EXT-001 Phase 7 — AI Marketplace.

Catalog and installation of reusable AI assets: plugins, skills,
policies, templates, and prompts. Every catalog item carries an immutable
id (CAT-XXXXXX), semantic version, source, and license. Installation is
audited and idempotent; items are searchable and replaceable.

Reuses the auto-registry ID pattern catalogue (scripts/auto_registry.py)
and the SDK manifest fields; no I/O at import time.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core import utcnow
from .compatibility import CompatibilityError, parse_version

MARKETPLACE_DIR = ".ai/core/marketplace/"

ITEM_KINDS = ("plugin", "skill", "policy", "template", "prompt")
APPROVED_LICENSES = ("MIT", "Apache-2.0", "BSD-3-Clause", "MPL-2.0")


class MarketplaceError(Exception):
    """Raised for invalid marketplace operations."""


@dataclass
class CatalogItem:
    """One installable AI asset."""

    id: str
    kind: str
    name: str
    version: str
    description: str
    source: str = ""
    license: str = "MIT"
    published_at: str = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        if not self.id.startswith("CAT-"):
            raise MarketplaceError(f"catalog id must start with CAT-: {self.id!r}")
        if self.kind not in ITEM_KINDS:
            raise MarketplaceError(f"unknown kind: {self.kind!r}")
        try:
            parse_version(self.version)
        except CompatibilityError as exc:
            raise MarketplaceError(str(exc)) from exc
        if self.license not in APPROVED_LICENSES:
            raise MarketplaceError(f"unapproved license: {self.license!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "source": self.source,
            "license": self.license,
            "published_at": self.published_at,
        }


class Marketplace:
    """Catalog of reusable AI assets with audited installation."""

    def __init__(self) -> None:
        self._items: dict[str, CatalogItem] = {}
        self._installed: dict[str, str] = {}
        self._history: list[dict[str, Any]] = []

    def add(self, item: CatalogItem) -> CatalogItem:
        if item.id in self._items:
            raise MarketplaceError(f"catalog item already indexed: {item.id}")
        self._items[item.id] = item
        self._history.append({"event": "indexed", "id": item.id, "at": utcnow()})
        return item

    def get(self, item_id: str) -> CatalogItem:
        try:
            return self._items[item_id]
        except KeyError:
            raise MarketplaceError(f"unknown catalog item: {item_id}") from None

    def search(self, kind: str | None = None, query: str = "") -> list[CatalogItem]:
        query = query.lower()
        items = self._items.values()
        if kind is not None:
            items = (i for i in items if i.kind == kind)
        if query:
            items = (
                i for i in items
                if query in i.name.lower() or query in i.description.lower()
            )
        return sorted(items, key=lambda i: i.name)

    def install(self, item_id: str) -> str:
        item = self.get(item_id)
        if item.id in self._installed:
            raise MarketplaceError(f"already installed: {item_id}")
        self._installed[item.id] = item.version
        self._history.append({"event": "installed", "id": item.id, "version": item.version, "at": utcnow()})
        return item.version

    def uninstall(self, item_id: str) -> None:
        if item_id not in self._installed:
            raise MarketplaceError(f"not installed: {item_id}")
        del self._installed[item_id]
        self._history.append({"event": "uninstalled", "id": item_id, "at": utcnow()})

    def is_installed(self, item_id: str) -> bool:
        return item_id in self._installed

    def installed(self) -> list[CatalogItem]:
        return [self._items[i] for i in sorted(self._installed)]

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "items": [i.to_dict() for i in self._items.values()],
            "installed": dict(self._installed),
            "history": list(self._history),
        }

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.snapshot(), indent=2) + "\n", encoding="utf-8")
        return path
