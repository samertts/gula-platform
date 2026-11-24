"""Contract tests: every shared Health Core error maps to the stable shape."""

from __future__ import annotations

import pytest
from app.health_core.common import (
    DuplicateEntityError,
    ForbiddenSyntheticOperationError,
    HealthCoreError,
    InvalidStateTransitionError,
    InvalidSyntheticReferenceError,
    TenantMismatchError,
    UnknownPatientError,
)
from app.health_core.contracts.errors import (
    ERROR_CATALOGUE,
    HealthCoreErrorResponse,
    error_response_from,
)
from pydantic import ValidationError

SHARED_ERRORS = (
    HealthCoreError,
    InvalidSyntheticReferenceError,
    UnknownPatientError,
    TenantMismatchError,
    DuplicateEntityError,
    InvalidStateTransitionError,
    ForbiddenSyntheticOperationError,
)
TIMESTAMP = "2026-11-18T10:00:00+00:00"


def test_all_shared_error_codes_are_catalogued() -> None:
    assert set(ERROR_CATALOGUE) == {error_class.code for error_class in SHARED_ERRORS}
    for code, error_class in ERROR_CATALOGUE.items():
        assert error_class.code == code


@pytest.mark.parametrize("error_class", SHARED_ERRORS)
def test_shared_error_code_maps_correctly(error_class: type[HealthCoreError]) -> None:
    error = error_class("client-safe message", details={"field": "patient_ref"})
    response = error_response_from(error, request_id="SYN-REQ-1", timestamp=TIMESTAMP)
    assert response.code == error.code
    assert response.status_code == error.status_code
    assert response.retryable == error.retryable
    assert response.message == "client-safe message"
    assert response.detail == response.message
    assert response.detail_ar == response.message
    assert response.request_id == "SYN-REQ-1"
    assert response.timestamp == TIMESTAMP
    assert response.details == {"field": "patient_ref"}


@pytest.mark.parametrize("error_class", SHARED_ERRORS)
def test_mapped_error_response_is_serialisable(error_class: type[HealthCoreError]) -> None:
    response = error_response_from(error_class("msg"), timestamp=TIMESTAMP)
    encoded = response.model_dump_json()
    assert error_class.code in encoded
    assert HealthCoreErrorResponse.model_validate_json(encoded) == response


def test_retryable_flag_is_preserved() -> None:
    class RetryableError(HealthCoreError):
        code = "RETRYABLE_SYNTHETIC"
        status_code = 503
        retryable = True

    response = error_response_from(RetryableError("try again"), timestamp=TIMESTAMP)
    assert response.retryable is True
    assert response.status_code == 503


def test_default_request_id_is_unknown() -> None:
    response = error_response_from(HealthCoreError("msg"), timestamp=TIMESTAMP)
    assert response.request_id == "unknown"


def test_error_response_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        HealthCoreErrorResponse(
            code="X",
            message="m",
            status_code=400,
            retryable=False,
            timestamp=TIMESTAMP,
            detail="m",
            detail_ar="m",
            unexpected="x",
        )


def test_error_codes_are_stable_strings() -> None:
    assert DuplicateEntityError.code == "DUPLICATE_ENTITY"
    assert DuplicateEntityError.status_code == 409
    assert UnknownPatientError.status_code == 404
    assert TenantMismatchError.status_code == 403
    assert ForbiddenSyntheticOperationError.status_code == 403
