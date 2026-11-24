"""OperationOutcome coverage for every Health Core error code the adapter can see."""

from __future__ import annotations

import json
from typing import Final

import pytest
from app.health_core.clinical.errors import ClinicalValidationError, UnknownClinicalEntityError
from app.health_core.common import HealthCoreError
from app.health_core.contracts.errors import ERROR_CATALOGUE, FHIR_ISSUE_CODE_BY_ERROR_CODE
from app.health_core.fhir import (
    ADAPTER_ISSUE_CODE_BY_ERROR_CODE,
    FHIR_R4_ISSUE_TYPES,
    FhirR4Adapter,
    InvalidFhirResourceError,
    UnsupportedFhirResourceError,
    fhir_issue_code_for,
    operation_outcome_from_error,
)
from app.health_core.lab.errors import (
    InvalidActorError,
    InvalidResultError,
    LabWorkflowError,
    UnknownLabEntityError,
    UnknownTestCodeError,
)

LOCAL_ERROR_CLASSES: Final[dict[str, type[HealthCoreError]]] = {
    cls.code: cls
    for cls in (
        UnsupportedFhirResourceError,
        InvalidFhirResourceError,
        ClinicalValidationError,
        UnknownClinicalEntityError,
        LabWorkflowError,
        UnknownLabEntityError,
        UnknownTestCodeError,
        InvalidResultError,
        InvalidActorError,
    )
}

# Expected R4 values are written independently of the adapter maps so a wrong
# map cannot pass by agreeing with itself. The first seven are the documented
# shared codes, canonicalised where the shared guidance is a legacy shorthand.
EXPECTED_R4_BY_ERROR_CODE: Final[dict[str, str]] = {
    "HEALTH_CORE_ERROR": "processing",
    "INVALID_SYNTHETIC_REFERENCE": "invalid",
    "UNKNOWN_PATIENT": "not-found",
    "TENANT_MISMATCH": "denied",
    "DUPLICATE_ENTITY": "duplicate",
    "INVALID_STATE_TRANSITION": "invariant",
    "FORBIDDEN_SYNTHETIC_OPERATION": "denied",
    "UNSUPPORTED_FHIR_RESOURCE": "not-supported",
    "INVALID_FHIR_RESOURCE": "invalid",
    "CLINICAL_VALIDATION_ERROR": "invalid",
    "UNKNOWN_CLINICAL_ENTITY": "not-found",
    "LAB_WORKFLOW_ERROR": "processing",
    "UNKNOWN_LAB_ENTITY": "not-found",
    "UNKNOWN_TEST_CODE": "not-supported",
    "INVALID_RESULT": "invalid",
    "INVALID_ACTOR": "invalid",
}

LEGACY_SHORTHANDS: Final[frozenset[str]] = frozenset(
    {"forbidden", "conflict", "deleted", "transient"}
)


def _all_error_classes() -> dict[str, type[HealthCoreError]]:
    """Return every error class covered by the adapter, keyed by stable code."""
    return {**ERROR_CATALOGUE, **LOCAL_ERROR_CLASSES}


def test_error_code_coverage_is_explicit_and_complete() -> None:
    """No error code can reach this package without an explicit R4 mapping."""
    all_classes = _all_error_classes()
    assert not set(ERROR_CATALOGUE) & set(LOCAL_ERROR_CLASSES)
    assert set(FHIR_ISSUE_CODE_BY_ERROR_CODE) <= set(ERROR_CATALOGUE)
    assert set(ADAPTER_ISSUE_CODE_BY_ERROR_CODE) <= set(LOCAL_ERROR_CLASSES)
    assert set(all_classes) == set(EXPECTED_R4_BY_ERROR_CODE)
    assert set(EXPECTED_R4_BY_ERROR_CODE.values()) <= FHIR_R4_ISSUE_TYPES


