from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.control_plane.enums import TenantLevel
from app.kernel.integration import get_kernel
from app.kernel.tenant.registry import TenantRegistry
from app.kernel.types import TenantDescriptor

logger = logging.getLogger("gula.control_plane.multi_tenant")


@dataclass
class TenantNode:
    id: str
    name: str
    level: TenantLevel
    parent_id: str | None = None
    children: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class MultiTenantController:
    _instance: MultiTenantController | None = None

    def __init__(self):
        if MultiTenantController._instance is not None:
            raise RuntimeError("MultiTenantController is a singleton.")
        self._nodes: dict[str, TenantNode] = {}
        self._level_order = [
            TenantLevel.NATIONAL,
            TenantLevel.MINISTRY,
            TenantLevel.DIRECTORATE,
            TenantLevel.HOSPITAL,
            TenantLevel.LABORATORY,
            TenantLevel.DEPARTMENT,
        ]
        MultiTenantController._instance = self

    @classmethod
    def get_instance(cls) -> MultiTenantController:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_kernel_tenant(self) -> TenantRegistry | None:
        kernel = get_kernel()
        return kernel.get_component("tenant_registry")

    def register_tenant(
        self,
        tenant_id: str,
        name: str,
        level: TenantLevel,
        parent_id: str | None = None,
        config: dict | None = None,
    ) -> TenantNode:
        node = TenantNode(
            id=tenant_id,
            name=name,
            level=level,
            parent_id=parent_id,
            config=config or {},
        )
        self._nodes[tenant_id] = node

        if parent_id and parent_id in self._nodes:
            self._nodes[parent_id].children.append(tenant_id)

        tr = self._get_kernel_tenant()
        if tr:
            td = TenantDescriptor(id=tenant_id, name=name, slug=name.lower().replace(" ", "-"))
            tr.register(td)

        logger.info(
            "Tenant registered: %s (%s) under %s", tenant_id, level.value, parent_id or "root",
        )
        return node

    def get_tenant(self, tenant_id: str) -> TenantNode | None:
        return self._nodes.get(tenant_id)

    def list_tenants(self, level: TenantLevel | None = None) -> list[TenantNode]:
        if level:
            return [n for n in self._nodes.values() if n.level == level]
        return list(self._nodes.values())

    def get_children(self, tenant_id: str) -> list[TenantNode]:
        node = self._nodes.get(tenant_id)
        if not node:
            return []
        return [self._nodes[cid] for cid in node.children if cid in self._nodes]

    def get_ancestors(self, tenant_id: str) -> list[TenantNode]:
        ancestors: list[TenantNode] = []
        node = self._nodes.get(tenant_id)
        while node and node.parent_id:
            parent = self._nodes.get(node.parent_id)
            if parent:
                ancestors.append(parent)
                node = parent
            else:
                break
        return ancestors

    def get_hierarchy(self, tenant_id: str) -> list[dict[str, Any]]:
        node = self._nodes.get(tenant_id)
        if not node:
            return []
        result = [{"id": node.id, "name": node.name, "level": node.level.value}]
        for child_id in node.children:
            child_node = self._nodes.get(child_id)
            if child_node:
                result.append(
                    {"id": child_node.id, "name": child_node.name, "level": child_node.level.value},
                )
        return result

    def tenant_isolation_policy(self, tenant_id: str) -> dict[str, Any]:
        kernel = get_kernel()
        tr = kernel.get_component("tenant_registry")
        isolation_info = {}
        if tr and tr.isolation:
            isolation_info = {"strategy": "schema", "isolated": True}
        node = self._nodes.get(tenant_id)
        return {
            "tenant_id": tenant_id,
            "level": node.level.value if node else "unknown",
            "parent_id": node.parent_id if node else None,
            "isolation": isolation_info,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "total": len(self._nodes),
            "by_level": {
                level.value: sum(1 for n in self._nodes.values() if n.level == level)
                for level in TenantLevel
            },
            "root_count": sum(1 for n in self._nodes.values() if n.parent_id is None),
        }
