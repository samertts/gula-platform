"""Explicit resource support, synthetic identifiers and reference validation.

The adapter is allow-list driven: a resource type is serialisable only when it
appears in :data:`SUPPORTED_FHIR_RESOURCE_TYPES`, and anything else is rejected
with :class:`UnsupportedFhirResourceError`. The separate
:data:`UNSUPPORTED_FHIR_RESOURCE_TYPES` tuple documents the national/adjacent
types that were consciously considered and deliberately left out; it is
documentation, not an exhaustive list of every FHIR R4 resource.

Every identifier and reference is opaque and ``SYN-`` prefixed. All values pass
through the shared ``reject_national_identifier`` and ``is_synthetic_id``
helpers before they can enter or leave a FHIR resource.
"""

from __future__ import annotations

import math
from typing import Final, cast

from app.health_core.clinical.entities import (
    Diagnosis,
    Encounter,
    EncounterStatus,
    Facility,
    Observation,
    Organization,
    Practitioner,
)
from app.health_core.common import (
    InvalidSyntheticReferenceError,
    is_synthetic_id,
    reject_national_identifier,
)
from app.health_core.contracts.version import HEALTH_CORE_CONTRACT_VERSION
from app.health_core.fhir.errors import InvalidFhirResourceError, UnsupportedFhirResourceError
from app.health_core.lab.models import LabOrder, LabOrderStatus, LabResult, Specimen, SpecimenStatus

__all__ = [
    "ENCOUNTER_STATUS_TO_FHIR",
    "EXTENSION_BASE",
    "IDENTIFIER_SYSTEM",
    "ORDER_STATUS_TO_FHIR",
    "PROFILE_BASE",
    "REFERENCE_TARGET_PREFIXES",
    "SPECIMEN_STATUS_TO_FHIR",
    "SUPPORTED_FHIR_RESOURCE_TYPES",
    "UNSUPPORTED_FHIR_RESOURCE_TYPES",
    "entity_type_for",
    "extension_boolean",
    "extension_code",
    "extension_datetime",
    "extension_decimal",
    "extension_integer",
    "extension_nested",
    "extension_quantity",
    "extension_string",
    "find_extension",
    "make_identifier",
    "make_reference",
    "profile_for",
    "require_bool",
    "require_dict",
    "require_extension",
    "require_extension_code",
    "require_extension_string",
    "require_finite",
    "require_int",
    "require_list",
    "require_str",
    "require_synthetic_value",
    "resource_type_for",
    "validate_identifier",
    "validate_reference",
]

FhirResource = dict[str, object]

# Synthetic, local URIs. Nothing here claims a national namespace or a real
# terminology binding; the version is the local Health Core contract version.
IDENTIFIER_SYSTEM: Final[str] = "urn:gula:synthetic:fhir:R4:identifier"
BARCODE_SYSTEM: Final[str] = "urn:gula:synthetic:fhir:R4:barcode"
CODE_SYSTEM: Final[str] = "urn:gula:synthetic:fhir:R4:CodeSystem/local"
TEST_CODE_SYSTEM: Final[str] = "urn:gula:synthetic:fhir:R4:CodeSystem/test"
UCUM_SYSTEM: Final[str] = "http://unitsofmeasure.org"
PROFILE_BASE: Final[str] = "urn:gula:synthetic:fhir:R4:StructureDefinition/synthetic-"
EXTENSION_BASE: Final[str] = "urn:gula:synthetic:fhir:R4:extension/"
SYNTHETIC_VERSION: Final[str] = HEALTH_CORE_CONTRACT_VERSION

