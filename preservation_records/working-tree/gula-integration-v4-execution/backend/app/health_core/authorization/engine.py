"""Deterministic, deny-by-default authorization policy engine — SYNTHETIC ONLY.

AUD-ARCH-003 / single-source-of-truth: this engine is NOT the platform-wide
permission authority. It exists solely to enforce declared boundaries inside the
non-activated synthetic Health Core slice (opaque ``SYN-`` identifiers, no real
identity or database). The ONE canonical authorization authority for GULA is
``backend/app/identity/services/authorization_service.py`` (with the RBAC/ABAC
decision engine in ``identity/services/authorization_decision.py``), as recorded
in ``app/domain_platform/shared_core.py``.

Decision equivalence between this synthetic engine and the canonical authority
is pinned by ``tests/health_core/test_authorization_synthetic_scope.py``: for a
shared corpus of authorization situations they must return the same ALLOW/DENY
verdict. Never extend this engine to real identities or production routes — use
the canonical authority instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from app.health_core.authorization.audit import AuthorizationAuditLog
from app.health_core.authorization.models import (
    PUBLIC_DENIAL_REASON,
    Action,
    AuthorizationDecision,
    Decision,
    PolicyId,
    Principal,
    ResourceContext,
)
from app.health_core.common.errors import InvalidSyntheticReferenceError
from app.health_core.common.ids import is_synthetic_id
from app.health_core.contracts.authorization import AUTHORIZATION_BOUNDARIES, Permission, Role
from app.health_core.contracts.catalogue import ContractOperation

__all__ = [
    "REVOCATION_POLICY_BY_SCOPE",
    "ROLE_PERMISSIONS",
    "AuthorizationEngine",
    "Grant",
    "Revocation",
    "RevocationScope",
]


class RevocationScope(StrEnum):
    """What a revocation record applies to."""

    PRINCIPAL = "principal"
    ROLE = "role"
    PERMISSION = "permission"


REVOCATION_POLICY_BY_SCOPE: dict[RevocationScope, PolicyId] = {
    RevocationScope.PRINCIPAL: PolicyId.DENY_REVOKED_PRINCIPAL,
    RevocationScope.ROLE: PolicyId.DENY_REVOKED_ROLE,
    RevocationScope.PERMISSION: PolicyId.DENY_REVOKED_PERMISSION,
}


def _build_role_permissions() -> dict[Role, frozenset[Permission]]:
    """Derive an exact per-role permission set from the declared boundaries.

    A role receives ONLY the permissions whose declared boundary names it as the
    minimum role. There is no ordering, inheritance or escalation implied by
    role seniority: an ADMIN with no explicit grant holds no permission at all.
    """
    by_role: dict[Role, set[Permission]] = {role: set() for role in Role}
    for boundary in AUTHORIZATION_BOUNDARIES.values():
        by_role[boundary.min_role].add(boundary.permission)
    return {role: frozenset(permissions) for role, permissions in by_role.items()}


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = _build_role_permissions()

_ORGANIZATION_ACTIONS = frozenset(
    {
        ContractOperation.ORGANIZATION_CREATE,
        ContractOperation.ORGANIZATION_READ,
        ContractOperation.FACILITY_CREATE,
        ContractOperation.FACILITY_READ,
    }
)
_FACILITY_ACTIONS = frozenset(
    {
        ContractOperation.FACILITY_CREATE,
        ContractOperation.FACILITY_READ,
    }
)
_PATIENT_ACTIONS = frozenset(
    {
        ContractOperation.ENCOUNTER_CREATE,
        ContractOperation.ENCOUNTER_READ,
        ContractOperation.DIAGNOSIS_CREATE,
        ContractOperation.DIAGNOSIS_READ,
        ContractOperation.OBSERVATION_CREATE,
        ContractOperation.OBSERVATION_READ,
        ContractOperation.MEDICAL_RECORD_CREATE,
        ContractOperation.MEDICAL_RECORD_READ,
        ContractOperation.LAB_ORDER_CREATE,
        ContractOperation.SPECIMEN_CREATE,
        ContractOperation.LAB_RESULT_CREATE,
    }
)


def _action_name(action: Action) -> str:
    """Return a stable string for an action, including unknown injected actions."""
    return action.value if isinstance(action, ContractOperation) else str(action)


def _permission_for(action: Action) -> Permission | None:
    """Return the declared permission for an action, or ``None`` (deny)."""
    if not isinstance(action, ContractOperation):
        return None
    boundary = AUTHORIZATION_BOUNDARIES.get(action)
    return None if boundary is None else boundary.permission


def _is_expired(expires_at: str | None, *, now: datetime) -> bool:
    """Return whether an ISO-8601 expiry has passed; malformed values fail closed."""
    if expires_at is None:
        return False
    try:
        moment = datetime.fromisoformat(expires_at)
    except ValueError:
        # Fail closed: a malformed expiry is treated as already expired. Using
        # datetime.min keeps the return value computed by the same comparison
        # as every well-formed expiry (rather than a literal success return).
        moment = datetime.min
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment <= now


def _require_principal_id(principal_id: str) -> str:
    """Validate an opaque principal id used to register grants or revocations."""
    if not is_synthetic_id(principal_id):
        raise InvalidSyntheticReferenceError(
            "principal_id must be a SYN- prefixed synthetic reference",
            details={"field": "principal_id"},
        )
    return principal_id


@dataclass(frozen=True, slots=True)
class Grant:
    """An authoritative, reason-bearing, optionally expiring permission grant."""

    principal_id: str
    permission: Permission
    reason: str
    granted_at: str
    expires_at: str | None = None

    def is_active(self, *, now: datetime) -> bool:
        """Return whether the grant is currently effective."""
        return not _is_expired(self.expires_at, now=now)


@dataclass(frozen=True, slots=True)
class Revocation:
    """An explicit revoke record that overrides every matching grant immediately."""

    scope: RevocationScope
    reason: str
    revoked_at: str
    principal_id: str | None = None
    role: Role | None = None
    permission: Permission | None = None
    expires_at: str | None = None

    def __post_init__(self) -> None:
        if self.scope is RevocationScope.PRINCIPAL and self.principal_id is None:
            raise ValueError("a principal revocation requires principal_id")
        if self.scope is RevocationScope.ROLE and self.role is None:
            raise ValueError("a role revocation requires role")
        if self.scope is RevocationScope.PERMISSION and self.permission is None:
            raise ValueError("a permission revocation requires permission")

    def is_active(self, *, now: datetime) -> bool:
        """Return whether the revocation is currently effective."""
        return not _is_expired(self.expires_at, now=now)

    def applies_to(self, principal: Principal, permission: Permission) -> bool:
        """Return whether this revocation hits this principal/permission pair."""
        if self.scope is RevocationScope.PRINCIPAL:
            return self.principal_id == principal.principal_id
        if self.scope is RevocationScope.ROLE:
            return self.role in principal.roles and (
                self.permission is None or self.permission is permission
            )
        return self.permission is permission


class AuthorizationEngine:
    """Evaluate (principal, action, resource) tuples and audit every decision."""

    def __init__(self) -> None:
        self._grants: dict[str, tuple[Grant, ...]] = {}
        self._revocations: tuple[Revocation, ...] = ()
        self._audit = AuthorizationAuditLog()

    @property
    def audit(self) -> AuthorizationAuditLog:
        """The append-only decision audit log."""
        return self._audit

    def grant(
        self,
        principal_id: str,
        permission: Permission,
        *,
        reason: str,
        expires_at: str | None = None,
        now: datetime | None = None,
    ) -> Grant:
        """Add one authoritative permission grant for a principal."""
        _require_principal_id(principal_id)
        if not isinstance(permission, Permission):
            raise ValueError("permission must be a Permission enum member")
        if not reason.strip():
            raise ValueError("a grant requires a non-empty reason")
        moment = now or datetime.now(UTC)
        record = Grant(
            principal_id=principal_id,
            permission=permission,
            reason=reason,
            granted_at=moment.isoformat(),
            expires_at=expires_at,
        )
        self._grants[principal_id] = (*self._grants.get(principal_id, ()), record)
        return record

    def revoke(
        self,
        scope: RevocationScope,
        *,
        reason: str,
        principal_id: str | None = None,
        role: Role | None = None,
        permission: Permission | None = None,
        expires_at: str | None = None,
        now: datetime | None = None,
    ) -> Revocation:
        """Register an explicit revoke record in the authoritative registry."""
        if not isinstance(scope, RevocationScope):
            raise ValueError("scope must be a RevocationScope enum member")
        if not reason.strip():
            raise ValueError("a revocation requires a non-empty reason")
        if principal_id is not None:
            _require_principal_id(principal_id)
        moment = now or datetime.now(UTC)
        record = Revocation(
            scope=scope,
            reason=reason,
            revoked_at=moment.isoformat(),
            principal_id=principal_id,
            role=role,
            permission=permission,
            expires_at=expires_at,
        )
        self._revocations = (*self._revocations, record)
        return record

    def revoke_principal(
        self, principal_id: str, *, reason: str, expires_at: str | None = None
    ) -> Revocation:
        """Revoke every permission of one principal immediately."""
        return self.revoke(
            RevocationScope.PRINCIPAL,
            reason=reason,
            principal_id=principal_id,
            expires_at=expires_at,
        )

    def revoke_role(
        self,
        role: Role,
        *,
        reason: str,
        permission: Permission | None = None,
        expires_at: str | None = None,
    ) -> Revocation:
        """Revoke a role entirely, or one permission granted through that role."""
        return self.revoke(
            RevocationScope.ROLE,
            reason=reason,
            role=role,
            permission=permission,
            expires_at=expires_at,
        )

    def revoke_permission(
        self, permission: Permission, *, reason: str, expires_at: str | None = None
    ) -> Revocation:
        """Revoke one permission for every principal and every source."""
        return self.revoke(
            RevocationScope.PERMISSION,
            reason=reason,
            permission=permission,
            expires_at=expires_at,
        )

    def active_grants(self, principal_id: str, *, now: datetime | None = None) -> tuple[Grant, ...]:
        """Return currently effective grants for a principal (test/audit surface)."""
        moment = now or datetime.now(UTC)
        return tuple(
            grant
            for grant in self._grants.get(principal_id, ())
            if grant.is_active(now=moment)
        )

    def active_revocations(self, *, now: datetime | None = None) -> tuple[Revocation, ...]:
        """Return currently effective revocations (test/audit surface)."""
        moment = now or datetime.now(UTC)
        return tuple(record for record in self._revocations if record.is_active(now=moment))

    def _effective_permissions(self, principal: Principal, *, now: datetime) -> frozenset[Permission]:
        """Union exact role permissions with authoritative, unexpired grants."""
        permissions: set[Permission] = set()
        for role in principal.roles:
            permissions.update(ROLE_PERMISSIONS.get(role, frozenset()))
        for grant in self.active_grants(principal.principal_id, now=now):
            permissions.add(grant.permission)
        return frozenset(permissions)

    def evaluate(self, principal: Principal, resource: ResourceContext) -> AuthorizationDecision:
        """Evaluate one guarded operation and append exactly one audit record."""
        now = datetime.now(UTC)
        occurred_at = now.isoformat()
        action_name = _action_name(resource.action)
        permission = _permission_for(resource.action)

        def deny(policy_id: PolicyId) -> AuthorizationDecision:
            decision = AuthorizationDecision(
                decision=Decision.DENY,
                policy_id=policy_id,
                reason=PUBLIC_DENIAL_REASON,
                principal_id=principal.principal_id,
                action=action_name,
                resource_id=resource.resource_id,
                tenant_id=resource.tenant_id,
                occurred_at=occurred_at,
            )
            self._audit.append(
                principal_id=principal.principal_id,
                tenant_id=resource.tenant_id,
                action=action_name,
                resource_id=resource.resource_id,
                decision=Decision.DENY.value,
                policy_id=policy_id.value,
                reason=PUBLIC_DENIAL_REASON,
                occurred_at=occurred_at,
            )
            return decision

        # Rule 1: no declared policy => deny. Authentication never creates a policy.
        if permission is None:
            return deny(PolicyId.DENY_NO_POLICY)
        # Rule 9: authentication alone grants nothing.
        if not principal.authenticated:
            return deny(PolicyId.DENY_UNAUTHENTICATED)
        # Rule 2/10: tenant equality is checked from supplied attributes only, so a
        # cross-tenant probe is denied without ever looking up the resource.
        if principal.tenant_id != resource.tenant_id:
            return deny(PolicyId.DENY_TENANT)
        # Rule 7: revocations override every grant, regardless of grant timing.
        for record in self.active_revocations(now=now):
            if record.applies_to(principal, permission):
                return deny(REVOCATION_POLICY_BY_SCOPE[record.scope])
        # Rules 4/9: exact role map + authoritative grants, no hierarchy.
        if permission not in self._effective_permissions(principal, now=now):
            return deny(PolicyId.DENY_MISSING_PERMISSION)
        # Rules 1/3: absent or out-of-scope organization and facility attributes.
        if resource.action in _ORGANIZATION_ACTIONS and resource.organization_id is None:
            return deny(PolicyId.DENY_MISSING_ATTRIBUTE)
        if (
            resource.organization_id is not None
            and resource.organization_id not in principal.organization_ids
        ):
            return deny(PolicyId.DENY_ORG_SCOPE)
        if resource.action in _FACILITY_ACTIONS and resource.facility_id is None:
            return deny(PolicyId.DENY_MISSING_ATTRIBUTE)
        if (
            resource.facility_id is not None
            and resource.facility_id not in principal.facility_ids
        ):
            return deny(PolicyId.DENY_FACILITY_SCOPE)
        # Rule 5: patient-scoped actions need an explicit matching patient scope.
        if (
            resource.action in _PATIENT_ACTIONS or resource.patient_ref is not None
        ) and (
            resource.patient_ref is None or resource.patient_ref not in principal.patient_scopes
        ):
            return deny(PolicyId.DENY_PATIENT_SCOPE)

        decision = AuthorizationDecision(
            decision=Decision.ALLOW,
            policy_id=PolicyId.ALLOW_EXPLICIT,
            reason="explicit permission and scope checks passed",
            principal_id=principal.principal_id,
            action=action_name,
            resource_id=resource.resource_id,
            tenant_id=resource.tenant_id,
            occurred_at=occurred_at,
        )
        self._audit.append(
            principal_id=principal.principal_id,
            tenant_id=resource.tenant_id,
            action=action_name,
            resource_id=resource.resource_id,
            decision=Decision.ALLOW.value,
            policy_id=PolicyId.ALLOW_EXPLICIT.value,
            reason=decision.reason,
            occurred_at=occurred_at,
        )
        return decision
