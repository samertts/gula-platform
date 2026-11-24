"""Runtime RBAC/ABAC authorization for the synthetic Health Core slice.

This package closes review finding F-02: declared boundaries become enforced
boundaries. It is intentionally isolated — no FastAPI router, no production
wiring, no database and no real identity. All identifiers remain opaque ``SYN-``.
"""

from __future__ import annotations

from app.health_core.authorization.audit import (
    GENESIS_HASH,
    AuditRecord,
    AuditVerification,
    AuthorizationAuditLog,
    compute_record_hash,
    verify_audit_chain,
)
from app.health_core.authorization.engine import (
    REVOCATION_POLICY_BY_SCOPE,
    ROLE_PERMISSIONS,
    AuthorizationEngine,
    Grant,
    Revocation,
    RevocationScope,
)
from app.health_core.authorization.errors import AuthorizationDenied
from app.health_core.authorization.guard import (
    AuthorizedHealthCore,
    ResourceAttributeIndex,
    build_authorized_context,
)
from app.health_core.authorization.models import (
    PUBLIC_DENIAL_REASON,
    Action,
    AuthorizationDecision,
    Decision,
    PolicyId,
    Principal,
    ResourceContext,
)

__all__ = [
    "GENESIS_HASH",
    "PUBLIC_DENIAL_REASON",
    "REVOCATION_POLICY_BY_SCOPE",
    "ROLE_PERMISSIONS",
    "Action",
    "AuditRecord",
    "AuditVerification",
    "AuthorizationAuditLog",
    "AuthorizationDecision",
    "AuthorizationDenied",
    "AuthorizationEngine",
    "AuthorizedHealthCore",
    "Decision",
    "Grant",
    "PolicyId",
    "Principal",
    "ResourceAttributeIndex",
    "ResourceContext",
    "Revocation",
    "RevocationScope",
    "build_authorized_context",
    "compute_record_hash",
    "verify_audit_chain",
]
