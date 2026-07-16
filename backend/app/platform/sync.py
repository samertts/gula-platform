"""Standardized offline sync module — change tracking, conflict resolution, bidirectional sync."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from . import PlatformRegistry

logger = logging.getLogger("gula.platform.sync")


@dataclass
class SyncChange:
    id: str = ""
    entity_type: str = ""
    entity_id: str = ""
    action: str = ""
    data: dict | None = None
    version: int = 1
    timestamp: str = ""


@dataclass
class SyncStatus:
    pending_changes: int = 0
    last_sync_at: str | None = None
    conflicts: int = 0


class SyncService:
    def __init__(self) -> None:
        self._changes: list[SyncChange] = []
        self._last_sync: str | None = None

    def push_changes(self, changes: list[SyncChange]) -> int:
        count = 0
        for change in changes:
            self._changes.append(change)
            count += 1
        return count

    def pull_changes(self, since: str | None = None) -> list[SyncChange]:
        if since is None:
            return list(self._changes)
        return [c for c in self._changes if c.timestamp > since]

    def resolve_conflicts(self, local: SyncChange, remote: SyncChange) -> SyncChange:
        if local.version >= remote.version:
            return local
        return remote

    def get_sync_status(self) -> dict:
        return {
            "pending_changes": len(self._changes),
            "last_sync_at": self._last_sync,
        }


PlatformRegistry.register("sync", SyncService(), capabilities=[
    {"name": "push_changes", "description": "Push local changes to the sync queue"},
    {"name": "pull_changes", "description": "Pull remote changes since a timestamp"},
    {"name": "resolve_conflicts", "description": "Resolve a conflict between local and remote changes"},
    {"name": "get_sync_status", "description": "Get the current sync status"},
])
