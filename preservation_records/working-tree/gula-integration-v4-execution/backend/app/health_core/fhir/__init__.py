"""Synthetic-only FHIR R4 adapter for isolated Health Core development.

Scope is deliberately small and explicit: nine frozen Health Core entity types
map to nine FHIR R4 resources. Every other resource type is rejected. This
package provides real serialisation, deserialisation, synthetic reference and
identifier validation, and a real FHIR R4 ``OperationOutcome`` error mapping.
It is not a FHIR server, not a client, and not production activated.

This is **not** full FHIR R4 compliance: there is no conformance statement, no
terminology server, no capability negotiation, no HTTP interaction and no
national profile binding. See ``GOVERNANCE/PRODUCTION_READINESS/
WS_C_FHIR_R4_REPORT.md`` for evidence and gaps.
"""

from __future__ import annotations

from app.health_core.fhir.adapter import FhirR4Adapter
from app.health_core.fhir.deserializers import deserialize_resource
from app.health_core.fhir.errors import (
    ADAPTER_ISSUE_CODE_BY_ERROR_CODE,
    FHIR_R4_ISSUE_TYPES,
    InvalidFhirResourceError,
    UnsupportedFhirResourceError,
    fhir_issue_code_for,
    operation_outcome_from_error,
)
from app.health_core.fhir.serializers import serialize_entity
from app.health_core.fhir.support import (
    SUPPORTED_FHIR_RESOURCE_TYPES,
    UNSUPPORTED_FHIR_RESOURCE_TYPES,
    validate_identifier,
    validate_reference,
)

__all__ = [
    "ADAPTER_ISSUE_CODE_BY_ERROR_CODE",
    "FHIR_R4_ISSUE_TYPES",
    "SUPPORTED_FHIR_RESOURCE_TYPES",
    "UNSUPPORTED_FHIR_RESOURCE_TYPES",
    "FhirR4Adapter",
    "InvalidFhirResourceError",
    "UnsupportedFhirResourceError",
    "deserialize_resource",
    "fhir_issue_code_for",
    "operation_outcome_from_error",
    "serialize_entity",
    "validate_identifier",
    "validate_reference",
]
