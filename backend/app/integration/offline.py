from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from app.platform.sync import SyncChange, SyncService
from app.services.offline_sync_service import is_clinical_entity

logger = logging.getLogger("gula.integration.offline")

_SUPPORTED_STRATEGIES = frozenset(
    {"last_write_wins", "first_write_wins", "merge", "manual"}
)


def _fingerprint(entry: OfflineQueueEntry) -> str:
    payload = json.dumps(entry.payload, sort_keys=True, default=str)
    return hashlib.sha256(
        f"{entry.id}:{entry.entity_id}:{entry.action}:{payload}".encode()
    ).hexdigest()


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

    def enqueue(self, entry: OfflineQueueEntry) -> bool:
        fingerprint = _fingerprint(entry)
        for existing in self._queue:
            if existing.id == entry.id and _fingerprint(existing) == fingerprint:
                logger.info("Offline duplicate suppressed: %s", entry.id)
                return False
        self._queue.append(entry)
        logger.info("Offline entry enqueued: %s/%s", entry.entity_type, entry.action)
        return True

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

    def force_dead(self, entry_id: str, reason: str) -> bool:
        """Move a bounded synthetic queue entry to dead state after retry exhaustion."""
        for entry in self._queue:
            if entry.id == entry_id:
                entry.status = "dead"
                logger.error("Offline entry dead after bounded retries: %s — %s", entry_id, reason)
                return True
        return False

    def queue_size(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for e in self._queue:
            counts[e.status] += 1
        return dict(counts)

    def list_dead(self) -> list[OfflineQueueEntry]:
        return [e for e in self._queue if e.status == "dead"]

    def snapshot(self) -> tuple[dict[str, Any], ...]:
        """Return a bounded, JSON-safe recovery snapshot of the queue.

        This is an additive, process-local recovery contract for synthetic
        workflows. It is not a database, audit authority, or durable store.
        """

        return tuple(
            {
                "id": entry.id,
                "entity_type": entry.entity_type,
                "entity_id": entry.entity_id,
                "action": entry.action,
                "payload": dict(entry.payload),
                "timestamp": entry.timestamp,
                "retry_count": entry.retry_count,
                "max_retries": entry.max_retries,
                "status": entry.status,
            }
            for entry in self._queue
        )

    def restore(self, snapshot: Sequence[Mapping[str, Any]]) -> None:
        """Restore a previously exported synthetic queue snapshot in place."""

        restored: list[OfflineQueueEntry] = []
        seen: set[str] = set()
        for item in snapshot:
            identifier = str(item.get("id", ""))
            if not identifier or len(identifier) > 200 or identifier in seen:
                raise ValueError("offline recovery snapshot has an invalid or duplicate entry id")
            seen.add(identifier)
            status = str(item.get("status", "pending"))
            if status not in {"pending", "processing", "completed", "failed", "dead"}:
                raise ValueError("offline recovery snapshot has an unsupported status")
            retry_count = int(item.get("retry_count", 0))
            max_retries = int(item.get("max_retries", 5))
            if retry_count < 0 or max_retries < 1 or retry_count > max_retries:
                raise ValueError("offline recovery snapshot has invalid retry state")
            entry = OfflineQueueEntry(
                id=identifier,
                entity_type=str(item.get("entity_type", "")),
                entity_id=str(item.get("entity_id", "")),
                action=str(item.get("action", "sync")),
                payload=dict(item.get("payload", {})),
                timestamp=float(item.get("timestamp", 0.0)),
                retry_count=retry_count,
                max_retries=max_retries,
                status=status,
            )
            if status == "processing":
                entry.status = "pending"
            restored.append(entry)
        self._queue = restored


class ConflictResolver:
    def __init__(self, strategy: str = "manual") -> None:
        if strategy not in _SUPPORTED_STRATEGIES:
            raise ValueError(f"unsupported offline conflict strategy: {strategy}")
        self._strategy = strategy

    def resolve(
        self,
        local: dict[str, Any],
        remote: dict[str, Any],
        version_local: int,
        version_remote: int,
        entity_type: str = "unknown",
        timestamp_local: float = 0.0,
        timestamp_remote: float = 0.0,
    ) -> dict[str, Any]:
        envelope = {
            "_conflict": True,
            "entity_type": entity_type,
            "local": local,
            "remote": remote,
            "version_local": version_local,
            "version_remote": version_remote,
            "timestamp_local": timestamp_local,
            "timestamp_remote": timestamp_remote,
        }

        if is_clinical_entity(entity_type) and self._strategy != "manual":
            logger.warning(
                "Rejected automatic clinical conflict resolution for %s with strategy %s",
                entity_type,
                self._strategy,
            )
            return {**envelope, "reason": "automatic clinical resolution not authorized"}

        if version_local == version_remote:
            return {**envelope, "reason": "equal versions require manual review"}

        if self._strategy == "last_write_wins":
            return remote if version_remote > version_local else local
        if self._strategy == "first_write_wins":
            return local if version_local > version_remote else remote
        if self._strategy == "merge":
            merged = dict(local)
            merged.update(remote)
            merged["_merged"] = True
            return merged
        return envelope


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
        self._processed: set[tuple[str, str]] = set()

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

    async def sync_all(
        self,
        *,
        eligible: Callable[[OfflineQueueEntry], bool] | None = None,
    ) -> dict[str, Any]:
        batch = self._store_forward.dequeue(50)
        if eligible is not None:
            accepted = [entry for entry in batch if eligible(entry)]
            rejected = [entry for entry in batch if not eligible(entry)]
            for entry in rejected:
                entry.status = "pending"
            batch = accepted
        results: list[dict[str, Any]] = []
        for entry in batch:
            fingerprint = _fingerprint(entry)
            marker = (entry.id, fingerprint)
            if marker in self._processed:
                self._store_forward.mark_success(entry.id)
                results.append({"id": entry.id, "status": "duplicate"})
                continue
            try:
                change = SyncChange(
                    id=entry.id,
                    entity_type=entry.entity_type,
                    entity_id=entry.entity_id,
                    action=entry.action,
                    data=entry.payload,
                    version=int(entry.payload.get("version", 1)),
                    timestamp=str(entry.timestamp),
                )
                self._delta_sync.push_delta([change])
                self._store_forward.mark_success(entry.id)
                self._processed.add(marker)
                results.append({"id": entry.id, "status": "synced"})
            except Exception as exc:
                self._store_forward.mark_failed(entry.id, str(exc))
                results.append({"id": entry.id, "status": "failed", "error": str(exc)})
        return {
            "synced": sum(1 for r in results if r["status"] == "synced"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "duplicates": sum(1 for r in results if r["status"] == "duplicate"),
            "results": results,
        }

    def get_status(self) -> dict[str, Any]:
        queue_status = self._store_forward.queue_size()
        sync_status = self._sync_service.get_sync_status()
        return {
            "queue": queue_status,
            "conflicts": queue_status.get("conflict", 0),
            "sync": sync_status,
            "edge_nodes": len(self._edge_sync._edge_nodes),
            "engine": "active",
        }

    def recovery_snapshot(self) -> dict[str, Any]:
        """Return bounded synthetic recovery state for the queue and dedupe set."""

        return {
            "queue": list(self._store_forward.snapshot()),
            "processed": [
                {"id": identifier, "fingerprint": fingerprint}
                for identifier, fingerprint in sorted(self._processed)
            ],
        }

    def restore_recovery_snapshot(self, snapshot: Mapping[str, Any]) -> None:
        """Restore queue and dedupe markers from a bounded synthetic snapshot."""

        queue = snapshot.get("queue", [])
        if not isinstance(queue, Sequence) or isinstance(queue, (str, bytes)):
            raise ValueError("offline recovery snapshot queue must be a sequence")
        self._store_forward.restore(queue)
        processed = snapshot.get("processed", [])
        if not isinstance(processed, Sequence) or isinstance(processed, (str, bytes)):
            raise ValueError("offline recovery snapshot processed set must be a sequence")
        restored: set[tuple[str, str]] = set()
        for item in processed:
            identifier = str(item.get("id", ""))
            fingerprint = str(item.get("fingerprint", ""))
            if not identifier or not fingerprint:
                raise ValueError("offline recovery snapshot has an incomplete dedupe marker")
            restored.add((identifier, fingerprint))
        self._processed = restored
