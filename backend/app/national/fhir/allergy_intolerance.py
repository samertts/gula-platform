from __future__ import annotations

from typing import Any

from app.ehr.models.allergy import AllergyIntolerance


class FHIRAllergyIntoleranceMapper:
    RESOURCE_TYPE = "AllergyIntolerance"

    @classmethod
    def from_model(cls, allergy: AllergyIntolerance) -> dict[str, Any]:
        resource = {
            "resourceType": cls.RESOURCE_TYPE,
            "id": allergy.fhir_id or allergy.id,
            "clinicalStatus": cls._build_clinical_status(allergy.status.value if allergy.status else "active"),
            "verificationStatus": cls._build_verification_status(allergy.status.value if allergy.status else None),
            "type": allergy.allergy_type.upper() if allergy.allergy_type else None,
            "category": [allergy.category] if allergy.category else [],
            "criticality": allergy.criticality.upper() if allergy.criticality else None,
            "code": {
                "coding": cls._build_codings(allergy),
                "text": allergy.code_display_ar or allergy.code_display,
            },
            "patient": {"reference": f"Patient/{allergy.patient_id}"},
            "encounter": {"reference": f"Encounter/{allergy.encounter_id}"} if allergy.encounter_id else None,
            "recorder": {"reference": f"Practitioner/{allergy.practitioner_id}"} if allergy.practitioner_id else None,
            "onsetDateTime": allergy.onset_date.isoformat() if allergy.onset_date else None,
            "recordedDate": allergy.recorded_date.isoformat() if allergy.recorded_date else None,
            "lastOccurrence": allergy.last_occurrence_date.isoformat() if allergy.last_occurrence_date else None,
            "note": [{"text": allergy.notes}] if allergy.notes else [],
            "reaction": cls._build_reactions(allergy),
        }
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def _build_clinical_status(cls, status: str) -> dict:
        mapping = {"active": "active", "resolved": "resolved", "confirmed": "active", "refuted": "inactive", "entered_in_error": "entered-in-error"}
        return {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": mapping.get(status, "active")}]}

    @classmethod
    def _build_verification_status(cls, status: str | None) -> dict | None:
        if not status:
            return None
        mapping = {"active": "confirmed", "resolved": "confirmed", "confirmed": "confirmed", "refuted": "refuted", "entered_in_error": "entered-in-error"}
        return {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification", "code": mapping.get(status, "unconfirmed")}]}

    @classmethod
    def _build_codings(cls, allergy: AllergyIntolerance) -> list[dict]:
        codings = []
        if allergy.code and allergy.code_system:
            system_map = {"snomed": "http://snomed.info/sct", "unii": "http://fdasis.nlm.nih.gov", "rxnorm": "http://www.nlm.nih.gov/research/umls/rxnorm"}
            codings.append({"system": system_map.get(allergy.code_system, "http://gula.health/code"), "code": allergy.code, "display": allergy.code_display})
        return codings

    @classmethod
    def _build_reactions(cls, allergy: AllergyIntolerance) -> list[dict] | None:
        if not allergy.reaction and not allergy.reaction_details:
            return None
        reaction: dict[str, Any] = {}
        if allergy.reaction:
            reaction["manifestation"] = [{"coding": [{"code": allergy.reaction}]}]
        if allergy.reaction_details:
            if isinstance(allergy.reaction_details, dict):
                if "severity" in allergy.reaction_details:
                    reaction["severity"] = allergy.reaction_details["severity"]
                if "exposureRoute" in allergy.reaction_details:
                    reaction["exposureRoute"] = {"coding": [{"code": allergy.reaction_details["exposureRoute"]}]}
        return [reaction] if reaction else None
