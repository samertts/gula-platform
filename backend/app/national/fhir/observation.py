from __future__ import annotations

from typing import Any


class FHIRObservationMapper:
    RESOURCE_TYPE = "Observation"

    @classmethod
    def from_lab_result(cls, result: dict, patient_id: str, encounter_id: str | None = None) -> dict[str, Any]:
        resource = {
            "resourceType": cls.RESOURCE_TYPE,
            "id": str(result.get("id", "")),
            "status": "final",
            "subject": {"reference": f"Patient/{patient_id}"},
            "code": {
                "coding": [{"system": "http://loinc.org", "code": result.get("test_code", ""), "display": result.get("test_name", "")}],
                "text": result.get("test_name", ""),
            },
            "valueQuantity": cls._build_quantity(result),
            "interpretation": cls._build_interpretation(result),
            "referenceRange": cls._build_reference_range(result),
            "issued": str(result.get("created_at", "")),
        }
        if encounter_id:
            resource["encounter"] = {"reference": f"Encounter/{encounter_id}"}
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def _build_quantity(cls, result: dict) -> dict | None:
        value = result.get("value")
        if value is None:
            return None
        return {
            "value": float(value) if value else 0,
            "unit": result.get("unit", ""),
            "system": "http://unitsofmeasure.org",
            "code": result.get("unit", ""),
        }

    @classmethod
    def _build_interpretation(cls, result: dict) -> list[dict] | None:
        flag = result.get("flag", "")
        if not flag:
            return None
        mapping = {"high": "H", "low": "L", "critical_high": "HH", "critical_low": "LL", "normal": "N"}
        return [{"coding": [{"code": mapping.get(flag, "N"), "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"}]}]

    @classmethod
    def _build_reference_range(cls, result: dict) -> list[dict] | None:
        low = result.get("normal_range_low")
        high = result.get("normal_range_high")
        if low is None and high is None:
            return None
        return [{"low": {"value": float(low)} if low is not None else None, "high": {"value": float(high)} if high is not None else None}]
