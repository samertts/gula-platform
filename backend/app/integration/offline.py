from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from backend.app.platform.sync import SyncChange, SyncService

logger = logging.getLogger("gula.integration.offline")


@dataclass
class OfflineQueueEntry:
    id: str = ""
    entity_type: str = ""
    entity_id: str = ""
    action: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    retry_count: int = 0
    max_retries: int = 5
    status: str = "pending"


class StoreForwardEngine:
    def __init__(self) -> None:
        self._queue: list[OfflineQueueEntry] = []
        self._processing = False

    def enqueue(self, entry: OfflineQueueEntry) -> None:
        self._queue.append(entry)
        logger.info("Offline entry enqueued: %s/%s", entry.entity_type, entry.action)

    def dequeue(self, count: int = 10) -> list[OfflineQueueEntry]:
        batch = [e for e in self._queue if e.status == "pending"][:count]
        for e in batch:
            e.status = "processing"
        return batch

    def mark_success(self, entry_id: str) -> None:
        for e in self._queue:
            if e.id == entry_id:
                e.status = "completed"
                break

    def mark_failed(self, entry_id: str, error: str) -> None:
        for e in self._queue:
            if e.id == entry_id:
                e.retry_count += 1
                if e.retry_count >= e.max_retries:
                    e.status = "dead"
                    logger.error("Offline entry dead: %s — %s", entry_id, error)
                else:
                    e.status = "pending"
                break

    def queue_size(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for e in self._queue:
            counts[e.status] += 1
        return dict(counts)

    def list_dead(self) -> list[OfflineQueueEntry]:
        return [e for e in self._queue if e.status == "dead"]


class ConflictResolver:
    def __init__(self, strategy: str = "last_write_wins") -> None:
        self._strategy = strategy

    def resolve(
        self,
        local: dict[str, Any],
        remote: dict[str, Any],
        version_local: int,
        version_remote: int,
    ) -> dict[str, Any]:
        if self._strategy == "last_write_wins":
            return remote if version_remote >= version_local else local
        if self._strategy == "first_write_wins":
            return local if version_local >= version_remote else remote
        if self._strategy == "merge":
            merged = dict(local)
            merged.update(remote)
            merged["_merged"] = True
            return merged
        if self._strategy == "manual":
            return {"_conflict": True, "local": local, "remote": remote}
        return remote


class DeltaSyncEngine:
    def __init__(self, sync_service: SyncService) -> None:
        self._sync = sync_service

    def compute_delta(self, local_version: int, remote_version: int, changes: list[SyncChange]) -> list[SyncChange]:
        return [c for c in changes if c.version > local_version and c.version <= remote_version]

    def push_delta(self, changes: list[SyncChange]) -> int:
        return self._sync.push_changes(changes)

    def pull_delta(self, since: str | None = None) -> list[SyncChange]:
        return self._sync.pull_changes(since)


class EdgeSyncEngine:
    def __init__(
        self,
        store_forward: StoreForwardEngine | None = None,
        conflict_resolver: ConflictResolver | None = None,
    ) -> None:
        self._store_forward = store_forward or StoreForwardEngine()
        self._conflict_resolver = conflict_resolver or ConflictResolver()
        self._edge_nodes: dict[str, dict[str, Any]] = {}
        self._last_sync: dict[str, float] = {}

    def register_edge_node(self, node_id: str, metadata: dict[str, Any] | None = None) -> None:
        self._edge_nodes[node_id] = metadata or {}
        logger.info("Edge node registered: %s", node_id)

    def unregister_edge_node(self, node_id: str) -> bool:
        if node_id in self._edge_nodes:
            del self._edge_nodes[node_id]
            self._last_sync.pop(node_id, None)
            logger.info("Edge node unregistered: %s", node_id)
            return True
        return False

    def sync_to_edge(self, node_id: str, data: list[dict[str, Any]]) -> dict[str, Any]:
        if node_id not in self._edge_nodes:
            return {"success": False, "error": f"Unknown edge node: {node_id}"}
        self._last_sync[node_id] = time.time()
        return {"success": True, "node_id": node_id, "records_synced": len(data)}

    def sync_from_edge(self, node_id: str, data: list[dict[str, Any]]) -> dict[str, Any]:
        if node_id not in self._edge_nodes:
            return {"success": False, "error": f"Unknown edge node: {node_id}"}
        for item in data:
            entry = OfflineQueueEntry(
                id=item.get("id", ""),
                entity_type=item.get("entity_type", "unknown"),
                entity_id=item.get("entity_id", ""),
                action=item.get("action", "sync"),
                payload=item.get("payload", {}),
                timestamp=time.time(),
            )
            self._store_forward.enqueue(entry)
        self._last_sync[node_id] = time.time()
        return {"success": True, "node_id": node_id, "records_received": len(data)}

    def get_edge_status(self, node_id: str | None = None) -> list[dict[str, Any]]:
        nodes = [node_id] if node_id else list(self._edge_nodes.keys())
        return [
            {
                "node_id": nid,
                "metadata": self._edge_nodes.get(nid, {}),
                "last_sync": self._last_sync.get(nid),
                "registered": True,
            }
            for nid in nodes if nid in self._edge_nodes
        ]


class OfflineSyncEngine:
    def __init__(
        self,
        sync_service: SyncService | None = None,
        store_forward: StoreForwardEngine | None = None,
        conflict_resolver: ConflictResolver | None = None,
        delta_sync: DeltaSyncEngine | None = None,
        edge_sync: EdgeSyncEngine | None = None,
    ) -> None:
        self._sync_service = sync_service or SyncService()
        self._store_forward = store_forward or StoreForwardEngine()
        self._conflict_resolver = conflict_resolver or ConflictResolver()
        self._delta_sync = delta_sync or DeltaSyncEngine(self._sync_service)
        self._edge_sync = edge_sync or EdgeSyncEngine(self._store_forward, self._conflict_resolver)

    @property
    def store_forward(self) -> StoreForwardEngine:
        return self._store_forward

    @property
    def conflict_resolver(self) -> ConflictResolver:
        return self._conflict_resolver

    @property
    def delta_sync(self) -> DeltaSyncEngine:
        return self._delta_sync

    @property
    def edge_sync(self) -> EdgeSyncEngine:
        return self._edge_sync

    async def sync_all(self) -> dict[str, Any]:
        batch = self._store_forward.dequeue(50)
        results: list[dict[str, Any]] = []
        for entry in batch:
            try:
                change = SyncChange(
                    id=entry.id,
                    entity_type=entry.entity_type,
                    entity_id=entry.entity_id,
                    action=entry.action,
                    data=entry.payload,
                    version=1,
                    timestamp=str(entry.timestamp),
                )
                self._delta_sync.push_delta([change])
                self._store_forward.mark_success(entry.id)
                results.append({"id": entry.id, "status": "synced"})
            except Exception as exc:
                self._store_forward.mark_failed(entry.id, str(exc))
                results.append({"id": entry.id, "status": "failed", "error": str(exc)})
        return {
            "synced": sum(1 for r in results if r["status"] == "synced"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "results": results,
        }

    def get_status(self) -> dict[str, Any]:
        queue_status = self._store_forward.queue_size()
        sync_status = self._sync_service.get_sync_status()
        return {
            "queue": queue_status,
            "sync": sync_status,
            "edge_nodes": len(self._edge_sync._edge_nodes),
            "engine": "active",
        }
