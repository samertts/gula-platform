from __future__ import annotations

from typing import Any

_STATUS_MAP = {
    "DRAFT": "preliminary",
    "TECHNICALLY_VALIDATED": "preliminary",
    "CLINICALLY_VALIDATED": "final",
    "RELEASED": "final",
    "CORRECTED": "amended",
    "AMENDED": "preliminary",
}


def result_to_fhir_observation(result, *, include_patient_reference: bool = False) -> dict[str, Any]:
    """Map a canonical result to a pure FHIR R4-shaped projection.

    This function is intentionally side-effect free. It does not publish, fetch,
    or persist FHIR resources and omits patient references from share-safe
    projections unless the caller has already made that policy decision.
    """

    value: dict[str, Any] | None
    if result.value_numeric is not None:
        value = {"valueQuantity": {"value": float(result.value_numeric)}}
        if result.unit:
            value["valueQuantity"]["unit"] = result.unit
    elif result.value_text:
        value = {"valueString": result.value_text}
    else:
        value = None

    observation: dict[str, Any] = {
        "resourceType": "Observation",
        "id": result.result_id,
        "identifier": [{"system": "urn:gula:lab-result", "value": result.result_id}],
        "status": _STATUS_MAP.get(result.status, "unknown"),
        "code": {"coding": [{"system": "urn:gula:lab-test", "code": result.test_code, "display": result.test_name}]},
        "meta": {"versionId": str(result.version), "tag": [{"system": "urn:gula:provenance", "code": result.provenance_type}]},
        "extension": [
            {"url": "urn:gula:abnormal-flag", "valueCode": result.abnormal_flag},
            {"url": "urn:gula:source-message", "valueString": result.source_message_id},
        ],
    }
    if value:
        observation.update(value)
    if include_patient_reference:
        observation["subject"] = {"reference": f"Patient/{result.patient_person_id}"}
    if result.released_at:
        observation["effectiveDateTime"] = result.released_at.isoformat()
    return observation