@pytest.mark.parametrize("code", sorted(EXPECTED_R4_BY_ERROR_CODE))
def test_every_mapped_code_produces_a_real_operation_outcome(code: str) -> None:
    """Each code emits exactly one R4 issue with valid severity and diagnostics."""
    error_class = _all_error_classes()[code]
    error = error_class("synthetic failure", details={"field": "id"})
    outcome = operation_outcome_from_error(error)

    assert outcome["resourceType"] == "OperationOutcome"
    issues = outcome["issue"]
    assert isinstance(issues, list)
    assert len(issues) == 1
    issue = issues[0]
    assert isinstance(issue, dict)
    assert set(issue) == {"severity", "code", "diagnostics"}
    assert issue["severity"] == ("fatal" if error.status_code >= 500 else "error")
    assert issue["code"] == EXPECTED_R4_BY_ERROR_CODE[code]
    assert issue["code"] in FHIR_R4_ISSUE_TYPES
    diagnostics = issue["diagnostics"]
    assert isinstance(diagnostics, str)
    assert code in diagnostics
    assert "synthetic failure" in diagnostics
    assert json.dumps({"field": "id"}, sort_keys=True, separators=(",", ":")) in diagnostics


def test_shared_guidance_is_used_but_legacy_shorthands_are_canonicalised() -> None:
    """Valid shared guidance is preserved; non-R4 shorthands never reach the wire."""
    for code, guidance in FHIR_ISSUE_CODE_BY_ERROR_CODE.items():
        actual = fhir_issue_code_for(ERROR_CATALOGUE[code]("synthetic failure"))
        assert actual in FHIR_R4_ISSUE_TYPES
        assert actual not in LEGACY_SHORTHANDS
        if guidance in FHIR_R4_ISSUE_TYPES:
            assert actual == guidance
        else:
            assert guidance in LEGACY_SHORTHANDS
            assert actual in {"denied", "duplicate", "invariant"}


def test_adapter_local_codes_have_explicit_r4_values() -> None:
    """Clinical, lab and adapter codes are mapped, not guessed by the caller."""
    for code, error_class in LOCAL_ERROR_CLASSES.items():
        assert fhir_issue_code_for(error_class("synthetic failure")) == EXPECTED_R4_BY_ERROR_CODE[
            code
        ]
        assert ADAPTER_ISSUE_CODE_BY_ERROR_CODE[code] in FHIR_R4_ISSUE_TYPES


def test_diagnostics_are_deterministic_and_carry_no_exception_text() -> None:
    """The same error always yields the same sanitised diagnostics string.

    Neither ``b`` nor ``a`` is an allow-listed detail key, so the whole details
    fragment is dropped: only the stable machine code and client-safe message
    remain. This is the strict post-allowlist expectation for this input.
    """
    error = InvalidFhirResourceError(
        "synthetic resource rejected", details={"b": 2, "a": {"field": "id"}}
    )
    expected_diagnostics = "INVALID_FHIR_RESOURCE: synthetic resource rejected"
    expected = {
        "resourceType": "OperationOutcome",
        "issue": [
            {"severity": "error", "code": "invalid", "diagnostics": expected_diagnostics}
        ],
    }
    assert operation_outcome_from_error(error) == expected
    assert operation_outcome_from_error(error) == expected


def test_fatal_severity_and_unknown_code_fallback_are_bounded() -> None:
    """A future error code cannot emit an invented issue type or success shape."""

    class FutureHealthCoreError(HealthCoreError):
        code = "SYNTHETIC_FUTURE_ERROR"
        status_code = 503

    outcome = operation_outcome_from_error(FutureHealthCoreError("synthetic unavailable"))
    issues = outcome["issue"]
    assert isinstance(issues, list)
    assert len(issues) == 1
    issue = issues[0]
    assert isinstance(issue, dict)
    assert issue["severity"] == "fatal"
    assert issue["code"] == "processing"
    assert issue["code"] in FHIR_R4_ISSUE_TYPES


