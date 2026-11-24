"""FHIR R4 ``OperationOutcome`` mapping for synthetic Health Core errors.

This module is a pure, in-process adapter: it converts an existing
``HealthCoreError`` into a real FHIR R4 ``OperationOutcome`` JSON dictionary.
It performs no I/O, creates no HTTP response and activates no route.

The shared codes documented in ``contracts.errors.FHIR_ISSUE_CODE_BY_ERROR_CODE``
remain authoritative guidance. Where that guidance uses a legacy shorthand that
is not an R4 issue-type code (``forbidden``/``conflict``), it is canonicalised
to the exact R4 value (``denied``/``duplicate``/``invariant``) before emission.
Workstream-local codes (clinical/lab/adapter) are mapped here deterministically
so that *every* error this package can raise has a real FHIR issue type and no
caller has to invent one.

An ``OperationOutcome.issue.diagnostics`` string is untrusted text. Only an
explicit allowlist of non-sensitive detail keys is emitted, and every emitted
value is HTML-escaped. HTTP/HTML consumers MUST render ``diagnostics`` escaped
(never as raw HTML): it never contains a traceback or a real-world identifier.
"""

from __future__ import annotations

import html
import json
from typing import Final

from app.health_core.clinical.errors import ClinicalValidationError, UnknownClinicalEntityError
from app.health_core.common import HealthCoreError
from app.health_core.contracts.errors import FHIR_ISSUE_CODE_BY_ERROR_CODE
from app.health_core.lab.errors import (
    InvalidActorError,
    InvalidResultError,
    LabWorkflowError,
    UnknownLabEntityError,
    UnknownTestCodeError,
)

__all__ = [
    "ADAPTER_ISSUE_CODE_BY_ERROR_CODE",
    "FHIR_R4_ISSUE_TYPES",
    "InvalidFhirResourceError",
    "UnsupportedFhirResourceError",
    "fhir_issue_code_for",
    "operation_outcome_from_error",
]

#: The only ``error.details`` keys allowed to reach ``diagnostics``. This is an
#: explicit allowlist of *descriptive validation context*, not a deny list:
#: ``field``/``key`` name the offending input, ``reason`` explains the failure,
#: ``expected``/``actual`` describe a value mismatch and ``status`` carries a
#: status value. An audit of this package's ``details=`` call sites shows that
#: many other keys are in common use (``tenant_id``, ``patient_ref``,
#: ``identifier``, ``barcode``, ``order_id`` and other ``*_id`` keys, ``errors``,
#: ...). Those can carry real-world identifiers and are therefore dropped
#: entirely rather than echoed into an untrusted consumer. Unknown future keys
#: are dropped by default for the same reason.
_DIAGNOSTICS_ALLOWED_DETAIL_KEYS: Final[frozenset[str]] = frozenset(
    {"field", "key", "reason", "expected", "actual", "status"}
)

#: The complete R4 ``OperationOutcome.issue.code`` value set. Emitting anything
#: outside this set would produce an invalid OperationOutcome, so guidance values
#: are canonicalised before they reach the wire.
FHIR_R4_ISSUE_TYPES: Final[frozenset[str]] = frozenset(
    {
        "invalid",
        "structure",
        "required",
        "value",
        "period",
        "too-long",
        "code",
        "invariant",
        "security",
        "login",
        "denied",
        "unavailable",
        "duplicate",
        "not-supported",
        "processing",
        "not-found",
        "suppressed",
        "multiple-matches",
        "multiple",
        "exception",
        "timeout",
        "throttled",
        "informational",
    }
)


class UnsupportedFhirResourceError(HealthCoreError):
    """A resource type is outside the explicit synthetic adapter allow-list."""

    code = "UNSUPPORTED_FHIR_RESOURCE"
    status_code = 400


class InvalidFhirResourceError(HealthCoreError):
    """A FHIR JSON resource failed structural or synthetic-value validation."""

    code = "INVALID_FHIR_RESOURCE"
    status_code = 400


