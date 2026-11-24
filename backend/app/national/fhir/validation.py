from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FHIRValidationResult:
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


REQUIRED_FIELDS: dict[str, list[str]] = {
    "Patient": ["resourceType", "id"],
    "Practitioner": ["resourceType", "id"],
    "Organization": ["resourceType", "id", "name"],
    "Encounter": ["resourceType", "id", "status", "class"],
    "Observation": ["resourceType", "id", "status", "code", "subject"],
    "Condition": ["resourceType", "id", "subject"],
    "AllergyIntolerance": ["resourceType", "id", "patient"],
    "Procedure": ["resourceType", "id", "status", "subject"],
    "DiagnosticReport": ["resourceType", "id", "status", "code", "subject"],
    "ServiceRequest": ["resourceType", "id", "status", "intent", "subject"],
    "Provenance": ["resourceType", "id", "target"],
    "AuditEvent": ["resourceType", "id", "type", "action", "recorded"],
    "Bundle": ["resourceType", "id", "type"],
}

_REFERENCE_FIELDS: dict[str, tuple[str, ...]] = {
    "Encounter": ("subject",),
    "Observation": ("subject",),
    "Condition": ("subject",),
    "AllergyIntolerance": ("patient",),
    "Procedure": ("subject",),
    "DiagnosticReport": ("subject",),
    "ServiceRequest": ("subject",),
    "Provenance": ("target",),
    "AuditEvent": ("agent",),
}

_CODEABLE_FIELDS: dict[str, tuple[str, ...]] = {
    "Observation": ("code",),
    "Condition": ("code",),
    "Procedure": ("code",),
    "DiagnosticReport": ("code",),
    "ServiceRequest": ("code",),
    "AuditEvent": ("type",),
}

_LOCAL_REFERENCE = re.compile(r"^#[A-Za-z0-9\-]+$")
_RELATIVE_REFERENCE = re.compile(r"^[A-Za-z][A-Za-z0-9]*/[A-Za-z0-9.\-]+$")
_ABSOLUTE_REFERENCE = re.compile(r"^https?://[^\s]+/[A-Za-z][A-Za-z0-9]*/[A-Za-z0-9.\-]+$")
_URN_REFERENCE = re.compile(r"^urn:uuid:[A-Za-z0-9\-]+$")


