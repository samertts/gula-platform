from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class KnowledgePlatform:
    _instance: KnowledgePlatform | None = None

    INDEXABLE_DIRS = [
        "docs/",
        "governance/",
        "backend/app/governance/",
        "backend/app/engineering/",
        "backend/app/security/",
        "backend/app/fhir/",
        "backend/app/integration/",
        "backend/app/ai_fabric/",
    ]

    def __new__(cls) -> KnowledgePlatform:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._index: dict[str, list[dict[str, Any]]] = {}
            cls._instance._built = False
        return cls._instance

    def build_index(self) -> None:
        if self._built:
            return
        repo_root = Path(__file__).resolve().parent.parent.parent
        self._index = {}

        categories = {
            "architecture": ["architecture", "ARCHITECTURE", "adr"],
            "policies": ["policy", "POLICY", "constitution"],
            "adr": ["ADR-", "adr-", "decision record"],
            "documentation": ["README", "readme", ".md"],
            "modules": ["backend/app/"],
            "api": ["routes", "Routes", "openapi", "OpenAPI"],
            "database": ["migration", "Migration", "alembic", "schema", "table"],
            "fhir": ["fhir", "FHIR"],
            "security": ["security", "Security", "auth", "Auth", "encrypt"],
            "infrastructure": ["docker", "Docker", "k8s", "terraform", "helm"],
            "governance": ["governance", "Governance"],
            "engineering": ["engineering", "Engineering"],
            "ai": ["ai_fabric", "AI", "model", "llm"],
        }

        for cat, patterns in categories.items():
            matches = []
            for search_dir in self.INDEXABLE_DIRS:
                full_dir = repo_root / search_dir
                if not full_dir.exists():
                    continue
                for f in full_dir.rglob("*"):
                    if f.is_file() and not any(excl in str(f) for excl in ["__pycache__", ".git", "node_modules"]):
                        rel = str(f.relative_to(repo_root))
                        for pat in patterns:
                            if pat in rel:
                                content = ""
                                try:
                                    content = f.read_text(encoding="utf-8", errors="replace")[:500]
                                except Exception:
                                    content = ""
                                matches.append({
                                    "path": rel,
                                    "preview": content[:200],
                                    "size": len(content),
                                })
                                break
            self._index[cat] = matches[:100]

        self._built = True

    @property
    def index(self) -> dict[str, list[dict[str, Any]]]:
        if not self._built:
            self.build_index()
        return self._index

    def search(self, query: str, category: str = "") -> list[dict[str, Any]]:
        if not self._built:
            self.build_index()
        results: list[dict[str, Any]] = []
        q = query.lower()
        words = q.split()

        cats = [category] if category else list(self._index.keys())
        for cat in cats:
            for entry in self._index.get(cat, []):
                text = (entry["path"] + " " + entry["preview"]).lower()
                if all(w in text for w in words):
                    score = sum(1 for w in words if w in text) / len(words)
                    results.append({**entry, "category": cat, "score": score})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:20]

    def search_by_category(self, category: str) -> list[dict[str, Any]]:
        return self._index.get(category, [])

    def get_categories(self) -> list[str]:
        return list(self._index.keys())

    def get_stats(self) -> dict[str, Any]:
        if not self._built:
            self.build_index()
        total = sum(len(v) for v in self._index.values())
        return {
            "total_entries": total,
            "categories": len(self._index),
            "entries_per_category": {k: len(v) for k, v in self._index.items()},
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "stats": self.get_stats(),
            "categories": self._index,
        }