EXT_TENANT: Final[str] = EXTENSION_BASE + "tenant"
EXT_PATIENT_LABEL: Final[str] = EXTENSION_BASE + "patient-label"
EXT_PRACTITIONER_ROLE: Final[str] = EXTENSION_BASE + "practitioner-role"
EXT_ENCOUNTER_STATUS: Final[str] = EXTENSION_BASE + "encounter-status"
EXT_ORDER_STATUS: Final[str] = EXTENSION_BASE + "order-status"
EXT_ORDER_IDEMPOTENCY: Final[str] = EXTENSION_BASE + "order-idempotency-key"
EXT_ORDER_CANCELLED_AT: Final[str] = EXTENSION_BASE + "order-cancelled-at"
EXT_ORDER_CANCELLATION_REASON: Final[str] = EXTENSION_BASE + "order-cancellation-reason"
EXT_SPECIMEN_STATUS: Final[str] = EXTENSION_BASE + "specimen-status"
EXT_SPECIMEN_REJECTION_REASON: Final[str] = EXTENSION_BASE + "specimen-rejection-reason"
EXT_RESULT_VALUE: Final[str] = EXTENSION_BASE + "result-value"
EXT_RESULT_RANGE: Final[str] = EXTENSION_BASE + "result-reference-range"
EXT_RESULT_CRITICAL: Final[str] = EXTENSION_BASE + "result-critical-flag"
EXT_RESULT_IDEMPOTENCY: Final[str] = EXTENSION_BASE + "result-idempotency-key"
EXT_AMENDMENT: Final[str] = EXTENSION_BASE + "result-amendment"
EXT_AMENDMENT_ID: Final[str] = EXTENSION_BASE + "amendment-id"
EXT_AMENDMENT_PREVIOUS: Final[str] = EXTENSION_BASE + "amendment-previous-value"
EXT_AMENDMENT_NEW: Final[str] = EXTENSION_BASE + "amendment-new-value"
EXT_AMENDMENT_REASON: Final[str] = EXTENSION_BASE + "amendment-reason"
EXT_AMENDMENT_ACTOR: Final[str] = EXTENSION_BASE + "amendment-actor"
EXT_AMENDMENT_AT: Final[str] = EXTENSION_BASE + "amendment-occurred-at"
EXT_AMENDMENT_VERSION: Final[str] = EXTENSION_BASE + "amendment-version"

# The authoritative allow-list. Each entry maps one frozen internal entity to
# one small, honestly scoped FHIR R4 resource. Nine resources only.
ENTITY_TYPE_BY_RESOURCE: Final[dict[str, type[object]]] = {
    "Practitioner": Practitioner,
    "Organization": Organization,
    "Location": Facility,
    "Encounter": Encounter,
    "Condition": Diagnosis,
    "Observation": Observation,
    "ServiceRequest": LabOrder,
    "Specimen": Specimen,
    "DiagnosticReport": LabResult,
}

SUPPORTED_FHIR_RESOURCE_TYPES: Final[tuple[str, ...]] = tuple(ENTITY_TYPE_BY_RESOURCE)

RESOURCE_TYPE_BY_ENTITY: Final[dict[type[object], str]] = {
    entity_type: resource_type for resource_type, entity_type in ENTITY_TYPE_BY_RESOURCE.items()
}

# Patient is NOT a supported top-level resource: no Patient entity exists in the
# synthetic slice and no identity link may be fabricated. It is allowed only as
# an opaque reference target (``Patient/SYN-PAT-...``).
UNSUPPORTED_FHIR_RESOURCE_TYPES: Final[tuple[str, ...]] = (
    "Patient",
    "MedicationRequest",
    "MedicationStatement",
    "AllergyIntolerance",
    "Immunization",
    "CarePlan",
    "DocumentReference",
    "Composition",
    "Procedure",
    "Bundle",
    "Goal",
    "Device",
    "Provenance",
    "Claim",
    "Coverage",
    "AuditEvent",
    "Questionnaire",
    "FamilyMemberHistory",
    "RelatedPerson",
    "Person",
    "Group",
    "SupplyRequest",
    "NutritionOrder",
    "RiskAssessment",
    "ImagingStudy",
    "Appointment",
    "Schedule",
    "CapabilityStatement",
)

