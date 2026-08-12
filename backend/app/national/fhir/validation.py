from __future__ import annotations

from dataclasses import dataclass, field


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
    "Bundle": ["resourceType", "id", "type"],
}


class FHIRValidationEngine:
    def validate(self, resource: dict) -> FHIRValidationResult:
        result = FHIRValidationResult()
        resource_type = resource.get("resourceType", "")
        required = REQUIRED_FIELDS.get(resource_type, ["resourceType"])
        for req_field in required:
            if req_field not in resource or resource[req_field] is None:
                result.valid = False
                result.errors.append(f"Missing required field: {req_field}")
        if resource_type == "Patient":
            self._validate_patient(resource, result)
        elif resource_type == "Encounter":
            self._validate_encounter(resource, result)
        return result

    def _validate_patient(self, resource: dict, result: FHIRValidationResult) -> None:
        if "identifier" in resource and not isinstance(resource["identifier"], list):
            result.errors.append("Patient.identifier must be a list")

    def _validate_encounter(self, resource: dict, result: FHIRValidationResult) -> None:
        valid_statuses = {"planned", "in-progress", "onleave", "finished", "cancelled", "entered-in-error", "unknown"}
        status = resource.get("status", "")
        if status and status not in valid_statuses:
            result.errors.append(f"Invalid Encounter status: {status}")
