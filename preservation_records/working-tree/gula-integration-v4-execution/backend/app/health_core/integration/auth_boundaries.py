"""Declarative authorization boundaries for synthetic client integration.

This module describes *which role may call which synthetic operation*. It is
not an authentication implementation: it issues no token, reads no session and
accepts no credential. Validation is fail-closed and rejects anonymous access,
public writes and any declared bypass path.

The catalogue covers read and write operations for all 10 eligible domains.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from app.health_core.common import ForbiddenSyntheticOperationError
from app.health_core.integration.api_client import DomainCode


class AccessMode(StrEnum):
    READ = "read"
    WRITE = "write"


class Role(StrEnum):
    """Synthetic roles used for integration contract tests only."""

    ANONYMOUS = "anonymous"
    SYNTHETIC_VIEWER = "synthetic_viewer"
    CLINICIAN = "clinician"
    LAB_TECHNICIAN = "lab_technician"
    LAB_MANAGER = "lab_manager"
    AUDITOR = "auditor"
    PLATFORM_ADMIN = "platform_admin"


class Operation(StrEnum):
    """Every synthetic read/write operation exposed by the client contract."""

    READ_PRACTITIONER = "read:practitioner"
    WRITE_PRACTITIONER = "write:practitioner"
    READ_FACILITY = "read:organization_facility"
    WRITE_FACILITY = "write:organization_facility"
    READ_MEDICAL_RECORD = "read:medical_record"
    WRITE_MEDICAL_RECORD = "write:medical_record"
    READ_ENCOUNTER = "read:encounter"
    WRITE_ENCOUNTER = "write:encounter"
    READ_DIAGNOSIS = "read:diagnosis"
    WRITE_DIAGNOSIS = "write:diagnosis"
    READ_OBSERVATION = "read:observation"
    WRITE_OBSERVATION = "write:observation"
    READ_LAB_ORDER = "read:lab_order"
    WRITE_LAB_ORDER = "write:lab_order"
    READ_SPECIMEN = "read:specimen"
    WRITE_SPECIMEN = "write:specimen"
    READ_LAB_RESULT = "read:lab_result"
    WRITE_LAB_RESULT = "write:lab_result"
    READ_VERIFICATION = "read:result_verification"
    WRITE_VERIFICATION = "write:result_verification"


ELIGIBLE_OPERATIONS: tuple[Operation, ...] = tuple(Operation)


@dataclass(frozen=True, slots=True)
class AuthBoundary:
    """Declarative rule for one operation."""

    operation: Operation
    required_role: Role
    anonymous_allowed: bool = False
    bypass_paths: tuple[str, ...] = ()
    rationale: str = ""


@dataclass(frozen=True, slots=True)
class BoundaryValidation:
    """Result of validating a complete boundary set."""

    errors: tuple[str, ...]
    checked_operations: tuple[Operation, ...]

    @property
    def is_valid(self) -> bool:
        """True when no violation was found."""
        return not self.errors

    def raise_if_invalid(self) -> None:
        """Raise a structured synthetic error when violations exist."""
        if self.errors:
            raise ForbiddenSyntheticOperationError(
                "invalid synthetic authorization boundary set",
                details={"errors": list(self.errors)},
            )


def is_write_operation(operation: Operation) -> bool:
    """True for write operations."""
    return operation.value.startswith(f"{AccessMode.WRITE.value}:")


def validate_boundaries(
    boundaries: Iterable[AuthBoundary],
    expected_operations: Iterable[Operation] = ELIGIBLE_OPERATIONS,
) -> BoundaryValidation:
    """Validate completeness and fail-closed properties of a boundary set."""
    rules = tuple(boundaries)
    expected = tuple(expected_operations)
    errors: list[str] = []

    by_operation: dict[Operation, list[AuthBoundary]] = {operation: [] for operation in expected}
    for rule in rules:
        if rule.operation not in by_operation:
            operation_name = getattr(rule.operation, "value", str(rule.operation))
            errors.append(f"UNKNOWN_OPERATION: {operation_name}")
            continue
        by_operation[rule.operation].append(rule)

    for operation, candidates in by_operation.items():
        if not candidates:
            errors.append(f"MISSING_OPERATION: {operation.value}")
            continue
        if len(candidates) > 1:
            errors.append(f"DUPLICATE_OPERATION: {operation.value}")
            continue
        rule = candidates[0]
        if rule.required_role is Role.ANONYMOUS:
            errors.append(f"ANONYMOUS_ROLE: {operation.value}")
        if rule.anonymous_allowed:
            kind = "PUBLIC_WRITE" if is_write_operation(operation) else "ANONYMOUS_READ"
            errors.append(f"{kind}: {operation.value}")
        if rule.bypass_paths:
            errors.append(f"BYPASS_PATH: {operation.value}: {rule.bypass_paths}")
        if (
            is_write_operation(operation)
            and rule.required_role is Role.SYNTHETIC_VIEWER
        ):
            errors.append(f"VIEWER_WRITE: {operation.value}")

    return BoundaryValidation(errors=tuple(errors), checked_operations=expected)


def assert_valid_boundaries(boundaries: Iterable[AuthBoundary]) -> None:
    """Raise unless the supplied boundary set is complete and bypass-free."""
    validate_boundaries(boundaries).raise_if_invalid()


def is_permitted(
    boundaries: Iterable[AuthBoundary], operation: Operation, role: Role
) -> bool:
    """Declarative permission check: exact role match, no hierarchy and no bypass."""
    rules = tuple(boundaries)
    if role is Role.ANONYMOUS or not validate_boundaries(rules).is_valid:
        return False
    for rule in rules:
        if rule.operation is operation:
            return (
                rule.required_role is role
                and not rule.anonymous_allowed
                and not rule.bypass_paths
            )
    return False


_WRITE_ROLE_BY_DOMAIN: dict[DomainCode, Role] = {
    DomainCode.PRACTITIONER: Role.LAB_MANAGER,
    DomainCode.FACILITY: Role.LAB_MANAGER,
    DomainCode.MEDICAL_RECORD: Role.LAB_MANAGER,
    DomainCode.ENCOUNTER: Role.CLINICIAN,
    DomainCode.DIAGNOSIS: Role.CLINICIAN,
    DomainCode.OBSERVATION: Role.CLINICIAN,
    DomainCode.LAB_ORDER: Role.LAB_TECHNICIAN,
    DomainCode.SPECIMEN: Role.LAB_TECHNICIAN,
    DomainCode.LAB_RESULT: Role.LAB_TECHNICIAN,
    DomainCode.RESULT_VERIFICATION: Role.LAB_MANAGER,
}

_OPERATION_BY_DOMAIN: dict[DomainCode, tuple[Operation, Operation]] = {
    DomainCode.PRACTITIONER: (
        Operation.READ_PRACTITIONER,
        Operation.WRITE_PRACTITIONER,
    ),
    DomainCode.FACILITY: (Operation.READ_FACILITY, Operation.WRITE_FACILITY),
    DomainCode.MEDICAL_RECORD: (
        Operation.READ_MEDICAL_RECORD,
        Operation.WRITE_MEDICAL_RECORD,
    ),
    DomainCode.ENCOUNTER: (Operation.READ_ENCOUNTER, Operation.WRITE_ENCOUNTER),
    DomainCode.DIAGNOSIS: (Operation.READ_DIAGNOSIS, Operation.WRITE_DIAGNOSIS),
    DomainCode.OBSERVATION: (
        Operation.READ_OBSERVATION,
        Operation.WRITE_OBSERVATION,
    ),
    DomainCode.LAB_ORDER: (Operation.READ_LAB_ORDER, Operation.WRITE_LAB_ORDER),
    DomainCode.SPECIMEN: (Operation.READ_SPECIMEN, Operation.WRITE_SPECIMEN),
    DomainCode.LAB_RESULT: (Operation.READ_LAB_RESULT, Operation.WRITE_LAB_RESULT),
    DomainCode.RESULT_VERIFICATION: (
        Operation.READ_VERIFICATION,
        Operation.WRITE_VERIFICATION,
    ),
}


def _default_boundaries() -> tuple[AuthBoundary, ...]:
    rules: list[AuthBoundary] = []
    for domain in DomainCode:
        read_operation, write_operation = _OPERATION_BY_DOMAIN[domain]
        rules.append(
            AuthBoundary(
                operation=read_operation,
                required_role=Role.SYNTHETIC_VIEWER,
                rationale=f"synthetic read of {domain.value} for integration fixtures",
            )
        )
        rules.append(
            AuthBoundary(
                operation=write_operation,
                required_role=_WRITE_ROLE_BY_DOMAIN[domain],
                rationale=f"synthetic write of {domain.value} requires an explicit named role",
            )
        )
    return tuple(rules)


DEFAULT_BOUNDARIES: tuple[AuthBoundary, ...] = _default_boundaries()

# Module-level maps are read-only to callers.
OPERATION_BY_DOMAIN = MappingProxyType(_OPERATION_BY_DOMAIN)