# Reference target type -> required synthetic id prefix. A type/prefix mismatch
# is a cross-resource reference error and is rejected, never coerced.
REFERENCE_TARGET_PREFIXES: Final[dict[str, str]] = {
    "Patient": "SYN-PAT-",
    "Practitioner": "SYN-PRC-",
    "Organization": "SYN-ORG-",
    "Location": "SYN-FAC-",
    "Encounter": "SYN-ENC-",
    "Condition": "SYN-DIA-",
    "Observation": "SYN-OBS-",
    "ServiceRequest": "SYN-ORD-",
    "Specimen": "SYN-SPC-",
    "DiagnosticReport": "SYN-RES-",
}

# Internal lifecycle states are richer than the corresponding FHIR status
# ValueSets. The exact internal state is preserved in a local extension and is
# validated against the FHIR status on deserialisation, so nothing is coerced.
ENCOUNTER_STATUS_TO_FHIR: Final[dict[EncounterStatus, str]] = {
    EncounterStatus.PLANNED: "planned",
    EncounterStatus.IN_PROGRESS: "in-progress",
    EncounterStatus.ADMITTED: "in-progress",
    EncounterStatus.TRANSFERRED: "in-progress",
    EncounterStatus.DISCHARGED: "finished",
    EncounterStatus.CANCELLED: "cancelled",
}

ORDER_STATUS_TO_FHIR: Final[dict[LabOrderStatus, str]] = {
    LabOrderStatus.PLACED: "active",
    LabOrderStatus.CANCELLED: "revoked",
}

SPECIMEN_STATUS_TO_FHIR: Final[dict[SpecimenStatus, str]] = {
    SpecimenStatus.REGISTERED: "available",
    SpecimenStatus.COLLECTED: "available",
    SpecimenStatus.RECEIVED: "available",
    SpecimenStatus.IN_TESTING: "available",
    SpecimenStatus.REJECTED: "unsatisfactory",
    SpecimenStatus.FINAL: "available",
}

SPECIMEN_TYPE_TEXT: Final[str] = "synthetic specimen"


def profile_for(resource_type: str) -> str:
    """Return the versioned local synthetic profile canonical for a resource type."""
    return f"{PROFILE_BASE}{resource_type}|{SYNTHETIC_VERSION}"


def resource_type_for(entity: object) -> str:
    """Return the supported resource type for an internal entity or fail closed."""
    resource_type = RESOURCE_TYPE_BY_ENTITY.get(type(entity))
    if resource_type is None:
        raise UnsupportedFhirResourceError(
            "internal entity type has no synthetic FHIR mapping",
            details={"entity_type": type(entity).__name__},
        )
    return resource_type


def entity_type_for(resource_type: object) -> type[object]:
    """Return the internal entity type for a supported resource type or fail closed."""
    if not isinstance(resource_type, str) or resource_type not in ENTITY_TYPE_BY_RESOURCE:
        rejected = resource_type if isinstance(resource_type, str) else type(resource_type).__name__
        if isinstance(resource_type, str) and resource_type in UNSUPPORTED_FHIR_RESOURCE_TYPES:
            raise UnsupportedFhirResourceError(
                "resource type is explicitly unsupported by the synthetic adapter",
                details={"resourceType": resource_type},
            )
        raise InvalidFhirResourceError(
            "resource type is not a supported synthetic FHIR resource",
            details={"resourceType": rejected},
        )
    return ENTITY_TYPE_BY_RESOURCE[resource_type]


def require_dict(value: object, *, field: str) -> dict[str, object]:
    """Accept a JSON object, otherwise raise a structured adapter error."""
    if not isinstance(value, dict):
        raise InvalidFhirResourceError(
            f"{field} must be a JSON object", details={"field": field}
        )
    return cast(dict[str, object], value)


