from __future__ import annotations

import json
import logging
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.kernel import Kernel

logger = logging.getLogger("gula.kernel.runtime_digital_twin")


@dataclass
class TwinEntity:
    id: str
    type: str
    name: str
    status: str = "unknown"
    properties: dict[str, Any] = field(default_factory=dict)
    relationships: dict[str, list[str]] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    version: int = 1

    def update(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ("id", "created_at", "version"):
                setattr(self, key, value)
        self.updated_at = time.time()
        self.version += 1

    def add_relationship(self, rel_type: str, target_id: str) -> None:
        if rel_type not in self.relationships:
            self.relationships[rel_type] = []
        if target_id not in self.relationships[rel_type]:
            self.relationships[rel_type].append(target_id)

    def remove_relationship(self, rel_type: str, target_id: str) -> bool:
        if rel_type in self.relationships and target_id in self.relationships[rel_type]:
            self.relationships[rel_type].remove(target_id)
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "status": self.status,
            "properties": self.properties,
            "relationships": self.relationships,
            "metrics": self.metrics,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
        }


@dataclass
class TwinSnapshot:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entities: dict[str, TwinEntity] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    entity_count: int = 0
    relationships_count: int = 0


class TwinStore:
    def __init__(self, store_dir: str = "/var/lib/gula/kernel/twin"):
        self._store_dir = Path(store_dir)
        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._snapshots: deque[TwinSnapshot] = deque(maxlen=50)

    def save_snapshot(self, snapshot: TwinSnapshot) -> str:
        filepath = self._store_dir / f"twin_{snapshot.id}.json"
        data = {
            "id": snapshot.id,
            "timestamp": snapshot.timestamp,
            "entities": {eid: ent.to_dict() for eid, ent in snapshot.entities.items()},
            "entity_count": snapshot.entity_count,
            "relationships_count": snapshot.relationships_count,
        }
        filepath.write_text(json.dumps(data, indent=2))
        self._snapshots.append(snapshot)
        logger.info(
            "Twin snapshot saved", extra={"path": str(filepath), "entities": snapshot.entity_count},
        )
        return str(filepath)

    def load_snapshot(self, snapshot_id: str) -> TwinSnapshot | None:
        filepath = self._store_dir / f"twin_{snapshot_id}.json"
        if not filepath.exists():
            return None
        try:
            data = json.loads(filepath.read_text())
            entities = {}
            for eid, edata in data.get("entities", {}).items():
                entities[eid] = TwinEntity(**edata)
            return TwinSnapshot(
                id=data["id"],
                timestamp=data["timestamp"],
                entities=entities,
                entity_count=data["entity_count"],
                relationships_count=data["relationships_count"],
            )
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.error(
                "Snapshot load failed", extra={"snapshot_id": snapshot_id, "error": str(exc)},
            )
            return None

    def list_snapshots(self) -> list[dict[str, Any]]:
        return [
            {"id": s.id, "timestamp": s.timestamp, "entities": s.entity_count}
            for s in self._snapshots
        ]


class TwinQuery:
    def __init__(self, twin: RuntimeDigitalTwin):
        self._twin = twin

    def find_by_type(self, entity_type: str) -> list[TwinEntity]:
        return [e for e in self._twin._entities.values() if e.type == entity_type]

    def find_by_tag(self, tag: str) -> list[TwinEntity]:
        return [e for e in self._twin._entities.values() if tag in e.tags]

    def find_by_status(self, status: str) -> list[TwinEntity]:
        return [e for e in self._twin._entities.values() if e.status == status]

    def find_by_property(self, key: str, value: Any) -> list[TwinEntity]:
        return [e for e in self._twin._entities.values() if e.properties.get(key) == value]

    def find_by_name(self, name: str) -> list[TwinEntity]:
        return [e for e in self._twin._entities.values() if e.name == name]

    def get_related(self, entity_id: str, rel_type: str | None = None) -> list[TwinEntity]:
        entity = self._twin._entities.get(entity_id)
        if not entity:
            return []
        related_ids: set[str] = set()
        for rtype, targets in entity.relationships.items():
            if rel_type is None or rtype == rel_type:
                related_ids.update(targets)
        return [self._twin._entities[eid] for eid in related_ids if eid in self._twin._entities]

    def count_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for e in self._twin._entities.values():
            counts[e.type] += 1
        return dict(counts)

    def search(self, query: str) -> list[TwinEntity]:
        q = query.lower()
        return [
            e
            for e in self._twin._entities.values()
            if q in e.name.lower() or q in e.type.lower() or any(q in t.lower() for t in e.tags)
        ]