#: FHIR R4 issue-type codes for errors that are not part of the 7 shared codes.
#: Every code this adapter can raise is covered; unknown future codes fall back
#: to ``processing`` rather than failing open with an empty or invented mapping.
ADAPTER_ISSUE_CODE_BY_ERROR_CODE: Final[dict[str, str]] = {
    UnsupportedFhirResourceError.code: "not-supported",
    InvalidFhirResourceError.code: "invalid",
    ClinicalValidationError.code: "invalid",
    UnknownClinicalEntityError.code: "not-found",
    LabWorkflowError.code: "processing",
    UnknownLabEntityError.code: "not-found",
    UnknownTestCodeError.code: "not-supported",
    InvalidResultError.code: "invalid",
    InvalidActorError.code: "invalid",
}


#: Legacy guidance shorthands that are not members of the R4 issue-type set.
_LEGACY_GUIDANCE_TO_R4: Final[dict[str, str]] = {
    "forbidden": "denied",
    "conflict": "duplicate",
    "deleted": "not-found",
    "transient": "unavailable",
}

#: Two shared errors share the legacy "conflict" shorthand but differ in R4.
_SHARED_R4_OVERRIDES: Final[dict[str, str]] = {
    "DUPLICATE_ENTITY": "duplicate",
    "INVALID_STATE_TRANSITION": "invariant",
}


def _canonical_issue_code(mapped: object, *, error_code: str) -> str:
    """Return a value from the R4 issue-type set, never a legacy shorthand."""
    if error_code in _SHARED_R4_OVERRIDES:
        return _SHARED_R4_OVERRIDES[error_code]
    candidate = str(mapped)
    if candidate in FHIR_R4_ISSUE_TYPES:
        return candidate
    return _LEGACY_GUIDANCE_TO_R4.get(candidate, "processing")


def fhir_issue_code_for(error: HealthCoreError) -> str:
    """Return the authoritative FHIR R4 issue type for a Health Core error."""
    code = str(error.code)
    if code in FHIR_ISSUE_CODE_BY_ERROR_CODE:
        return _canonical_issue_code(FHIR_ISSUE_CODE_BY_ERROR_CODE[code], error_code=code)
    return _canonical_issue_code(
        ADAPTER_ISSUE_CODE_BY_ERROR_CODE.get(code, "processing"), error_code=code
    )


def _sanitised_diagnostics_details(details: dict[str, object]) -> dict[str, str]:
    """Return only allow-listed keys, each HTML-escaped before serialisation.

    Non-string values are stringified first so every emitted value is a plain
    escaped string; this keeps the JSON deterministic and free of raw markup.
    """
    return {
        key: html.escape(str(value), quote=True)
        for key, value in details.items()
        if key in _DIAGNOSTICS_ALLOWED_DETAIL_KEYS
    }


def operation_outcome_from_error(error: HealthCoreError) -> dict[str, object]:
    """Map a Health Core error into a real FHIR R4 ``OperationOutcome`` dict.

    ``severity`` is derived from the error's HTTP-equivalent status so it never
    disagrees with the canonical envelope. ``diagnostics`` carries the stable
    machine code, the client-safe message and a sanitised subset of structured
    details; it never includes an exception traceback or a real-world identifier.

    ``diagnostics`` is **untrusted text**. Only the allow-listed detail keys in
    ``_DIAGNOSTICS_ALLOWED_DETAIL_KEYS`` survive, and each value is HTML-escaped
    with ``html.escape(str(value), quote=True)`` before JSON serialisation; all
    other keys are dropped. HTTP/HTML consumers MUST still render it escaped
    (never as raw HTML). The emitted string is a valid FHIR R4 ``string`` and
    the OperationOutcome shape is unchanged.
    """
    details = _sanitised_diagnostics_details(error.details)
    diagnostics = f"{error.code}: {error.message}"
    if details:
        diagnostics += " | " + json.dumps(details, sort_keys=True, separators=(",", ":"))
    severity = "fatal" if int(error.status_code) >= 500 else "error"
    return {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": severity,
                "code": fhir_issue_code_for(error),
                "diagnostics": diagnostics,
            }
        ],
    }
