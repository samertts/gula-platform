"""Core value objects for the runtime authorization layer.

Every value object here is frozen and synthetic-only. Principals carry only
opaque ``SYN-`` identifiers and authenticated attributes; they deliberately carry
no grant field because grants and revocations must come from the authoritative
:mod:`app.health_core.authorization.engine` registry, never from caller input.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from app.health_core.common.errors import InvalidSyntheticReferenceError
from app.health_core.common.ids import is_synthetic_id
from app.health_core.contracts.authorization import Role
from app.health_core.contracts.catalogue import ContractOperation

__all__ = [
    "PUBLIC_DENIAL_REASON",
    "Action",
    "AuthorizationDecision",
    "Decision",
    "PolicyId",
    "Principal",
    "ResourceContext",
]

type Action = ContractOperation

#: Every denial surfaces the same generic text: it never reveals whether a
#: resource exists, which tenant owns it, or which policy rejected the call.
PUBLIC_DENIAL_REASON = "authorization denied for this operation"


class Decision(StrEnum):
    """The two possible outcomes of an authorization evaluation."""

    ALLOW = "ALLOW"
    DENY = "DENY"


class PolicyId(StrEnum):
    """Stable internal identifiers for the rule that produced a decision."""

    ALLOW_EXPLICIT = "ALLOW:EXPLICIT_PERMISSION"
    DENY_NO_POLICY = "DENY:NO_POLICY"
    DENY_UNAUTHENTICATED = "DENY:UNAUTHENTICATED"
    DENY_TENANT = "DENY:CROSS_TENANT"
    DENY_REVOKED_PRINCIPAL = "DENY:REVOKED_PRINCIPAL"
    DENY_REVOKED_ROLE = "DENY:REVOKED_ROLE"
    DENY_REVOKED_PERMISSION = "DENY:REVOKED_PERMISSION"
    DENY_MISSING_PERMISSION = "DENY:MISSING_PERMISSION"
    DENY_MISSING_ATTRIBUTE = "DENY:MISSING_RESOURCE_ATTRIBUTE"
    DENY_ORG_SCOPE = "DENY:ORGANIZATION_SCOPE"
    DENY_FACILITY_SCOPE = "DENY:FACILITY_SCOPE"
    DENY_PATIENT_SCOPE = "DENY:PATIENT_SCOPE"


def _require_synthetic(value: str, *, field_name: str) -> str:
    """Return a validated opaque ``SYN-`` identifier."""
    if not is_synthetic_id(value):
        raise InvalidSyntheticReferenceError(
            f"{field_name} must be a SYN- prefixed synthetic reference",
            details={"field": field_name},
        )
    return value


def _validate_synthetic_set(values: frozenset[str], *, field_name: str) -> frozenset[str]:
    """Validate every member of an identifier set, failing closed on the first bad one."""
    for value in values:
        _require_synthetic(value, field_name=field_name)
    return values


@dataclass(frozen=True, slots=True)
class Principal:
    """An authenticated synthetic principal and its explicitly issued attributes.

    Roles, organization/facility sets and patient scopes are attributes of the
    authenticated identity. Permissions are NOT attributes: they are resolved by
    the engine from the exact role map plus authoritative grants, minus active
    revocations. Being authenticated therefore grants nothing on its own.
    """

    principal_id: str
    tenant_id: str
    roles: frozenset[Role] = field(default_factory=frozenset)
    organization_ids: frozenset[str] = field(default_factory=frozenset)
    facility_ids: frozenset[str] = field(default_factory=frozenset)
    patient_scopes: frozenset[str] = field(default_factory=frozenset)
    authenticated: bool = True

    def __post_init__(self) -> None:
        _require_synthetic(self.principal_id, field_name="principal_id")
        _require_synthetic(self.tenant_id, field_name="tenant_id")
        for role in self.roles:
            if not isinstance(role, Role):
                raise ValueError("roles must contain only Role enum members")
        _validate_synthetic_set(self.organization_ids, field_name="organization_ids")
        _validate_synthetic_set(self.facility_ids, field_name="facility_ids")
        _validate_synthetic_set(self.patient_scopes, field_name="patient_scopes")

    def without_authentication(self) -> Principal:
        """Return a copy flagged as unauthenticated (for fail-closed tests)."""
        return Principal(
            principal_id=self.principal_id,
            tenant_id=self.tenant_id,
            roles=self.roles,
            organization_ids=self.organization_ids,
            facility_ids=self.facility_ids,
            patient_scopes=self.patient_scopes,
            authenticated=False,
        )

    def with_patient_scope(self, patient_ref: str) -> Principal:
        """Return a copy with one additional explicit patient scope."""
        _require_synthetic(patient_ref, field_name="patient_ref")
        return Principal(
            principal_id=self.principal_id,
            tenant_id=self.tenant_id,
            roles=self.roles,
            organization_ids=self.organization_ids,
            facility_ids=self.facility_ids,
            patient_scopes=self.patient_scopes | {patient_ref},
            authenticated=self.authenticated,
        )

    def with_organization(self, organization_id: str) -> Principal:
        """Return a copy with one additional permitted organization."""
        _require_synthetic(organization_id, field_name="organization_id")
        return Principal(
            principal_id=self.principal_id,
            tenant_id=self.tenant_id,
            roles=self.roles,
            organization_ids=self.organization_ids | {organization_id},
            facility_ids=self.facility_ids,
            patient_scopes=self.patient_scopes,
            authenticated=self.authenticated,
        )

    def with_facility(self, facility_id: str) -> Principal:
        """Return a copy with one additional permitted facility."""
        _require_synthetic(facility_id, field_name="facility_id")
        return Principal(
            principal_id=self.principal_id,
            tenant_id=self.tenant_id,
            roles=self.roles,
            organization_ids=self.organization_ids,
            facility_ids=self.facility_ids | {facility_id},
            patient_scopes=self.patient_scopes,
            authenticated=self.authenticated,
        )

    def with_role(self, role: Role) -> Principal:
        """Return a copy carrying one additional *exact* role (no hierarchy)."""
        if not isinstance(role, Role):
            raise ValueError("role must be a Role enum member")
        return Principal(
            principal_id=self.principal_id,
            tenant_id=self.tenant_id,
            roles=self.roles | {role},
            organization_ids=self.organization_ids,
            facility_ids=self.facility_ids,
            patient_scopes=self.patient_scopes,
            authenticated=self.authenticated,
        )


@dataclass(frozen=True, slots=True)
class ResourceContext:
    """The attributes of one guarded operation evaluated by the engine.

    Resource attributes for reads come from the authoritative attribute index,
    never from caller-supplied claims. ``action`` is intentionally not validated
    here: an unknown action must reach the engine and be denied as ``NO_POLICY``.
    """

    tenant_id: str
    resource_id: str
    action: Action
    organization_id: str | None = None
    facility_id: str | None = None
    patient_ref: str | None = None

    def __post_init__(self) -> None:
        _require_synthetic(self.tenant_id, field_name="tenant_id")
        _require_synthetic(self.resource_id, field_name="resource_id")
        if self.organization_id is not None:
            _require_synthetic(self.organization_id, field_name="organization_id")
        if self.facility_id is not None:
            _require_synthetic(self.facility_id, field_name="facility_id")
        if self.patient_ref is not None:
            _require_synthetic(self.patient_ref, field_name="patient_ref")

    def with_action(self, action: Action) -> ResourceContext:
        """Return the same resource attributes bound to a different action."""
        return ResourceContext(
            tenant_id=self.tenant_id,
            resource_id=self.resource_id,
            action=action,
            organization_id=self.organization_id,
            facility_id=self.facility_id,
            patient_ref=self.patient_ref,
        )


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    """The complete internal result of one evaluation, ready for audit."""

    decision: Decision
    policy_id: PolicyId
    reason: str
    principal_id: str
    action: str
    resource_id: str
    tenant_id: str
    occurred_at: str

    @property
    def allowed(self) -> bool:
        """True only for an explicit ALLOW decision."""
        return self.decision is Decision.ALLOW
