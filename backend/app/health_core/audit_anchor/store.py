"""File-backed append-only storage for audit-anchor entries.

This is a local engineering building block: one JSON object per line, flushed and
``fsync``-ed on every append. It is deliberately dependency-free (no database, no
network, no external notary). It is NOT an independently notarized audit anchor.

Only synthetic keys and synthetic tenant identifiers are used in this package.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class AuditStoreError(Exception):
    """Raised when the persistent store is unreadable or malformed."""


class AuditChainError(Exception):
    """Raised when a chain operation would violate integrity (fail closed)."""


def open_store(path: str | Path) -> AuditAnchorStore:
    """Open (or lazily create) an append-only audit-anchor store at ``path``."""
    return AuditAnchorStore(path)


class AuditAnchorStore:
    """Append-only JSONL store with an ``fsync`` per append.

    There is intentionally no update or delete method. Tampering is detectable
    because every entry is signed and linked to the preceding entry's hash; see
    :mod:`app.health_core.audit_anchor.verification`.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, entry: Mapping[str, Any]) -> dict[str, Any]:
        """Durably append one record and return the stored representation."""
        record = dict(entry)
        line = json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return record

    def read_all(self) -> list[dict[str, Any]]:
        """Read every record in file order; fail closed on malformed content."""
        if not self.path.exists():
            return []
        entries: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise AuditStoreError(
                        f"malformed audit record at line {line_number}"
                    ) from exc
                if not isinstance(value, dict):
                    raise AuditStoreError(f"audit record at line {line_number} is not an object")
                entries.append(value)
        return entries

    def __repr__(self) -> str:
        return f"AuditAnchorStore(path={str(self.path)!r})"


__all__ = [
    "AuditAnchorStore",
    "AuditChainError",
    "AuditStoreError",
    "open_store",
]
