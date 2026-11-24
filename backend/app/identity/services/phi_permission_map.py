"""B1 — centralized, explicit per-action PHI permission map.

Owner directive GULA-MASTER-AUTH-2026-11-19 §5/B1 requires one authoritative
map for Protected Health Information actions. This module is that map. It is a
*policy table*, not an authorization engine: the resulting permission key is
enforced by the canonical ``AuthorizationDecisionService`` through the existing
``RolePermissionService`` / RBAC catalog.

Design properties:

* read / create / update / delete / export / print / share / administrative are
  distinct actions with distinct permission keys; a broad permission can never
  imply an unrelated PHI operation;
* unmapped resource/action pairs resolve to ``None`` so callers fail closed;
* the canonical key format ``<resource>.<action>`` matches the seeded NIAM
  permission catalog (e.g. ``lab_result.read``, ``patient_record.export``).
"""

from __future__ import annotations

from enum import StrEnum


class PhiAction(StrEnum):
    read = "read"
    create = "create"
    update = "update"
    delete = "delete"
    export = "export"
    print = "print"
    share = "share"
    administer = "administrative"


# Resource types that carry PHI in the canonical NIAM authorization model.
PHI_RESOURCE_TYPES = frozenset(
    {
        "patient_record",
        "lab_result",
        "lab_order",
        "sample",
        "encounter",
        "clinical_note",
        "diagnostic_report",
        "imaging_study",
        "prescription",
        "medication",
        "immunization",
        "allergy",
        "care_plan",
        "document",
    }
)

# Explicit, centralized action registry. Every PHI resource supports exactly the
# same eight actions; no implicit inheritance between them. A "delete" action is
# intentionally distinct from "update": erasure/soft-delete of PHI is a separate
# high-risk operation that must never be granted by an update permission.
PHI_ACTIONS = frozenset(action.value for action in PhiAction)
# Accept the conventional "administer" token as an alias for "administrative".
_ACTION_ALIASES = {"administer": PhiAction.administer.value}


class PhiPermissionUnresolved(ValueError):
    """No explicit permission is defined for the requested PHI action."""


def canonical_phi_action(action: str) -> str | None:
    """Return the canonical action token, or None when the action is unmapped."""
    if not isinstance(action, str):
        return None
    candidate = action.strip().lower()
    candidate = _ACTION_ALIASES.get(candidate, candidate)
    return candidate if candidate in PHI_ACTIONS else None


def resolve_phi_permission(resource_type: str, action: str) -> str | None:
    """Return the exact permission key for a PHI action; None means fail closed.

    The caller must deny when this returns None for a PHI resource. Non-PHI
    resources return None so their existing authorization path is unchanged.
    """
    if resource_type not in PHI_RESOURCE_TYPES:
        return None
    canonical_action = canonical_phi_action(action)
    if canonical_action is None:
        return None
    return f"{resource_type}.{canonical_action}"


def require_phi_permission(resource_type: str, action: str) -> str:
    """Strict variant used by policy tooling; raises instead of returning None."""
    permission = resolve_phi_permission(resource_type, action)
    if permission is None:
        raise PhiPermissionUnresolved(f"{resource_type}.{action}")
    return permission
