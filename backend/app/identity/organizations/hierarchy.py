"""Generic organization / facility hierarchy service.

The hierarchy is an organizational graph over ``NIAMOrganization`` nodes linked
through ``parent_org_id``. The graph is deliberately *generic and
configurable*: a national deployment (Ministry → Directorate → Institution /
Hospital / PHC → Department → Unit / Service) is expressed as layer data, never
hard-coded country-specific values.

Capabilities
------------
* **Layer classification** — ``ORG_HIERARCHY_LAYERS`` maps an organization type
  to a generic hierarchy layer (deterministic, first-match wins).
* **Traversal** — ancestors (root-first) and descendants (deterministic order)
  with a cycle guard that raises ``OrganizationHierarchyError``.
* **Effective scope** — a node plus every descendant, resolved
  deterministically for scoped queries.
* **Cycle prevention** — ``set_parent`` refuses any reparent that would create
  a cycle or point at a missing / self node.
* **Auditability** — reparent and detach mutations are recorded through the
  identity audit service (hash-chained) when an ``AuditService`` is provided.

The graph logic lives in pure functions (``ancestor_ids``,
``descendant_ids``, ``would_create_cycle``, ...) so that correctness can be
verified without a database; the service is a thin async adapter that loads
nodes and records auditable mutations.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.models.audit import AuditAction
from app.identity.models.niam_organization import NIAMOrganization
from app.identity.services.audit_service import AuditService


@dataclass(frozen=True)
class HierarchyLayer:
    name: str
    label: str
    org_types: tuple[str, ...]


# Generic, country-agnostic hierarchy layers (national default). The layer
# registry is plain data: a deployment may extend or re-map org types without
# changing any code path. The ordering is significant: a lower index sits
# higher in the hierarchy.
ORG_HIERARCHY_LAYERS: tuple[HierarchyLayer, ...] = (
    HierarchyLayer(
        name="national",
        label="National / Ministry",
        org_types=("ministry",),
    ),
    HierarchyLayer(
        name="directorate",
        label="Directorate / Regional authority",
        org_types=("directorate",),
    ),
    HierarchyLayer(
        name="institution",
        label="Institution / Facility",
        org_types=(
            "government_hospital",
            "private_hospital",
            "primary_healthcare_sector",
            "health_center",
            "government_laboratory",
            "private_laboratory",
            "blood_bank",
            "forensic_medicine",
            "university",
            "research_center",
            "pharmacy",
            "medical_company",
        ),
    ),
    HierarchyLayer(name="department", label="Department", org_types=()),
    HierarchyLayer(name="unit", label="Unit / Service", org_types=()),
)

_UNCLASSIFIED_LAYER = "unclassified"


class OrganizationHierarchyError(Exception):
    """Raised when an organization hierarchy operation is invalid."""


@dataclass(frozen=True)
class OrgHierarchyNode:
    id: str
    org_id: str
    name_en: str
    name_ar: str
    org_type: str
    layer: str
    parent_id: str | None


def layer_name_for(org_type: str | None) -> str:
    """Return the generic hierarchy layer for an organization type."""
    if not org_type:
        return _UNCLASSIFIED_LAYER
    for layer in ORG_HIERARCHY_LAYERS:
        if org_type in layer.org_types:
            return layer.name
    return _UNCLASSIFIED_LAYER


def layer_index(layer_name: str) -> int:
    """Return the deterministic index of a layer (lower = higher in the graph)."""
    for index, layer in enumerate(ORG_HIERARCHY_LAYERS):
        if layer.name == layer_name:
            return index
    return len(ORG_HIERARCHY_LAYERS)


def ancestor_ids(parent_map: Mapping[str, str | None], start_id: str) -> list[str]:
    """Return the root-first ancestor chain of ``start_id`` (excluding itself).

    ``parent_map`` maps every node id to its parent id (``None`` for roots).

    Raises ``OrganizationHierarchyError`` on a cycle or a dangling parent.
    """
    if start_id not in parent_map:
        raise OrganizationHierarchyError(f"node_not_found: {start_id}")
    chain: list[str] = []
    visited = {start_id}
    cursor = parent_map[start_id]
    while cursor is not None:
        if cursor in visited:
            raise OrganizationHierarchyError("cycle_detected")
        if cursor not in parent_map:
            raise OrganizationHierarchyError(f"dangling_parent: {cursor}")
        visited.add(cursor)
        chain.append(cursor)
        cursor = parent_map[cursor]
    chain.reverse()
    return chain


def descendant_ids(
    children_map: Mapping[str, Sequence[str]],
    start_id: str,
) -> list[str]:
    """Return all descendant ids of ``start_id`` in deterministic BFS order.

    ``children_map`` maps a parent id to its child ids (the child ids are
    sorted by the caller for determinism). The result excludes ``start_id``
    itself and is cycle-guarded by a visited set.
    """
    descendants: list[str] = []
    visited = {start_id}
    frontier = list(children_map.get(start_id, []))
    while frontier:
        next_frontier: list[str] = []
        for child in frontier:
            if child in visited:
                continue
            visited.add(child)
            descendants.append(child)
            next_frontier.extend(children_map.get(child, ()))
        frontier = sorted(next_frontier)
    return descendants


def effective_scope_ids(start_id: str, descendant_id_list: Iterable[str]) -> list[str]:
    """Return ``start_id`` plus every descendant id, sorted deterministically."""
    return sorted([start_id, *descendant_id_list])


def would_create_cycle(
    parent_map: Mapping[str, str | None],
    org_id: str,
    new_parent_id: str,
) -> bool:
    """Return True when re-parenting ``org_id`` under ``new_parent_id`` would
    create a cycle.

    A dangling ``new_parent_id`` is *not* reported as a cycle here; the caller
    validates the parent exists before calling this check.
    """
    visited = {org_id}
    cursor = new_parent_id
    while cursor is not None:
        if cursor in visited:
            return True
        if cursor not in parent_map:
            return False
        visited.add(cursor)
        cursor = parent_map[cursor]
    return False


class OrganizationHierarchyService:
    """Async adapter over the organization hierarchy graph.

    ``audit`` is optional: when provided, every structural mutation is
    recorded through the hash-chained identity audit service.
    """

    def __init__(self, session: AsyncSession, audit: AuditService | None = None) -> None:
        self.session = session
        self.audit = audit

    async def get_organization(self, org_id: str) -> NIAMOrganization | None:
        stmt = select(NIAMOrganization).where(NIAMOrganization.id == org_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _require_organization(self, org_id: str) -> NIAMOrganization:
        org = await self.get_organization(org_id)
        if org is None:
            raise OrganizationHierarchyError(f"organization_not_found: {org_id}")
        return org

    async def get_ancestors(self, org_id: str) -> list[NIAMOrganization]:
        """Return the org's ancestor chain, root-first, excluding the org."""
        node = await self._require_organization(org_id)
        nodes: dict[str, NIAMOrganization] = {node.id: node}
        parent_map: dict[str, str | None] = {node.id: node.parent_org_id}
        current = node
        while current.parent_org_id is not None:
            if current.parent_org_id in nodes:
                raise OrganizationHierarchyError("cycle_detected")
            parent = await self._require_organization(current.parent_org_id)
            nodes[parent.id] = parent
            parent_map[parent.id] = parent.parent_org_id
            current = parent
        chain_ids = ancestor_ids(parent_map, org_id)
        return [nodes[node_id] for node_id in chain_ids]

    async def get_path(self, org_id: str) -> list[OrgHierarchyNode]:
        """Return the deterministic root-first path including the org itself."""
        node = await self._require_organization(org_id)
        ancestors = await self.get_ancestors(node.id)
        return [self._to_node(org) for org in ancestors] + [self._to_node(node)]

    @staticmethod
    def _to_node(org: NIAMOrganization) -> OrgHierarchyNode:
        return OrgHierarchyNode(
            id=org.id,
            org_id=org.org_id,
            name_en=org.name_en,
            name_ar=org.name_ar,
            org_type=org.org_type,
            layer=layer_name_for(org.org_type),
            parent_id=org.parent_org_id,
        )

    async def get_descendants(self, org_id: str) -> list[NIAMOrganization]:
        """Return all descendants in deterministic breadth-first order."""
        await self._require_organization(org_id)
        children_map: dict[str, list[str]] = {}
        descendants_by_id: dict[str, NIAMOrganization] = {}
        visited = {org_id}
        frontier = [org_id]
        while frontier:
            stmt = (
                select(NIAMOrganization)
                .where(NIAMOrganization.parent_org_id.in_(frontier))
                .order_by(NIAMOrganization.id)
            )
            result = await self.session.execute(stmt)
            level_children = list(result.scalars().all())
            level_by_id = {child.id: child for child in level_children}
            for parent_id in frontier:
                children_map[parent_id] = [
                    child.id for child in level_children if child.parent_org_id == parent_id
                ]
            next_frontier: list[str] = []
            for parent_id in frontier:
                for child_id in children_map[parent_id]:
                    if child_id in visited:
                        continue
                    visited.add(child_id)
                    descendants_by_id[child_id] = level_by_id[child_id]
                    next_frontier.append(child_id)
            frontier = sorted(next_frontier)
        descendant_id_list = descendant_ids(children_map, org_id)
        return [descendants_by_id[node_id] for node_id in descendant_id_list]

    async def get_effective_scope(self, org_id: str) -> list[str]:
        """Return the org id plus every descendant id, sorted deterministically."""
        await self._require_organization(org_id)
        descendants = await self.get_descendants(org_id)
        return effective_scope_ids(org_id, [node.id for node in descendants])

    async def set_parent(
        self,
        org_id: str,
        new_parent_id: str,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> NIAMOrganization:
        """Re-parent ``org_id`` under ``new_parent_id`` (audited).

        Refuses self-parenting, missing nodes, and any reparent that would
        create a cycle.
        """
        org = await self._require_organization(org_id)
        parent = await self._require_organization(new_parent_id)
        if new_parent_id == org.id:
            raise OrganizationHierarchyError("self_parent")
        parent_map: dict[str, str | None] = {org.id: org.parent_org_id}
        for ancestor in await self.get_ancestors(org.id):
            parent_map[ancestor.id] = ancestor.parent_org_id
        for ancestor in await self.get_ancestors(parent.id):
            parent_map[ancestor.id] = ancestor.parent_org_id
        parent_map[parent.id] = parent.parent_org_id
        if would_create_cycle(parent_map, org.id, parent.id):
            raise OrganizationHierarchyError("cycle_detected")

        previous = org.parent_org_id
        org.parent_org_id = parent.id
        if self.audit is not None:
            await self.audit.record(
                AuditAction.organization_hierarchy_changed,
                actor_id=actor_id,
                target_type="organization",
                target_id=org.id,
                changes={"parent_org_id": {"from": previous, "to": parent.id}},
                metadata={
                    "parent_name": parent.name_en,
                    "parent_type": parent.org_type,
                    "reason": reason,
                },
                organization_id=org.id,
            )
        return org

    async def detach(
        self,
        org_id: str,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> NIAMOrganization:
        """Make ``org_id`` a root node by clearing its parent (audited)."""
        org = await self._require_organization(org_id)
        previous = org.parent_org_id
        if previous is None:
            return org
        org.parent_org_id = None
        if self.audit is not None:
            await self.audit.record(
                AuditAction.organization_hierarchy_changed,
                actor_id=actor_id,
                target_type="organization",
                target_id=org.id,
                changes={"parent_org_id": {"from": previous, "to": None}},
                metadata={"reason": reason},
                organization_id=org.id,
            )
        return org

    async def validate_layer_ordering(self, org_id: str) -> list[str]:
        """Return advisory warnings when a node's layer sits above its parent's.

        Deterministic and non-blocking: hierarchy integrity never depends on
        layer ordering because the graph is generic and country-agnostic.
        """
        warnings: list[str] = []
        node = await self._require_organization(org_id)
        current = node
        while current.parent_org_id is not None:
            parent = await self._require_organization(current.parent_org_id)
            child_layer = layer_name_for(current.org_type)
            parent_layer = layer_name_for(parent.org_type)
            if (
                child_layer != _UNCLASSIFIED_LAYER
                and parent_layer != _UNCLASSIFIED_LAYER
                and layer_index(child_layer) < layer_index(parent_layer)
            ):
                warnings.append(
                    f"organization {current.org_id} ({child_layer}) is above "
                    f"parent {parent.org_id} ({parent_layer})"
                )
            current = parent
        return warnings