class FHIRValidationEngine:
    """Conservative structural pre-check over FHIR R4-shaped dictionaries.

    This is intentionally not a full FHIR conformance validator. It detects
    malformed identifiers, broken reference shapes, missing structural
    elements and inconsistent Bundle entries without inventing terminology or
    changing authorization policy.
    """

    def validate(self, resource: dict) -> FHIRValidationResult:
        result = FHIRValidationResult()
        resource_type = resource.get("resourceType", "")
        required = REQUIRED_FIELDS.get(resource_type, ["resourceType"])
        for req_field in required:
            if req_field not in resource or resource[req_field] is None:
                result.valid = False
                result.errors.append(f"Missing required field: {req_field}")

        if resource_type not in REQUIRED_FIELDS:
            return result

        self._validate_identifiers(resource, result)
        for field_name in _REFERENCE_FIELDS.get(resource_type, ()):
            self._validate_reference_field(resource.get(field_name), field_name, result)
        for field_name in _CODEABLE_FIELDS.get(resource_type, ()):
            self._validate_codeable_concept(resource.get(field_name), field_name, result)
        self._validate_provenance(resource, result)

        if resource_type == "Patient":
            self._validate_patient(resource, result)
        elif resource_type == "Encounter":
            self._validate_encounter(resource, result)
        elif resource_type == "Bundle":
            self._validate_bundle(resource, result)

        return result

    def _validate_identifiers(self, resource: dict, result: FHIRValidationResult) -> None:
        if "identifier" not in resource:
            return
        identifiers = resource["identifier"]
        if not isinstance(identifiers, list):
            result.valid = False
            result.errors.append(f"{resource.get('resourceType')}.identifier must be a list")
            return
        for index, identifier in enumerate(identifiers):
            if not isinstance(identifier, dict):
                result.valid = False
                result.errors.append(f"identifier[{index}] must be an object")
                continue
            value = identifier.get("value")
            if not isinstance(value, str) or not value.strip():
                result.valid = False
                result.errors.append(f"identifier[{index}].value is required")
            system = identifier.get("system")
            if system is not None and (not isinstance(system, str) or not system.strip()):
                result.valid = False
                result.errors.append(f"identifier[{index}].system must be a non-empty string")

    def _validate_reference_field(
        self, value: Any, field_name: str, result: FHIRValidationResult,
    ) -> None:
        if value is None:
            return
        values = value if isinstance(value, list) else [value]
        for index, item in enumerate(values):
            label = field_name if not isinstance(value, list) else f"{field_name}[{index}]"
            if isinstance(item, dict):
                if "reference" not in item:
                    # FHIR permits identifier-only references; there is no
                    # literal reference to validate in that case.
                    if isinstance(item.get("identifier"), dict):
                        continue
                    result.valid = False
                    result.errors.append(f"{label}.reference is required")
                    continue
                reference = item["reference"]
            else:
                reference = item
            if not isinstance(reference, str) or not reference.strip():
                result.valid = False
                result.errors.append(f"{label}.reference must be a non-empty string")
                continue
            if not (
                _LOCAL_REFERENCE.match(reference)
                or _RELATIVE_REFERENCE.match(reference)
                or _ABSOLUTE_REFERENCE.match(reference)
                or _URN_REFERENCE.match(reference)
            ):
                result.valid = False
                result.errors.append(f"Broken reference in {label}: {reference}")

    def _validate_codeable_concept(
        self, value: Any, field_name: str, result: FHIRValidationResult,
    ) -> None:
        if value is None:
            return
        if not isinstance(value, dict):
            result.valid = False
            result.errors.append(f"{field_name} must be a CodeableConcept object")
            return
        coding = value.get("coding")
        if coding is not None and not isinstance(coding, list):
            result.valid = False
            result.errors.append(f"{field_name}.coding must be a list")

    def _validate_provenance(self, resource: dict, result: FHIRValidationResult) -> None:
        meta = resource.get("meta")
        if meta is None:
            result.warnings.append("FHIR meta.source absent; provenance not retained in resource")
            return
        if not isinstance(meta, dict):
            result.valid = False
            result.errors.append("meta must be an object")
            return
        source = meta.get("source")
        if source is not None and not isinstance(source, str):
            result.valid = False
            result.errors.append("meta.source must be a string")

    def _validate_patient(self, resource: dict, result: FHIRValidationResult) -> None:
        active = resource.get("active")
        if active is not None and not isinstance(active, bool):
            result.valid = False
            result.errors.append("Patient.active must be a boolean")

    def _validate_encounter(self, resource: dict, result: FHIRValidationResult) -> None:
        valid_statuses = {"planned", "in-progress", "onleave", "finished", "cancelled", "entered-in-error", "unknown"}
        status = resource.get("status", "")
        if status and status not in valid_statuses:
            result.valid = False
            result.errors.append(f"Invalid Encounter status: {status}")
        encounter_class = resource.get("class")
        if encounter_class is not None and not isinstance(encounter_class, dict):
            result.valid = False
            result.errors.append("Encounter.class must be a Coding object")

    def _validate_bundle(self, resource: dict, result: FHIRValidationResult) -> None:
        entries = resource.get("entry")
        if entries is None:
            return
        if not isinstance(entries, list):
            result.valid = False
            result.errors.append("Bundle.entry must be a list")
            return

        seen_full_urls: set[str] = set()
        contained_ids: set[str] = set()
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                result.valid = False
                result.errors.append(f"Bundle.entry[{index}] must be an object")
                continue
            nested = entry.get("resource")
            if nested is not None:
                if not isinstance(nested, dict) or not nested.get("resourceType"):
                    result.valid = False
                    result.errors.append(f"Bundle.entry[{index}].resource must have resourceType")
                else:
                    nested_id = nested.get("id")
                    if isinstance(nested_id, str) and nested_id:
                        contained_ids.add(nested_id)
            full_url = entry.get("fullUrl")
            if full_url is not None:
                if not isinstance(full_url, str) or not full_url.strip():
                    result.valid = False
                    result.errors.append(f"Bundle.entry[{index}].fullUrl must be a non-empty string")
                elif full_url in seen_full_urls:
                    result.valid = False
                    result.errors.append(f"Duplicate Bundle.entry.fullUrl: {full_url}")
                else:
                    seen_full_urls.add(full_url)

        for reference in self._local_references(resource):
            if reference[1:] not in contained_ids:
                result.valid = False
                result.errors.append(f"Unresolved local Bundle reference: {reference}")

    def _local_references(self, value: Any) -> list[str]:
        found: list[str] = []
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "reference" and isinstance(item, str) and _LOCAL_REFERENCE.match(item):
                    found.append(item)
                else:
                    found.extend(self._local_references(item))
        elif isinstance(value, list):
            for item in value:
                found.extend(self._local_references(item))
        return found
