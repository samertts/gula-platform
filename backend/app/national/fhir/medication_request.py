from __future__ import annotations

from typing import Any

from app.ehr.models.medication import MedicationRequest


class FHIRMedicationRequestMapper:
    RESOURCE_TYPE = "MedicationRequest"

    @classmethod
    def from_model(cls, request: MedicationRequest) -> dict[str, Any]:
        resource = {
            "resourceType": cls.RESOURCE_TYPE,
            "id": request.fhir_id or request.id,
            "status": cls._map_status(request.status.value if request.status else "draft"),
            "intent": request.intent or "order",
            "priority": request.priority or "routine",
            "category": [{"coding": [{"code": request.category}]}] if request.category else [],
            "medicationCodeableConcept": {
                "coding": cls._build_codings(request),
                "text": request.medication_name_ar or request.medication_name,
            },
            "subject": {"reference": f"Patient/{request.patient_id}"},
            "encounter": {"reference": f"Encounter/{request.encounter_id}"} if request.encounter_id else None,
            "requester": {"reference": f"Practitioner/{request.prescriber_id}"} if request.prescriber_id else None,
            "reasonCode": [{"coding": [{"code": request.reason_code}], "text": request.reason_description or ""}] if request.reason_code else [],
            "note": [{"text": request.note}] if request.note else [],
            "dosageInstruction": cls._build_dosage(request),
            "dispenseRequest": cls._build_dispense_request(request),
            "substitution": {"allowedBoolean": request.substitution_allowed} if request.substitution_allowed is not None else None,
            "authoredOn": request.authored_on.isoformat() if request.authored_on else None,
        }
        if request.medication_brand:
            resource["medicationCodeableConcept"]["coding"].append({"code": request.medication_brand})
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def _map_status(cls, status: str) -> str:
        mapping = {
            "draft": "draft",
            "active": "active",
            "completed": "completed",
            "discontinued": "stopped",
            "cancelled": "cancelled",
            "entered_in_error": "entered-in-error",
        }
        return mapping.get(status, "unknown")

    @classmethod
    def _build_codings(cls, request: MedicationRequest) -> list[dict]:
        codings = []
        if request.medication_code and request.medication_code_system:
            system_map = {"snomed": "http://snomed.info/sct", "rxnorm": "http://www.nlm.nih.gov/research/umls/rxnorm", "atc": "http://www.whocc.no/atc"}
            codings.append({"system": system_map.get(request.medication_code_system, "http://gula.health/code"), "code": request.medication_code, "display": request.medication_name})
        return codings

    @classmethod
    def _build_dosage(cls, request: MedicationRequest) -> list[dict]:
        dosage = []
        entry = {}
        if request.dosage_instruction:
            entry["text"] = request.dosage_instruction
        if request.route:
            entry["route"] = {"coding": [{"code": request.route}]}
        if request.dosage_instructions:
            entry["additionalInstruction"] = [{"text": str(d)} for d in (request.dosage_instructions if isinstance(request.dosage_instructions, list) else [])]
        if entry:
            dosage.append(entry)
        return dosage

    @classmethod
    def _build_dispense_request(cls, request: MedicationRequest) -> dict | None:
        dispense = {}
        if request.quantity is not None:
            dispense["quantity"] = {"value": request.quantity, "unit": request.quantity_unit or ""}
        if request.valid_from or request.valid_to:
            period = {}
            if request.valid_from:
                period["start"] = request.valid_from.isoformat()
            if request.valid_to:
                period["end"] = request.valid_to.isoformat()
            dispense["validityPeriod"] = period
        if request.refills is not None:
            dispense["numberOfRepeatsAllowed"] = request.refills
        if request.dispense_interval_days:
            dispense["dispenseInterval"] = {"value": request.dispense_interval_days, "unit": "d", "system": "http://unitsofmeasure.org", "code": "d"}
        return {k: v for k, v in dispense.items() if v is not None} or None
