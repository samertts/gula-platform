from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC

logger = logging.getLogger("gula.health_data.governance.lineage")


@dataclass
class LineageNode:
    id: str
    entity_type: str
    entity_id: str
    system: str
    timestamp: datetime
    operation: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class LineageEdge:
    source_id: str
    target_id: str
    transformation: str
    transformation_details: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataLineage:
    id: str
    entity_type: str
    entity_id: str
    nodes: list[LineageNode] = field(default_factory=list)
    edges: list[LineageEdge] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class LineageTracker:
    def __init__(self):
        self._lineages: dict[str, DataLineage] = {}

    def track(
        self,
        entity_type: str,
        entity_id: str,
        node: LineageNode,
        parent_node_id: str | None = None,
        transformation: str = "",
    ) -> DataLineage:
        key = f"{entity_type}:{entity_id}"
        if key not in self._lineages:
            self._lineages[key] = DataLineage(
                id=hashlib.sha256(key.encode()).hexdigest()[:16],
                entity_type=entity_type,
                entity_id=entity_id,
            )

        lineage = self._lineages[key]
        lineage.nodes.append(node)

        if parent_node_id:
            edge = LineageEdge(
                source_id=parent_node_id,
                target_id=node.id,
                transformation=transformation,
            )
            lineage.edges.append(edge)

        logger.debug("Lineage tracked: %s/%s via %s", entity_type, entity_id, node.operation)
        return lineage

    def get(self, entity_type: str, entity_id: str) -> DataLineage | None:
        return self._lineages.get(f"{entity_type}:{entity_id}")

    def get_upstream(self, entity_type: str, entity_id: str) -> list[LineageNode]:
        lineage = self.get(entity_type, entity_id)
        if not lineage:
            return []
        source_ids = {e.source_id for e in lineage.edges}
        return [n for n in lineage.nodes if n.id in source_ids]

    def get_downstream(self, entity_type: str, entity_id: str) -> list[LineageNode]:
        lineage = self.get(entity_type, entity_id)
        if not lineage:
            return []
        target_ids = {e.target_id for e in lineage.edges}
        return [n for n in lineage.nodes if n.id in target_ids]

    def list_by_type(self, entity_type: str) -> list[DataLineage]:
        return [v for k, v in self._lineages.items() if k.startswith(f"{entity_type}:")]
