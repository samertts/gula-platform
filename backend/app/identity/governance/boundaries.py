"""Authority boundaries — ministry / directorate / facility / professional / domain.

Governance authorities must never silently override one another. This module
provides the explicit boundary model:

* **Boundary types** — every authority is classified into exactly one of the
  five boundary types (``AuthorityBoundaryType``) via the configurable
  ``AUTHORITY_BOUNDARY_TYPE_MAP``.
* **Explicit control, never silent** — ``resolve`` maps a privileged action to
  its allowed controlling boundary types in deterministic precedence order
  (``PRIVILEGED_ACTION_POLICY``). When several boundary types claim the same
  action, the precedence order decides *explicitly* and the decision records
  the rule. When two authorities of the *same* controlling type both claim the
  action, resolution raises ``AuthorityBoundaryConflict`` — an ambiguity that
  must be resolved explicitly, never by silent override.
* **Unspecified legal authority as policy/config** — ``PRIVILEGED_ACTION_POLICY``
  and ``AUTHORITY_BOUNDARY_TYPE_MAP`` are the configuration points where legal
  authority that has not yet been codified is expressed. Actions outside the
  policy are denied by default (``action_not_governed``).
* **Privileged actions are auditable** — ``enforce`` records every privileged
  decision (allow or deny) through the hash-chained identity audit service.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app._compat import StrEnum
from app.identity.governance.models import IdentityAuthority
from app.identity.models.audit import AuditAction
from app.identity.services.audit_service import AuditService


class AuthorityBoundaryType(StrEnum):
    ministry = "ministry"
    directorate = "directorate"
    facility = "facility"
    professional = "professional"
    domain = "domain"


# Configurable classification: authority_type -> boundary type. This is the
# policy/config knob for legal authority that is not yet codified. Unknown
# authority types fall back to the generic ``domain`` boundary.
AUTHORITY_BOUNDARY_TYPE_MAP: dict[str, AuthorityBoundaryType] = {
    "ministry": AuthorityBoundaryType.ministry,
    "health_ministry": AuthorityBoundaryType.ministry,
    "national_authority": AuthorityBoundaryType.ministry,
    "directorate": AuthorityBoundaryType.directorate,
    "health_directorate": AuthorityBoundaryType.directorate,
    "regional_authority": AuthorityBoundaryType.directorate,
    "facility_authority": AuthorityBoundaryType.facility,
    "hospital_authority": AuthorityBoundaryType.facility,
    "laboratory_authority": AuthorityBoundaryType.facility,
    "professional_authority": AuthorityBoundaryType.professional,
    "professional_syndicate": AuthorityBoundaryType.professional,
    "medical_syndicate": AuthorityBoundaryType.professional,
    "trade_union": AuthorityBoundaryType.professional,
    "domain_authority": AuthorityBoundaryType.domain,
}

DEFAULT_BOUNDARY_TYPE: AuthorityBoundaryType = AuthorityBoundaryType.domain


# Privileged action -> allowed controlling boundary types in precedence order.
# The FIRST listed boundary type that appears among the requesting authorities
# controls the decision deterministically. This precedence is explicit: no
# boundary silently overrides another. Actions not listed here are not
# governed and are denied by default.
PRIVILEGED_ACTION_POLICY: dict[str, tuple[AuthorityBoundaryType, ...]] = {
    "identity.revoke": (AuthorityBoundaryType.ministry,),
    "identity.restore": (AuthorityBoundaryType.ministry,),
    "organization.administer": (
        AuthorityBoundaryType.ministry,
        AuthorityBoundaryType.directorate,
    ),
    "facility.administer": (AuthorityBoundaryType.facility,),
    "facility.certify": (
        AuthorityBoundaryType.ministry,
        AuthorityBoundaryType.directorate,
        AuthorityBoundaryType.facility,
    ),
    "professional.verify": (
        AuthorityBoundaryType.professional,
        AuthorityBoundaryType.ministry,
    ),
    "professional.suspend": (
        AuthorityBoundaryType.professional,
        AuthorityBoundaryType.ministry,
    ),
    "license.issue": (AuthorityBoundaryType.professional,),
    "domain.authorize": (
        AuthorityBoundaryType.domain,
        AuthorityBoundaryType.ministry,
    ),
}


class AuthorityBoundaryError(Exception):
    """Raised when no authority boundary permits a privileged action."""


class AuthorityBoundaryConflict(AuthorityBoundaryError):
    """Raised when several authorities of the same controlling type both claim.

    The ambiguity must be resolved explicitly; it is never silently overridden.
    """


@dataclass(frozen=True)
class AuthorityBoundary:
    authority_id: str
    boundary_type: AuthorityBoundaryType
    jurisdiction: str = "national"
    organization_id: str | None = None


@dataclass(frozen=True)
class AuthorityBoundaryDecision:
    allowed: bool
    action: str
    subject_kind: str
    boundary_type: AuthorityBoundaryType | None
    authority_id: str | None
    precedence: tuple[AuthorityBoundaryType, ...]
    reason: str


def boundary_type_for(authority_type: str | None) -> AuthorityBoundaryType:
    """Classify an authority type into a boundary type (default: ``domain``)."""
    if not authority_type:
        return DEFAULT_BOUNDARY_TYPE
    return AUTHORITY_BOUNDARY_TYPE_MAP.get(authority_type, DEFAULT_BOUNDARY_TYPE)


def boundary_for_authority(authority: IdentityAuthority) -> AuthorityBoundary:
    """Derive a boundary from an ``IdentityAuthority`` record."""
    return AuthorityBoundary(
        authority_id=authority.id,
        boundary_type=boundary_type_for(authority.authority_type),
        jurisdiction=authority.jurisdiction,
        organization_id=None,
    )


class AuthorityBoundaryService:
    """Resolve and enforce authority boundaries for privileged actions.

    ``audit`` is optional: when provided, every privileged decision (allow,
    deny, conflict) is recorded through the hash-chained identity audit.
    """

    def __init__(self, audit: AuditService | None = None) -> None:
        self.audit = audit

    @staticmethod
    def resolve(
        authorities: Sequence[AuthorityBoundary],
        action: str,
        subject_kind: str,
    ) -> AuthorityBoundaryDecision:
        """Deterministically resolve which authority boundary controls ``action``.

        * ``action`` outside ``PRIVILEGED_ACTION_POLICY`` -> denied.
        * No authority carries an allowed boundary type -> denied.
        * Several allowed boundary types -> the highest-precedence one
          controls (explicit precedence, never silent).
        * Several authorities of the *same* controlling type -> conflict.
        """
        precedence = PRIVILEGED_ACTION_POLICY.get(action, ())
        if not precedence:
            return AuthorityBoundaryDecision(
                allowed=False,
                action=action,
                subject_kind=subject_kind,
                boundary_type=None,
                authority_id=None,
                precedence=precedence,
                reason="action_not_governed",
            )
        allowed = [b for b in authorities if b.boundary_type in precedence]
        if not allowed:
            return AuthorityBoundaryDecision(
                allowed=False,
                action=action,
                subject_kind=subject_kind,
                boundary_type=None,
                authority_id=None,
                precedence=precedence,
                reason="no_authority_for_action",
            )
        controlling = next(t for t in precedence if any(b.boundary_type == t for b in allowed))
        candidates = [b for b in allowed if b.boundary_type == controlling]
        if len(candidates) > 1:
            raise AuthorityBoundaryConflict(
                f"{action} claimed by multiple {controlling.value} authorities: "
                f"{', '.join(b.authority_id for b in candidates)}"
            )
        controlling_authority = candidates[0]
        return AuthorityBoundaryDecision(
            allowed=True,
            action=action,
            subject_kind=subject_kind,
            boundary_type=controlling_authority.boundary_type,
            authority_id=controlling_authority.authority_id,
            precedence=precedence,
            reason=f"controlled_by_{controlling_authority.boundary_type.value}",
        )

    async def enforce(
        self,
        action: str,
        authorities: Sequence[AuthorityBoundary],
        subject_kind: str,
        *,
        subject_id: str | None = None,
        actor_id: str | None = None,
        organization_id: str | None = None,
    ) -> AuthorityBoundaryDecision:
        """Enforce a privileged action; record the decision and raise on denial.

        Returns the controlling decision on success, otherwise raises
        ``AuthorityBoundaryError`` (or ``AuthorityBoundaryConflict``).
        """
        try:
            decision = self.resolve(authorities, action, subject_kind)
        except AuthorityBoundaryConflict as conflict:
            if self.audit is not None:
                await self.audit.record(
                    AuditAction.authority_boundary_denied,
                    actor_id=actor_id,
                    target_type=subject_kind,
                    target_id=subject_id,
                    metadata={
                        "action": action,
                        "reason": "conflict",
                        "detail": str(conflict),
                    },
                    organization_id=organization_id,
                    outcome="conflict",
                )
            raise
        if decision.allowed:
            if self.audit is not None:
                await self.audit.record(
                    AuditAction.authority_boundary_enforced,
                    actor_id=actor_id,
                    target_type=subject_kind,
                    target_id=subject_id,
                    metadata={
                        "action": action,
                        "authority_id": decision.authority_id,
                        "boundary_type": (
                            decision.boundary_type.value if decision.boundary_type else None
                        ),
                        "reason": decision.reason,
                    },
                    organization_id=organization_id,
                )
            return decision
        if self.audit is not None:
            await self.audit.record(
                AuditAction.authority_boundary_denied,
                actor_id=actor_id,
                target_type=subject_kind,
                target_id=subject_id,
                metadata={
                    "action": action,
                    "reason": decision.reason,
                },
                organization_id=organization_id,
                outcome="denied",
            )
        raise AuthorityBoundaryError(f"{action} denied for {subject_kind}: {decision.reason}")
