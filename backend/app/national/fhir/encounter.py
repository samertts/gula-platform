from __future__ import annotations

from typing import Any

from app.national.domain.encounter import Encounter


class FHIREncounterMapper:
    RESOURCE_TYPE = "Encounter"

    @classmethod
    def from_model(cls, encounter: Encounter) -> dict[str, Any]:
        resource = {
            "resourceType": cls.RESOURCE_TYPE,
            "id": encounter.fhir_id or encounter.id,
            "status": encounter.status.value if encounter.status else "unknown",
            "class": cls._build_class(encounter),
            "type": [{"coding": [{"code": encounter.encounter_type.value}]}]
            if encounter.encounter_type
            else [],
            "subject": {"reference": f"Patient/{encounter.patient_id}"},
            "participant": cls._build_participants(encounter),
            "period": cls._build_period(encounter),
            "reasonCode": [{"text": encounter.reason_description}]
            if encounter.reason_description
            else [],
            "diagnosis": cls._build_diagnosis(encounter),
            "serviceProvider": {"reference": f"Organization/{encounter.organization_id}"}
            if encounter.organization_id
            else None,
            "location": [{"location": {"reference": f"Location/{encounter.facility_id}"}}]
            if encounter.facility_id
            else [],
        }
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def _build_class(cls, encounter: Encounter) -> dict:
        class_map = {
            "outpatient": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
            },
            "inpatient": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "IMP",
            },
            "emergency": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "EMER",
            },
            "virtual": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "VR"},
        }
        return class_map.get(
            encounter.encounter_type.value if encounter.encounter_type else "", {"code": "OTH"},
        )

    @classmethod
    def _build_participants(cls, encounter: Encounter) -> list[dict]:
        if encounter.practitioner_id:
            return [{"individual": {"reference": f"Practitioner/{encounter.practitioner_id}"}}]
        return []

    @classmethod
    def _build_period(cls, encounter: Encounter) -> dict:
        period = {}
        if encounter.period_start:
            period["start"] = encounter.period_start.isoformat()
        if encounter.period_end:
            period["end"] = encounter.period_end.isoformat()
        return period

    @classmethod
    def _build_diagnosis(cls, encounter: Encounter) -> list[dict]:
        if encounter.diagnosis_code:
            return [
                {
                    "condition": {"coding": [{"code": encounter.diagnosis_code}]},
                    "use": {"coding": [{"code": "DD"}]},
                },
            ]
        return []
