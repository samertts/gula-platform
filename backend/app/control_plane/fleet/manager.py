from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC

logger = logging.getLogger("gula.control_plane.fleet.manager")


@dataclass
class NodeDescriptor:
    node_id: str
    hostname: str
    ip_address: str
    role: str = "worker"
    status: str = "registered"
    labels: dict[str, str] = field(default_factory=dict)
    resources: dict[str, Any] = field(default_factory=dict)
    last_heartbeat: str | None = None
    registered_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class ContainerDescriptor:
    container_id: str
    node_id: str
    image: str
    name: str
    status: str = "created"
    ports: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    started_at: str | None = None


@dataclass
class EdgeDeviceDescriptor:
    device_id: str
    node_id: str
    model: str
    firmware_version: str = ""
    status: str = "registered"
    capabilities: list[str] = field(default_factory=list)
    last_seen: str | None = None
    registered_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class FleetManager:
    _instance: FleetManager | None = None

    def __init__(self):
        if FleetManager._instance is not None:
            raise RuntimeError("FleetManager is a singleton.")
        self._nodes: dict[str, NodeDescriptor] = {}
        self._containers: dict[str, ContainerDescriptor] = {}
        self._edge_devices: dict[str, EdgeDeviceDescriptor] = {}
        FleetManager._instance = self

    @classmethod
    def get_instance(cls) -> FleetManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_node(self, node: NodeDescriptor) -> None:
        self._nodes[node.node_id] = node
        logger.info("Node registered: %s (%s)", node.node_id, node.hostname)

    def unregister_node(self, node_id: str) -> None:
        self._nodes.pop(node_id, None)
        self._containers = {k: v for k, v in self._containers.items() if v.node_id != node_id}
        self._edge_devices = {k: v for k, v in self._edge_devices.items() if v.node_id != node_id}
        logger.info("Node unregistered: %s", node_id)

    def get_node(self, node_id: str) -> NodeDescriptor | None:
        return self._nodes.get(node_id)

    def list_nodes(self, role: str | None = None) -> list[NodeDescriptor]:
        if role:
            return [n for n in self._nodes.values() if n.role == role]
        return list(self._nodes.values())

    def heartbeat(self, node_id: str, resources: dict[str, Any] | None = None) -> bool:
        node = self._nodes.get(node_id)
        if not node:
            return False
        node.last_heartbeat = datetime.now(UTC).isoformat()
        if resources:
            node.resources.update(resources)
        return True

    def get_stale_nodes(self, timeout_seconds: int = 120) -> list[NodeDescriptor]:
        now = datetime.now(UTC)
        stale: list[NodeDescriptor] = []
        for node in self._nodes.values():
            if node.last_heartbeat:
                hb_time = datetime.fromisoformat(node.last_heartbeat)
                if (now - hb_time).total_seconds() > timeout_seconds:
                    stale.append(node)
        return stale

    def register_container(self, container: ContainerDescriptor) -> None:
        self._containers[container.container_id] = container

    def list_containers(self, node_id: str | None = None) -> list[ContainerDescriptor]:
        if node_id:
            return [c for c in self._containers.values() if c.node_id == node_id]
        return list(self._containers.values())

    def register_edge_device(self, device: EdgeDeviceDescriptor) -> None:
        self._edge_devices[device.device_id] = device

    def list_edge_devices(self, node_id: str | None = None) -> list[EdgeDeviceDescriptor]:
        if node_id:
            return [d for d in self._edge_devices.values() if d.node_id == node_id]
        return list(self._edge_devices.values())

    def summary(self) -> dict[str, Any]:
        return {
            "nodes": len(self._nodes),
            "containers": len(self._containers),
            "edge_devices": len(self._edge_devices),
            "stale_nodes": len(self.get_stale_nodes()),
        }
