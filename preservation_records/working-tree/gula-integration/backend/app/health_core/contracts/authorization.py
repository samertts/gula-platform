"""Authorization boundary contract for every synthetic Health Core operation.

Permission and role values follow the reference-data style of existing
permission enums (``<namespace>:<resource>.<action>`` values plus a ``describe``
helper). Every declared operation has exactly one boundary and NO operation is
public: a boundary must be explicitly changed by an owner decision to become
public, and this contract family never declares one.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, StrEnum

from app.health_core.contracts.catalogue import DOMAIN_OPERATIONS, ContractDomain, ContractOperation

PERMISSION_NAMESPACE = "health_core"


class Role(StrEnum):
    """Minimum synthetic roles recognised by this contract family."""

    VIEWER = "viewer"
    CLINICIAN = "clinician"
    LAB_TECHNICIAN = "lab_technician"
    ADMIN = "admin"


class Permission(Enum):
    """Reference-data-style permissions, one per contract operation."""

    PRACTITIONER_CREATE = "health_core:practitioner.create"
    PRACTITIONER_READ = "health_core:practitioner.read"
    ORGANIZATION_CREATE = "health_core:organization.create"
    ORGANIZATION_READ = "health_core:organization.read"
    FACILITY_CREATE = "health_core:facility.create"
    FACILITY_READ = "health_core:facility.read"
    MEDICAL_RECORD_CREATE = "health_core:medical_record.create"
    MEDICAL_RECORD_READ = "health_core:medical_record.read"
    ENCOUNTER_CREATE = "health_core:encounter.create"
    ENCOUNTER_READ = "health_core:encounter.read"
    DIAGNOSIS_CREATE = "health_core:diagnosis.create"
    DIAGNOSIS_READ = "health_core:diagnosis.read"
    OBSERVATION_CREATE = "health_core:observation.create"
    OBSERVATION_READ = "health_core:observation.read"
    LAB_ORDER_CREATE = "health_core:lab_order.create"
    LAB_ORDER_READ = "health_core:lab_order.read"
    SPECIMEN_CREATE = "health_core:specimen.create"
    SPECIMEN_READ = "health_core:specimen.read"
    LAB_RESULT_CREATE = "health_core:lab_result.create"
    LAB_RESULT_READ = "health_core:lab_result.read"
    RESULT_VERIFICATION_CREATE = "health_core:result_verification.create"
    RESULT_VERIFICATION_READ = "health_core:result_verification.read"

    def describe(self) -> str:
        """Return a short human-readable label, matching house permission style."""
        _, _, action = self.value.partition(":")
        domain, _, verb = action.rpartition(".")
        label = "".join(part.title() for part in domain.split("_"))
        return f"{label}.{verb.title()}"


@dataclass(frozen=True, slots=True)
class AuthorizationBoundary:
    """The single authorization requirement attached to a contract operation."""

    operation: ContractOperation
    permission: Permission
    min_role: Role
    public: bool = False
    tenant_scoped: bool = True


_LAB_DOMAINS = frozenset(
    {
        ContractDomain.LAB_ORDER,
        ContractDomain.SPECIMEN,
        ContractDomain.LAB_RESULT,
        ContractDomain.RESULT_VERIFICATION,
    }
)


def _min_role_for(operation: ContractOperation) -> Role:
    """Derive the minimum role from the operation's domain and verb."""
    domain = ContractDomain(operation.value.split(".", 1)[0])
    if operation.name.endswith("_READ"):
        return Role.VIEWER
    if domain in _LAB_DOMAINS:
        return Role.LAB_TECHNICIAN
    return Role.CLINICIAN


AUTHORIZATION_BOUNDARIES: dict[ContractOperation, AuthorizationBoundary] = {
    operation: AuthorizationBoundary(
        operation=operation,
        permission=Permission[operation.name],
        min_role=_min_role_for(operation),
    )
    for pair in DOMAIN_OPERATIONS.values()
    for operation in pair
}


def boundary_for(operation: ContractOperation) -> AuthorizationBoundary:
    """Return the declared boundary, failing closed if one is missing."""
    boundary = AUTHORIZATION_BOUNDARIES.get(operation)
    if boundary is None:
        raise KeyError(f"contract operation has no authorization boundary: {operation.value}")
    if boundary.public:
        raise ValueError(f"contract operation must not be public: {operation.value}")
    return boundary
