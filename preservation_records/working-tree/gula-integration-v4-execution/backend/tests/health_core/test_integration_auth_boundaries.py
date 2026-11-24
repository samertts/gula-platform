"""Tests for declarative authorization boundaries and bypass rejection."""

from __future__ import annotations

from dataclasses import replace

import pytest
from app.health_core.common import ForbiddenSyntheticOperationError
from app.health_core.integration import (
    DEFAULT_BOUNDARIES,
    AuthBoundary,
    Operation,
    Role,
    assert_valid_boundaries,
    is_permitted,
    is_write_operation,
    validate_boundaries,
)


def test_default_boundaries_are_complete_and_valid() -> None:
    validation = validate_boundaries(DEFAULT_BOUNDARIES)
    assert validation.is_valid
    assert validation.errors == ()
    assert len(validation.checked_operations) == 20
    assert len(DEFAULT_BOUNDARIES) == 20


def test_every_domain_has_explicit_read_and_write_boundaries() -> None:
    operations = {boundary.operation for boundary in DEFAULT_BOUNDARIES}
    for operation in Operation:
        assert operation in operations
    assert is_write_operation(Operation.WRITE_LAB_RESULT)
    assert not is_write_operation(Operation.READ_LAB_RESULT)


def test_public_write_is_rejected() -> None:
    changed = tuple(
        replace(boundary, anonymous_allowed=True)
        if boundary.operation is Operation.WRITE_LAB_RESULT
        else boundary
        for boundary in DEFAULT_BOUNDARIES
    )
    validation = validate_boundaries(changed)
    assert not validation.is_valid
    assert any(error.startswith("PUBLIC_WRITE") for error in validation.errors)


def test_anonymous_read_is_rejected() -> None:
    changed = tuple(
        replace(boundary, anonymous_allowed=True)
        if boundary.operation is Operation.READ_ENCOUNTER
        else boundary
        for boundary in DEFAULT_BOUNDARIES
    )
    errors = validate_boundaries(changed).errors
    assert any(error.startswith("ANONYMOUS_READ") for error in errors)


def test_anonymous_required_role_is_rejected() -> None:
    changed = tuple(
        replace(boundary, required_role=Role.ANONYMOUS)
        if boundary.operation is Operation.WRITE_SPECIMEN
        else boundary
        for boundary in DEFAULT_BOUNDARIES
    )
    errors = validate_boundaries(changed).errors
    assert any(error.startswith("ANONYMOUS_ROLE") for error in errors)


def test_bypass_path_is_rejected() -> None:
    changed = tuple(
        replace(boundary, bypass_paths=("/demo/write",))
        if boundary.operation is Operation.WRITE_VERIFICATION
        else boundary
        for boundary in DEFAULT_BOUNDARIES
    )
    errors = validate_boundaries(changed).errors
    assert any(error.startswith("BYPASS_PATH") for error in errors)


def test_viewer_cannot_be_granted_a_write() -> None:
    changed = tuple(
        replace(boundary, required_role=Role.SYNTHETIC_VIEWER)
        if boundary.operation is Operation.WRITE_MEDICAL_RECORD
        else boundary
        for boundary in DEFAULT_BOUNDARIES
    )
    errors = validate_boundaries(changed).errors
    assert any(error.startswith("VIEWER_WRITE") for error in errors)


def test_missing_duplicate_and_unknown_operations_are_rejected() -> None:
    missing = tuple(
        boundary
        for boundary in DEFAULT_BOUNDARIES
        if boundary.operation is not Operation.READ_LAB_RESULT
    )
    assert any(
        error.startswith("MISSING_OPERATION")
        for error in validate_boundaries(missing).errors
    )
    duplicate = (*DEFAULT_BOUNDARIES, DEFAULT_BOUNDARIES[0])
    assert any(
        error.startswith("DUPLICATE_OPERATION")
        for error in validate_boundaries(duplicate).errors
    )
    unknown = (
        *DEFAULT_BOUNDARIES,
        AuthBoundary(operation="read:unknown", required_role=Role.AUDITOR),  # type: ignore[arg-type]
    )
    assert any(
        error.startswith("UNKNOWN_OPERATION")
        for error in validate_boundaries(unknown).errors
    )


def test_assert_valid_boundaries_raises_structured_error() -> None:
    changed = tuple(
        replace(boundary, anonymous_allowed=True)
        if boundary.operation is Operation.WRITE_LAB_ORDER
        else boundary
        for boundary in DEFAULT_BOUNDARIES
    )
    with pytest.raises(ForbiddenSyntheticOperationError) as exc:
        assert_valid_boundaries(changed)
    assert exc.value.code == "FORBIDDEN_SYNTHETIC_OPERATION"
    assert exc.value.status_code == 403


def test_exact_role_match_without_hierarchy_or_anonymous_access() -> None:
    assert is_permitted(
        DEFAULT_BOUNDARIES, Operation.WRITE_LAB_RESULT, Role.LAB_TECHNICIAN
    )
    assert not is_permitted(
        DEFAULT_BOUNDARIES, Operation.WRITE_LAB_RESULT, Role.PLATFORM_ADMIN
    )
    assert not is_permitted(DEFAULT_BOUNDARIES, Operation.READ_ENCOUNTER, Role.ANONYMOUS)
    assert not is_permitted(
        DEFAULT_BOUNDARIES, Operation.READ_ENCOUNTER, Role.LAB_MANAGER
    )


def test_invalid_boundary_set_fails_closed() -> None:
    changed = tuple(
        replace(boundary, anonymous_allowed=True)
        if boundary.operation is Operation.WRITE_LAB_RESULT
        else boundary
        for boundary in DEFAULT_BOUNDARIES
    )
    assert not is_permitted(
        changed, Operation.WRITE_LAB_RESULT, Role.LAB_TECHNICIAN
    )
