from __future__ import annotations

import logging
import time

from app.integration.connector.spec import (
    ConnectorSpec,
    ConnectorStatus,
    ConnectorType,
)

logger = logging.getLogger("gula.integration.connector.registry")


class ConnectorRegistry:
    def __init__(self):
        self._connectors: dict[str, ConnectorSpec] = {}
        self._type_index: dict[str, list[str]] = {}
        self._tag_index: dict[str, list[str]] = {}

    def register(self, spec: ConnectorSpec) -> ConnectorSpec:
        spec.updated_at = time.time()
        self._connectors[spec.id] = spec

        self._type_index.setdefault(spec.connector_type.name.lower(), [])
        if spec.id not in self._type_index[spec.connector_type.name.lower()]:
            self._type_index[spec.connector_type.name.lower()].append(spec.id)

        for tag in spec.tags:
            self._tag_index.setdefault(tag, [])
            if spec.id not in self._tag_index[tag]:
                self._tag_index[tag].append(spec.id)

        logger.info(
            "Connector registered: %s (%s) [%s]",
            spec.name,
            spec.connector_type.name,
            spec.id,
        )
        return spec

    def unregister(self, connector_id: str) -> bool:
        spec = self._connectors.pop(connector_id, None)
        if spec is None:
            return False

        type_key = spec.connector_type.name.lower()
        if type_key in self._type_index and connector_id in self._type_index[type_key]:
            self._type_index[type_key].remove(connector_id)

        for tag in spec.tags:
            if tag in self._tag_index and connector_id in self._tag_index[tag]:
                self._tag_index[tag].remove(connector_id)

        logger.info("Connector unregistered: %s", connector_id)
        return True

    def get(self, connector_id: str) -> ConnectorSpec | None:
        return self._connectors.get(connector_id)

    def find_by_name(self, name: str) -> ConnectorSpec | None:
        for spec in self._connectors.values():
            if spec.name == name:
                return spec
        return None

    def list_by_type(self, connector_type: ConnectorType) -> list[ConnectorSpec]:
        type_key = connector_type.name.lower()
        ids = self._type_index.get(type_key, [])
        return [self._connectors[cid] for cid in ids if cid in self._connectors]

    def list_by_tag(self, tag: str) -> list[ConnectorSpec]:
        ids = self._tag_index.get(tag, [])
        return [self._connectors[cid] for cid in ids if cid in self._connectors]

    def list_all(self) -> list[ConnectorSpec]:
        return list(self._connectors.values())

    def list_active(self) -> list[ConnectorSpec]:
        return [
            s for s in self._connectors.values()
            if s.status == ConnectorStatus.ACTIVE
        ]

    def update_status(self, connector_id: str, status: ConnectorStatus) -> bool:
        spec = self._connectors.get(connector_id)
        if spec is None:
            return False
        spec.status = status
        spec.updated_at = time.time()
        logger.info(
            "Connector %s status updated: %s", connector_id, status.name,
        )
        return True

    def record_health(
        self, connector_id: str, status: str, latency_ms: float = 0.0,
    ) -> bool:
        spec = self._connectors.get(connector_id)
        if spec is None:
            return False
        spec.health.status = status
        spec.health.latency_ms = latency_ms
        spec.health.last_checked = time.time()
        spec.updated_at = time.time()
        return True

    def count(self) -> int:
        return len(self._connectors)

    def count_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for spec in self._connectors.values():
            key = spec.connector_type.name.lower()
            counts[key] = counts.get(key, 0) + 1
        return counts
