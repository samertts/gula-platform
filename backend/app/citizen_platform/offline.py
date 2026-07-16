from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.platform.sync import SyncChange
from app.platform.sync import SyncService as PlatformSyncService

logger = logging.getLogger("gula.citizen.offline")


@dataclass
class OfflineAction:
    id: str = ""
    citizen_id: str = ""
    action_type: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    synced: bool = False
    sync_error: str = ""


@dataclass
class SyncManifest:
    citizen_id: str = ""
    last_sync_at: str = ""
    pending_actions: int = 0
    failed_actions: int = 0
    total_changes: int = 0


class CitizenOfflineService:
    def __init__(self, sync_service: PlatformSyncService | None = None) -> None:
        self._platform_sync = sync_service or PlatformSyncService()
        self._pending_actions: dict[str, list[OfflineAction]] = {}
        self._synced_actions: dict[str, list[OfflineAction]] = {}

    def queue_action(
        self, citizen_id: str, action_type: str, payload: dict[str, Any]
    ) -> OfflineAction:
        action = OfflineAction(
            id=f"off_{citizen_id}_{datetime.now(UTC).timestamp()}",
            citizen_id=citizen_id,
            action_type=action_type,
            payload=payload,
            timestamp=datetime.now(UTC).isoformat(),
        )
        if citizen_id not in self._pending_actions:
            self._pending_actions[citizen_id] = []
        self._pending_actions[citizen_id].append(action)
        return action

    def get_pending_actions(self, citizen_id: str) -> list[OfflineAction]:
        return self._pending_actions.get(citizen_id, [])

    def sync_pending_actions(self, citizen_id: str) -> SyncManifest:
        pending = self._pending_actions.get(citizen_id, [])
        synced: list[OfflineAction] = []
        failed: list[OfflineAction] = []

        for action in pending:
            try:
                change = SyncChange(
                    id=action.id,
                    entity_type=action.action_type,
                    entity_id=action.payload.get("entity_id", ""),
                    action="upsert",
                    data=action.payload,
                    timestamp=action.timestamp,
                )
                self._platform_sync.push_changes([change])
                action.synced = True
                synced.append(action)
            except Exception as exc:
                action.sync_error = str(exc)
                failed.append(action)
                logger.error("Offline sync failed for %s: %s", action.id, exc)

        if citizen_id not in self._synced_actions:
            self._synced_actions[citizen_id] = []
        self._synced_actions[citizen_id].extend(synced)
        self._pending_actions[citizen_id] = failed

        return SyncManifest(
            citizen_id=citizen_id,
            last_sync_at=datetime.now(UTC).isoformat(),
            pending_actions=len(failed),
            failed_actions=len(failed),
            total_changes=len(synced),
        )

    def get_sync_history(self, citizen_id: str) -> list[OfflineAction]:
        return self._synced_actions.get(citizen_id, [])

    def get_sync_status(self, citizen_id: str) -> dict[str, Any]:
        pending = len(self._pending_actions.get(citizen_id, []))
        synced = len(self._synced_actions.get(citizen_id, []))
        return {
            "citizen_id": citizen_id,
            "pending_actions": pending,
            "synced_actions": synced,
            "total_actions": pending + synced,
        }


class OfflineSyncEngine:
    def __init__(self, platform_sync: PlatformSyncService) -> None:
        self._platform_sync = platform_sync
        self._cache: dict[str, dict[str, Any]] = {}

    def cache_data(self, citizen_id: str, data_type: str, data: Any) -> None:
        key = f"{citizen_id}:{data_type}"
        self._cache[key] = {
            "data": data,
            "cached_at": datetime.now(UTC).isoformat(),
        }

    def get_cached_data(self, citizen_id: str, data_type: str) -> Any | None:
        key = f"{citizen_id}:{data_type}"
        entry = self._cache.get(key)
        if entry:
            return entry["data"]
        return None

    def invalidate_cache(self, citizen_id: str, data_type: str) -> bool:
        key = f"{citizen_id}:{data_type}"
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def pull_remote_changes(self, citizen_id: str, since: str | None = None) -> list[SyncChange]:
        return self._platform_sync.pull_changes(since=since)

    def resolve_conflict(
        self, local: SyncChange, remote: SyncChange
    ) -> SyncChange:
        return self._platform_sync.resolve_conflicts(local, remote)

    def get_data_freshness(self, citizen_id: str, data_type: str) -> str | None:
        key = f"{citizen_id}:{data_type}"
        entry = self._cache.get(key)
        if entry:
            return entry["cached_at"]
        return None