class RuntimeDigitalTwin:
    def __init__(self, kernel: Kernel | None = None):
        self._kernel = kernel
        self._entities: dict[str, TwinEntity] = {}
        self._store = TwinStore()
        self._query = TwinQuery(self)
        self._update_count: int = 0
        self._last_snapshot: float = 0.0
        self._sync_interval: float = 60.0

    @property
    def query(self) -> TwinQuery:
        return self._query

    def register_entity(
        self,
        entity_id: str,
        entity_type: str,
        name: str,
        status: str = "unknown",
        properties: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> TwinEntity:
        if entity_id in self._entities:
            logger.warning(
                "Entity already registered, updating", extra={"id": entity_id, "type": entity_type},
            )
        entity = TwinEntity(
            id=entity_id,
            type=entity_type,
            name=name,
            status=status,
            properties=properties or {},
            tags=tags or [],
        )
        self._entities[entity_id] = entity
        self._update_count += 1
        logger.info("Entity registered", extra={"id": entity_id, "type": entity_type, "name": name})
        return entity

    def update_entity(self, entity_id: str, **kwargs: Any) -> bool:
        entity = self._entities.get(entity_id)
        if not entity:
            return False
        entity.update(**kwargs)
        self._update_count += 1
        return True

    def remove_entity(self, entity_id: str) -> bool:
        if entity_id in self._entities:
            del self._entities[entity_id]
            for e in self._entities.values():
                for rels in e.relationships.values():
                    if entity_id in rels:
                        rels.remove(entity_id)
            self._update_count += 1
            return True
        return False

    def get_entity(self, entity_id: str) -> TwinEntity | None:
        return self._entities.get(entity_id)

    def list_entities(self) -> list[TwinEntity]:
        return list(self._entities.values())

    def add_relationship(self, source_id: str, rel_type: str, target_id: str) -> bool:
        source = self._entities.get(source_id)
        target = self._entities.get(target_id)
        if not source or not target:
            return False
        source.add_relationship(rel_type, target_id)
        target.add_relationship(f"inverse_{rel_type}", source_id)
        self._update_count += 1
        return True

    def snapshot(self) -> TwinSnapshot:
        snapshot = TwinSnapshot(
            entities=dict(self._entities),
            entity_count=len(self._entities),
            relationships_count=sum(
                len(rels) for e in self._entities.values() for rels in e.relationships.values()
            ),
        )
        self._last_snapshot = time.time()
        return snapshot

    def persist_snapshot(self) -> str:
        snapshot = self.snapshot()
        return self._store.save_snapshot(snapshot)

    def get_snapshot_data(self) -> dict[str, Any]:
        return {
            "timestamp": time.time(),
            "entities": {eid: ent.to_dict() for eid, ent in self._entities.items()},
            "entity_count": len(self._entities),
            "relationships_count": sum(
                len(rels) for e in self._entities.values() for rels in e.relationships.values()
            ),
            "update_count": self._update_count,
        }

    def get_stats(self) -> dict[str, Any]:
        type_counts = self._query.count_by_type()
        status_counts: dict[str, int] = defaultdict(int)
        for e in self._entities.values():
            status_counts[e.status] += 1
        return {
            "total_entities": len(self._entities),
            "by_type": type_counts,
            "by_status": dict(status_counts),
            "update_count": self._update_count,
            "snapshots_stored": len(self._store._snapshots),
        }
