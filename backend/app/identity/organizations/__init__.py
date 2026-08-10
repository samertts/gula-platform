"""Organization administration guard — PROGRAM-STABLE-003 Phase 3.

Enforces zero cross-domain administration: organization owners may only
administer the organization they belong to. Reusable by any identity
administrative surface.
"""

from __future__ import annotations

from app.identity.organizations.guard import (
    OrganizationAccessDecision,
    OrganizationAccessDeniedError,
    OrganizationAccessGuard,
)
from app.identity.organizations.hierarchy import (
    ORG_HIERARCHY_LAYERS,
    HierarchyLayer,
    OrganizationHierarchyError,
    OrganizationHierarchyService,
    OrgHierarchyNode,
    ancestor_ids,
    descendant_ids,
    effective_scope_ids,
    layer_index,
    layer_name_for,
    would_create_cycle,
)

__all__ = [
    "ORG_HIERARCHY_LAYERS",
    "HierarchyLayer",
    "OrgHierarchyNode",
    "OrganizationAccessDecision",
    "OrganizationAccessDeniedError",
    "OrganizationAccessGuard",
    "OrganizationHierarchyError",
    "OrganizationHierarchyService",
    "ancestor_ids",
    "descendant_ids",
    "effective_scope_ids",
    "layer_index",
    "layer_name_for",
    "would_create_cycle",
]
