"""Small, dependency-free security policy helpers.

These helpers encode platform-owned invariants inspired by relationship-based
authorization and identity/audit patterns from public security projects. They
do not import or copy implementation code from external projects.
"""

from __future__ import annotations

import re
import uuid

from shared.rbac import get_permissions_for_role

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_COLLECTION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


def sanitize_request_id(value: str | None) -> str:
    """Accept only bounded log-safe request IDs; replace everything else."""
    candidate = (value or "").strip()
    if _REQUEST_ID_RE.fullmatch(candidate):
        return candidate
    return str(uuid.uuid4())


def normalize_collection_name(value: str | None) -> str:
    """Return a bounded, non-path-like collection key for tenant namespaces."""
    candidate = (value or "default").strip()
    if not _COLLECTION_RE.fullmatch(candidate):
        raise ValueError("collection must contain only letters, digits, '.', '_' or '-'")
    return candidate


def tenant_collection_key(current_user, requested: str | None) -> str:
    """Namespace AI/RAG collections by lab, never by caller-controlled lab IDs.

    Platform administrators without a lab use an explicit platform namespace;
    all other institutional users are forced into their own lab namespace.
    """
    collection = normalize_collection_name(requested)
    lab_id = getattr(current_user, "lab_id", None)
    if lab_id is not None:
        return f"lab:{int(lab_id)}:{collection}"

    role = getattr(current_user, "role", "")
    if "system:admin" not in get_permissions_for_role(role):
        raise PermissionError("A tenant context is required for this operation")
    return f"platform:{collection}"
