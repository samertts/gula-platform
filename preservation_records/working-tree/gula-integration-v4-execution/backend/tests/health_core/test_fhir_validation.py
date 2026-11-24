"""Negative FHIR R4 adapter tests: fail closed on malformed or real-looking data."""

from __future__ import annotations

import copy
from typing import Any

import pytest
from app.health_core.common import InvalidSyntheticReferenceError, is_synthetic_id
from app.health_core.fhir import (
    FhirR4Adapter,
    InvalidFhirResourceError,
    UnsupportedFhirResourceError,
    validate_identifier,
    validate_reference,
)
from app.health_core.fhir.support import (
    EXT_ENCOUNTER_STATUS,
    EXT_ORDER_STATUS,
    EXT_TENANT,
    IDENTIFIER_SYSTEM,
    REFERENCE_TARGET_PREFIXES,
)

from tests.health_core.test_fhir_roundtrip import (
    ADAPTER,
    PATIENT,
    encounter,
    order,
    organization,
    practitioner,
    specimen,
)


def _fresh(kind: str) -> dict[str, Any]:
    """Return a valid serialised resource for one supported entity."""
    builders = {
        "encounter": encounter,
        "organization": organization,
        "order": order,
        "practitioner": practitioner,
        "specimen": specimen,
    }
    return dict(ADAPTER.serialize(builders[kind]()))


def _set_extension(resource: dict[str, Any], url: str, key: str, value: object) -> None:
    """Replace one named extension value in a resource under test."""
    extensions = resource["extension"]
    assert isinstance(extensions, list)
    for extension in extensions:
        assert isinstance(extension, dict)
        if extension.get("url") == url:
            extension[key] = value
            return
    raise AssertionError(f"extension {url} not found")


@pytest.mark.parametrize(
    "reference",
    (
        "Patient/1234567890123",
        "Patient/ABCDEF123456789",
        "Patient/abc",
        "not-a-reference",
        "http://example.org/Patient/SYN-PAT-000000000001",
        "Device/SYN-DEV-000000000001",
        "Patient/SYN-PAT-000000000001/extra",
    ),
)
def test_invalid_reference_is_rejected(reference: str) -> None:
    """Only exact relative Type/SYN-... references are accepted."""
    resource = _fresh("encounter")
    resource["subject"] = {"reference": reference}
    with pytest.raises((InvalidFhirResourceError, InvalidSyntheticReferenceError)):
        ADAPTER.deserialize(resource)


def test_reference_with_display_or_extra_keys_is_rejected() -> None:
    """Ambiguous Reference objects are never silently coerced."""
    resource = _fresh("encounter")
    resource["subject"] = {
        "reference": "Patient/SYN-PAT-000000000001",
        "display": "not a synthetic field",
    }
    with pytest.raises(InvalidFhirResourceError):
        ADAPTER.deserialize(resource)


def test_cross_resource_reference_mismatch_is_rejected() -> None:
    """A patient id under a practitioner reference is a type/prefix mismatch."""
    resource = _fresh("encounter")
    participants = resource["participant"]
    assert isinstance(participants, list)
    assert isinstance(participants[0], dict)
    participants[0]["individual"] = {"reference": "Practitioner/SYN-PAT-000000000001"}
    with pytest.raises(InvalidSyntheticReferenceError):
        ADAPTER.deserialize(resource)


def test_wrong_expected_reference_type_is_rejected() -> None:
    """The direct validator enforces the caller's expected target type."""
    with pytest.raises(InvalidFhirResourceError):
        validate_reference(
            {"reference": "Practitioner/SYN-PRC-000000000001"},
            expected_type="Patient",
            field="subject",
        )


@pytest.mark.parametrize(
    "value",
    ("1234567890123", "ABCDEF123456789", "SYN-PAT-short", 12345),
)
def test_real_or_malformed_identifier_value_is_rejected(value: object) -> None:
    """Identifier values must be opaque SYN- references."""
    resource = _fresh("encounter")
    identifiers = resource["identifier"]
    assert isinstance(identifiers, list)
    assert isinstance(identifiers[0], dict)
    identifiers[0]["value"] = value
    with pytest.raises((InvalidFhirResourceError, InvalidSyntheticReferenceError)):
        ADAPTER.deserialize(resource)


def test_non_synthetic_identifier_system_is_rejected() -> None:
    """An external identifier system cannot masquerade as a synthetic one."""
    resource = _fresh("encounter")
    identifiers = resource["identifier"]
    assert isinstance(identifiers, list)
    assert isinstance(identifiers[0], dict)
    identifiers[0]["system"] = "urn:example:external"
    with pytest.raises(InvalidFhirResourceError):
        ADAPTER.deserialize(resource)


def test_identifier_helper_validates_system_and_prefix() -> None:
    """The shared helper returns the opaque value on the happy path."""
    assert validate_identifier(
        {"system": IDENTIFIER_SYSTEM, "value": PATIENT.ref},
        expected_system=IDENTIFIER_SYSTEM,
        field="identifier",
        expected_prefix="SYN-PAT-",
    ) == PATIENT.ref


