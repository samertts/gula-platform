"""Contract tests: every operation declares a non-public authorization boundary."""

from __future__ import annotations

import pytest
from app.health_core.contracts.authorization import (
    AUTHORIZATION_BOUNDARIES,
    PERMISSION_NAMESPACE,
    Permission,
    Role,
    boundary_for,
)
from app.health_core.contracts.catalogue import ContractOperation


def test_every_operation_has_exactly_one_boundary() -> None:
    assert set(AUTHORIZATION_BOUNDARIES) == set(ContractOperation)
    for operation, boundary in AUTHORIZATION_BOUNDARIES.items():
        assert boundary.operation is operation


@pytest.mark.parametrize("operation", list(ContractOperation))
def test_no_operation_is_public(operation: ContractOperation) -> None:
    boundary = AUTHORIZATION_BOUNDARIES[operation]
    assert boundary.public is False


@pytest.mark.parametrize("operation", list(ContractOperation))
def test_every_boundary_declares_permission_and_role(operation: ContractOperation) -> None:
    boundary = AUTHORIZATION_BOUNDARIES[operation]
    assert isinstance(boundary.permission, Permission)
    assert isinstance(boundary.min_role, Role)
    assert boundary.tenant_scoped is True


@pytest.mark.parametrize("operation", list(ContractOperation))
def test_permission_names_align_with_operations(operation: ContractOperation) -> None:
    permission = AUTHORIZATION_BOUNDARIES[operation].permission
    assert permission.name == operation.name
    assert permission.value.startswith(f"{PERMISSION_NAMESPACE}:")
    assert permission.value.endswith(f".{operation.value.split('.', 1)[1]}")


def test_permission_describe_returns_readable_label() -> None:
    assert Permission.PRACTITIONER_READ.describe() == "Practitioner.Read"
    assert Permission.LAB_RESULT_CREATE.describe() == "LabResult.Create"


def test_boundary_for_returns_declared_boundary() -> None:
    boundary = boundary_for(ContractOperation.RESULT_VERIFICATION_CREATE)
    assert boundary.permission is Permission.RESULT_VERIFICATION_CREATE
    assert boundary.min_role is Role.LAB_TECHNICIAN


def test_read_operations_require_viewer_role() -> None:
    read_operations = [op for op in ContractOperation if op.name.endswith("_READ")]
    assert len(read_operations) == 11
    for operation in read_operations:
        assert AUTHORIZATION_BOUNDARIES[operation].min_role is Role.VIEWER