def require_list(value: object, *, field: str) -> list[object]:
    """Accept a JSON array, otherwise raise a structured adapter error."""
    if not isinstance(value, list):
        raise InvalidFhirResourceError(
            f"{field} must be a JSON array", details={"field": field}
        )
    return cast(list[object], value)


def require_str(value: object, *, field: str, max_length: int = 256) -> str:
    """Accept a non-empty bounded string, otherwise raise a structured error."""
    if not isinstance(value, str) or not value or len(value) > max_length:
        raise InvalidFhirResourceError(
            f"{field} must be a non-empty string of at most {max_length} characters",
            details={"field": field},
        )
    return value


def require_bool(value: object, *, field: str) -> bool:
    """Accept only a real boolean (JSON booleans must not be coerced)."""
    if not isinstance(value, bool):
        raise InvalidFhirResourceError(f"{field} must be a boolean", details={"field": field})
    return value


def require_int(value: object, *, field: str) -> int:
    """Accept only an integer (JSON booleans must not be coerced)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidFhirResourceError(f"{field} must be an integer", details={"field": field})
    return value


def require_finite(value: object, *, field: str) -> float:
    """Accept a finite real number and reject booleans, text, NaN and infinity."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidFhirResourceError(f"{field} must be a finite number", details={"field": field})
    number = float(value)
    if not math.isfinite(number):
        raise InvalidFhirResourceError(f"{field} must be a finite number", details={"field": field})
    return number


def require_synthetic_value(value: object, *, field: str, prefix: str | None = None) -> str:
    """Accept only an opaque ``SYN-`` value, optionally of one exact kind."""
    text = require_str(value, field=field)
    reject_national_identifier(text, field=field)
    if not is_synthetic_id(text):
        raise InvalidSyntheticReferenceError(
            f"{field} must be a SYN- prefixed synthetic reference",
            details={"field": field},
        )
    if prefix is not None and not text.startswith(prefix):
        raise InvalidSyntheticReferenceError(
            f"{field} does not match its resource kind (cross-resource mismatch)",
            details={"field": field, "expected_prefix": prefix},
        )
    return text


def validate_reference(
    value: object,
    *,
    expected_type: str,
    field: str,
    expected_prefix: str | None = None,
) -> str:
    """Validate a FHIR ``Reference`` and return its synthetic id part.

    Only ``{"reference": "Type/SYN-..."}`` is accepted. Display strings,
    absolute URLs, wrong target types and type/prefix mismatches are rejected.
    """
    obj = require_dict(value, field=field)
    if set(obj) != {"reference"}:
        raise InvalidFhirResourceError(
            f"{field} must carry only a reference string",
            details={"field": field, "keys": sorted(obj)},
        )
    raw = require_str(obj["reference"], field=f"{field}.reference")
    parts = raw.split("/")
    if len(parts) != 2 or not all(parts) or any(c.isspace() for c in raw):
        raise InvalidFhirResourceError(
            f"{field} must be a relative 'Type/SYN-...' reference",
            details={"field": field},
        )
    target_type, target_id = parts
    if target_type not in REFERENCE_TARGET_PREFIXES:
        raise InvalidFhirResourceError(
            f"{field} targets an unknown resource type",
            details={"field": field, "targetType": target_type},
        )
    if target_type != expected_type:
        raise InvalidFhirResourceError(
            f"{field} has a cross-resource reference type mismatch",
            details={"field": field, "expected": expected_type, "actual": target_type},
        )
    prefix = expected_prefix or REFERENCE_TARGET_PREFIXES[target_type]
    return require_synthetic_value(target_id, field=f"{field}.id", prefix=prefix)