def test_adapter_facade_uses_the_same_outcome_mapping() -> None:
    """The public facade does not fork the deterministic error mapping."""
    error = UnsupportedFhirResourceError(
        "synthetic resource type rejected", details={"resourceType": "Patient"}
    )
    assert FhirR4Adapter().operation_outcome(error) == operation_outcome_from_error(error)


def test_diagnostics_allowlist_escapes_markup_and_drops_sensitive_keys() -> None:
    """Untrusted detail markup is HTML-escaped; disallowed keys never reach diagnostics."""
    error = InvalidFhirResourceError(
        "synthetic resource rejected",
        details={
            "reason": "<script>alert(1)</script>",
            "field": "<b>x</b>",
            "tenant_id": "<script>alert(2)</script>",
        },
    )
    outcome = operation_outcome_from_error(error)
    assert outcome["resourceType"] == "OperationOutcome"
    issues = outcome["issue"]
    assert isinstance(issues, list)
    assert len(issues) == 1
    issue = issues[0]
    assert isinstance(issue, dict)
    assert set(issue) == {"severity", "code", "diagnostics"}
    assert issue["severity"] == "error"
    assert issue["code"] == "invalid"
    assert issue["code"] in FHIR_R4_ISSUE_TYPES
    diagnostics = issue["diagnostics"]
    assert isinstance(diagnostics, str)

    # Raw markup supplied by a client is never echoed verbatim.
    assert "<script>" not in diagnostics
    assert "<b>" not in diagnostics

    # Allow-listed keys survive, HTML-escaped before JSON serialisation. The
    # escaped <script> form is present for the allowed "reason" key.
    expected_details = json.dumps(
        {
            "field": "&lt;b&gt;x&lt;/b&gt;",
            "reason": "&lt;script&gt;alert(1)&lt;/script&gt;",
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    assert expected_details in diagnostics

    # The identifier-bearing key and its value are dropped entirely.
    assert "tenant_id" not in diagnostics
    assert "alert(2)" not in diagnostics
    assert "&lt;script&gt;alert(2)&lt;/script&gt;" not in diagnostics

    # Stable machine code and client-safe message prefix are unchanged.
    assert diagnostics.startswith("INVALID_FHIR_RESOURCE: synthetic resource rejected | ")


def test_diagnostics_escapes_quotes_ampersands_and_non_string_values() -> None:
    """quote=True escaping and stringification keep every emitted value plain text."""
    error = InvalidFhirResourceError(
        "synthetic resource rejected",
        details={"field": 'a"b\'c&<d>', "status": 503},
    )
    issues = operation_outcome_from_error(error)["issue"]
    assert isinstance(issues, list)
    assert len(issues) == 1
    issue = issues[0]
    assert isinstance(issue, dict)
    diagnostics = issue["diagnostics"]
    assert isinstance(diagnostics, str)
    expected_details = json.dumps(
        {"field": "a&quot;b&#x27;c&amp;&lt;d&gt;", "status": "503"},
        sort_keys=True,
        separators=(",", ":"),
    )
    assert expected_details in diagnostics
    assert "<d>" not in diagnostics


def test_diagnostics_allowlist_is_explicit_and_closed() -> None:
    """Exactly the six documented keys are retained; any other key is dropped."""
    error = InvalidFhirResourceError(
        "synthetic resource rejected",
        details={
            "field": "f",
            "key": "k",
            "reason": "r",
            "expected": "e",
            "actual": "a",
            "status": "s",
            "label": "dropped",
            "resourceType": "dropped",
        },
    )
    issues = operation_outcome_from_error(error)["issue"]
    assert isinstance(issues, list)
    assert len(issues) == 1
    issue = issues[0]
    assert isinstance(issue, dict)
    diagnostics = issue["diagnostics"]
    assert isinstance(diagnostics, str)
    expected_details = json.dumps(
        {"actual": "a", "expected": "e", "field": "f", "key": "k", "reason": "r", "status": "s"},
        sort_keys=True,
        separators=(",", ":"),
    )
    assert expected_details in diagnostics
    assert "dropped" not in diagnostics
