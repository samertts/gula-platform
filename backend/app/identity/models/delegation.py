"""B5 — canonical NIAM delegation record.

Owner directive GULA-MASTER-AUTH-2026-11-19 §5/B5 (AUD-SEC-008).

A delegation is NOT a second authorization engine. It is an additive, revocable,
time-bounded, scope-bounded, depth-limited *input* to the single canonical
authority (``RolePermissionService.effective_permissions``). The delegated role
is a canonical ``niam_roles`` row; the delegated permissions are a verified
subset of that role's active permissions; the delegated scope is a verified
subset of the delegator's own canonical scope.

No new role/permission catalog entry is created by this model. No identity or
account identifier is minted. All identifiers are the canonical NIAM 26-char
account/role/organization IDs.

Protected decisions (HOLD, MPI REJECT, MP-001, ODR-001…004, D-020/D-021,
ADR-A…J, AUD-02/07/16) are never touched by this model.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, Column, DateTime, Index, Integer, String

from app._compat import UTC
from app.identity.base import IdentityBaseEntity


class DelegationStatus:
    active = "active"
    revoked = "revoked"
    expired = "expired"


class NiamDelegation(IdentityBaseEntity):
    """Scoped, revocable, depth-limited delegation of a canonical NIAM role.

    ``depth`` is the delegation-hop count (1 = first delegation of a directly
    assigned role). ``MAX_DELEGATION_DEPTH`` caps re-delegation chains so that
    authority can never be propagated indefinitely (deep-limited).
    """

    __tablename__ = "niam_delegations"
    __table_args__ = (
        CheckConstraint("depth >= 1 AND depth <= 3", name="ck_niam_delegations_depth"),
        Index("ix_niam_delegations_delegate", "delegate_account_id", "status"),
        Index("ix_niam_delegations_role", "role_id", "status"),
    )

    uuid = Column(String(36), unique=True, nullable=False, index=True)

    # The account that holds (directly or via a shallower delegation) the role
    # and grants it, and the account that receives the delegated authority.
    delegator_account_id = Column(String(26), nullable=False, index=True)
    delegate_account_id = Column(String(26), nullable=False, index=True)

    # Canonical role id (niam_roles.id) — never a new/ad-hoc role.
    role_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=True, index=True)
    department_id = Column(String(26), nullable=True, index=True)
    unit_id = Column(String(26), nullable=True, index=True)
    workspace_id = Column(String(26), nullable=True, index=True)
    scope_type = Column(String(30), nullable=False)

    # Verified non-empty subset of the role's active permission keys. A JSON
    # list only; any other shape is treated as "no permissions" by the reader.
    permission_keys = Column(JSON, nullable=False)

    depth = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default=DelegationStatus.active, index=True)
    reason = Column(String(500), nullable=True)
    starts_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(String(26), nullable=True)
    revocation_reason = Column(String(500), nullable=True)
    version = Column(Integer, nullable=False, default=1)


__all__ = ["DelegationStatus", "NiamDelegation"]
