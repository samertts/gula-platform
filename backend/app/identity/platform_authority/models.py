"""NIAM Platform Authority — assignment-bound platform-global capability grants.

Phase 10 implementation of the architecture in
docs/security/NIAM_PLATFORM_AUTHORITY_ARCHITECTURE.md. A Platform Authority
assignment is a grant of exactly one of the four capabilities below to a
canonical NIAM identity (niam_identities, reached via Account.identity_id --
never an organization account role and never an organization_id). It is a
separate axis from niam_role_assignments (organization-scoped RBAC) and is
never resolved through Membership/RolePermissionService.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app._compat import UTC, StrEnum
from app.identity.base import IdentityBaseEntity


class PlatformCapability(StrEnum):
    federation_manage = "platform.federation.manage"
    trust_manage = "platform.trust.manage"
    certificates_manage = "platform.certificates.manage"
    governance_manage = "platform.governance.manage"


class PlatformAuthorityAssignmentStatus(StrEnum):
    active = "active"
    revoked = "revoked"


class PlatformAuthorityAssignment(IdentityBaseEntity):
    """One grant of one platform capability to one canonical NIAM identity.

    Revocation is terminal for a given row (mirrors niam_role_assignments'
    existing revoked -> {} transition rule) -- re-granting the same
    capability to the same identity after a revocation creates a new row
    rather than reactivating the old one, so the full grant/revoke history
    is preserved. At most one row per (identity_id, capability) may be
    'active' at a time; enforced by a partial unique index in the migration
    (see 20260908_0003), not just application logic, because a check-then-
    insert grant can otherwise race.
    """

    __tablename__ = "niam_platform_authority_assignments"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    identity_id = Column(
        String(26),
        ForeignKey("niam_identities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    capability = Column(String(80), nullable=False, index=True)
    status = Column(
        String(20),
        nullable=False,
        default=PlatformAuthorityAssignmentStatus.active.value,
        index=True,
    )

    granted_by = Column(
        String(26), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True
    )
    granted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    revoked_by = Column(
        String(26), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True
    )
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(Text, nullable=True)