def validate_identifier(
    value: object,
    *,
    expected_system: str,
    field: str,
    expected_prefix: str | None = None,
) -> str:
    """Validate a synthetic FHIR identifier and return its opaque value."""
    obj = require_dict(value, field=field)
    if set(obj) != {"system", "value"}:
        raise InvalidFhirResourceError(
            f"{field} must carry exactly a system and a value",
            details={"field": field, "keys": sorted(obj)},
        )
    system = require_str(obj["system"], field=f"{field}.system")
    if system != expected_system:
        raise InvalidFhirResourceError(
            f"{field} uses an unexpected identifier system",
            details={"field": field, "system": system},
        )
    return require_synthetic_value(
        obj["value"], field=f"{field}.value", prefix=expected_prefix
    )


def make_reference(target_type: str, synthetic_id: str, *, field: str) -> dict[str, object]:
    """Build and validate a relative ``Type/SYN-...`` FHIR reference."""
    reference: dict[str, object] = {"reference": f"{target_type}/{synthetic_id}"}
    validate_reference(reference, expected_type=target_type, field=field)
    return reference


def make_identifier(
    synthetic_id: str,
    *,
    field: str,
    system: str = IDENTIFIER_SYSTEM,
    expected_prefix: str | None = None,
) -> dict[str, object]:
    """Build and validate one opaque synthetic FHIR identifier."""
    identifier: dict[str, object] = {"system": system, "value": synthetic_id}
    validate_identifier(
        identifier, expected_system=system, field=field, expected_prefix=expected_prefix
    )
    return identifier


def extension_code(url: str, code: str) -> dict[str, object]:
    """Return a FHIR extension carrying a ``valueCode``."""
    return {"url": url, "valueCode": code}


def extension_string(url: str, text: str) -> dict[str, object]:
    """Return a FHIR extension carrying a ``valueString``."""
    return {"url": url, "valueString": text}


def extension_boolean(url: str, flag: bool) -> dict[str, object]:
    """Return a FHIR extension carrying a ``valueBoolean``."""
    return {"url": url, "valueBoolean": flag}


def extension_integer(url: str, number: int) -> dict[str, object]:
    """Return a FHIR extension carrying a ``valueInteger``."""
    return {"url": url, "valueInteger": number}


def extension_decimal(url: str, number: float) -> dict[str, object]:
    """Return a FHIR extension carrying a ``valueDecimal``."""
    return {"url": url, "valueDecimal": number}


def extension_quantity(url: str, number: float, unit: str) -> dict[str, object]:
    """Return a FHIR extension carrying a UCUM-style ``valueQuantity``."""
    return {
        "url": url,
        "valueQuantity": {
            "value": number,
            "unit": unit,
            "system": UCUM_SYSTEM,
            "code": unit,
        },
    }


def extension_datetime(url: str, moment: str) -> dict[str, object]:
    """Return a FHIR extension carrying a ``valueDateTime``."""
    return {"url": url, "valueDateTime": moment}


def extension_nested(url: str, children: list[dict[str, object]]) -> dict[str, object]:
    """Return a FHIR extension carrying nested child extensions."""
    return {"url": url, "extension": children}


def find_extension(resource: dict[str, object], url: str) -> dict[str, object] | None:
    """Find one local extension by URL, failing closed on malformed containers."""
    extensions = resource.get("extension")
    if extensions is None:
        return None
    for item in require_list(extensions, field="extension"):
        child = require_dict(item, field="extension[]")
        if child.get("url") == url:
            return child
    return None


def require_extension(resource: dict[str, object], url: str, *, field: str) -> dict[str, object]:
    """Require a local extension by URL."""
    extension = find_extension(resource, url)
    if extension is None:
        raise InvalidFhirResourceError(
            f"{field} is required for synthetic resources",
            details={"field": field, "url": url},
        )
    return extension


def require_extension_code(extension: dict[str, object], *, field: str) -> str:
    """Read and validate the ``valueCode`` of a local extension."""
    return require_str(extension.get("valueCode"), field=f"{field}.valueCode")


def require_extension_string(extension: dict[str, object], *, field: str) -> str:
    """Read and validate the ``valueString`` of a local extension."""
    return require_str(extension.get("valueString"), field=f"{field}.valueString")