@pytest.mark.parametrize(
    "resource_type",
    ("Patient", "MedicationRequest", "Bundle", "Claim", "AuditEvent", "Procedure"),
)
def test_unsupported_resource_is_rejected(resource_type: str) -> None:
    """Unsupported types raise a structured error in both directions."""
    with pytest.raises(UnsupportedFhirResourceError) as raised:
        ADAPTER.deserialize({"resourceType": resource_type, "id": "SYN-X-000001"})
    assert raised.value.code == "UNSUPPORTED_FHIR_RESOURCE"
    assert resource_type in str(raised.value.details)


def test_non_dict_resource_is_rejected() -> None:
    """A malformed resource is not treated as an empty resource."""
    with pytest.raises(InvalidFhirResourceError):
        ADAPTER.deserialize(["Encounter"])  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field",
    ("resourceType", "id", "meta", "identifier", "extension", "active", "qualification"),
)
def test_missing_required_field_is_rejected(field: str) -> None:
    """Removing any required field fails deserialisation."""
    source = "practitioner" if field == "qualification" else "organization"
    resource = _fresh(source)
    del resource[field]
    with pytest.raises((InvalidFhirResourceError, UnsupportedFhirResourceError)):
        ADAPTER.deserialize(resource)


def test_wrong_synthetic_profile_is_rejected() -> None:
    """A foreign profile cannot be relabelled as a synthetic resource."""
    resource = _fresh("encounter")
    meta = resource["meta"]
    assert isinstance(meta, dict)
    meta["profile"] = ["http://example.org/StructureDefinition/FakeEncounter"]
    with pytest.raises(InvalidFhirResourceError):
        ADAPTER.deserialize(resource)


def test_invalid_version_is_rejected() -> None:
    """meta.versionId must be a positive integer string."""
    resource = _fresh("encounter")
    meta = resource["meta"]
    assert isinstance(meta, dict)
    meta["versionId"] = "not-a-version"
    with pytest.raises(InvalidFhirResourceError):
        ADAPTER.deserialize(resource)


def test_lifecycle_state_and_fhir_status_must_agree() -> None:
    """The exact synthetic state extension is authoritative, not the FHIR code."""
    resource = _fresh("encounter")
    _set_extension(resource, EXT_ENCOUNTER_STATUS, "valueCode", "admitted")
    resource["status"] = "planned"
    with pytest.raises(InvalidFhirResourceError):
        ADAPTER.deserialize(resource)


def test_unknown_lifecycle_state_is_rejected() -> None:
    """An invented state cannot be smuggled through a local extension."""
    resource = _fresh("order")
    _set_extension(resource, EXT_ORDER_STATUS, "valueCode", "not-a-state")
    with pytest.raises(InvalidFhirResourceError):
        ADAPTER.deserialize(resource)


def test_tenant_extension_is_required_and_synthetic() -> None:
    """A resource without a synthetic tenant is not a Health Core resource."""
    resource = _fresh("encounter")
    extensions = resource["extension"]
    assert isinstance(extensions, list)
    resource["extension"] = [item for item in extensions if item.get("url") != EXT_TENANT]
    with pytest.raises(InvalidFhirResourceError):
        ADAPTER.deserialize(resource)


def test_forged_patient_label_is_rejected() -> None:
    """A real-looking patient label cannot enter through an extension."""
    resource = _fresh("order")
    _set_extension(resource, "urn:gula:synthetic:fhir:R4:extension/patient-label", "valueString", "1234567890")
    with pytest.raises((InvalidFhirResourceError, InvalidSyntheticReferenceError)):
        ADAPTER.deserialize(resource)


def test_missing_specimen_barcode_is_rejected() -> None:
    """A specimen must carry both its id and its synthetic barcode."""
    resource = _fresh("specimen")
    identifiers = resource["identifier"]
    assert isinstance(identifiers, list)
    resource["identifier"] = identifiers[:1]
    with pytest.raises(InvalidFhirResourceError):
        ADAPTER.deserialize(resource)


def test_deep_copy_of_valid_resource_still_round_trips() -> None:
    """Validation is structural, not object-identity dependent."""
    original = ADAPTER.serialize(order())
    clone = copy.deepcopy(original)
    assert ADAPTER.deserialize(clone) == order()


def test_synthetic_reference_helper_is_strict() -> None:
    """The read-only shared id helpers remain the single acceptance boundary."""
    assert is_synthetic_id(PATIENT.ref) is True
    assert is_synthetic_id("1234567890") is False


def test_every_reference_prefix_is_synthetic() -> None:
    """The reference-type table contains only SYN- prefixed kinds."""
    for target_type, prefix in REFERENCE_TARGET_PREFIXES.items():
        assert target_type
        assert prefix.startswith("SYN-")
        assert FhirR4Adapter is not None
