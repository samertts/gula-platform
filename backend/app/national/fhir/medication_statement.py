from __future__ import annotations

from typing import Any

from app.ehr.models.medication import MedicationStatement


class FHIRMedicationStatementMapper:
    RESOURCE_TYPE = "MedicationStatement"

    @classmethod
    def from_model(cls, statement: MedicationStatement) -> dict[str, Any]:
        resource = {
            "resourceType": cls.RESOURCE_TYPE,
            "id": statement.fhir_id or statement.id,
            "status": statement.status or "active",
            "category": {"coding": [{"code": statement.category}]} if statement.category else None,
            "medicationCodeableConcept": {
                "coding": cls._build_codings(statement),
                "text": statement.medication_name_ar or statement.medication_name,
            },
            "subject": {"reference": f"Patient/{statement.patient_id}"},
            "encounter": {"reference": f"Encounter/{statement.encounter_id}"}
            if statement.encounter_id
            else None,
            "informationSource": {"reference": f"Practitioner/{statement.practitioner_id}"}
            if statement.practitioner_id
            else None,
            "reasonCode": [
                {
                    "coding": [{"code": statement.reason_code}],
                    "text": statement.reason_description or "",
                },
            ]
            if statement.reason_code
            else [],
            "note": [{"text": statement.note}] if statement.note else [],
            "dosage": cls._build_dosage(statement),
            "effectivePeriod": cls._build_period(statement),
            "dateAsserted": statement.date_recorded.isoformat()
            if statement.date_recorded
            else None,
        }
        if statement.medication_brand:
            resource["medicationCodeableConcept"]["coding"].append(
                {"code": statement.medication_brand},
            )
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def _build_codings(cls, statement: MedicationStatement) -> list[dict]:
        codings = []
        if statement.medication_code and statement.medication_code_system:
            system_map = {
                "snomed": "http://snomed.info/sct",
                "rxnorm": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "atc": "http://www.whocc.no/atc",
            }
            codings.append(
                {
                    "system": system_map.get(
                        statement.medication_code_system, "http://gula.health/code",
                    ),
                    "code": statement.medication_code,
                    "display": statement.medication_name,
                },
            )
        return codings

    @classmethod
    def _build_dosage(cls, statement: MedicationStatement) -> list[dict]:
        dosage = []
        entry = {}
        if statement.dosage_text:
            entry["text"] = statement.dosage_text
        if statement.route:
            entry["route"] = {"coding": [{"code": statement.route}]}
        if statement.frequency:
            entry["timing"] = {"code": {"coding": [{"code": statement.frequency}]}}
        if statement.strength_value:
            entry["doseAndRate"] = [
                {
                    "doseQuantity": {
                        "value": float(statement.strength_value) if statement.strength_value else 0,
                        "unit": statement.strength_unit or "",
                    },
                },
            ]
        if statement.timing:
            entry["timing"] = {"code": {"coding": [{"code": str(statement.timing)}]}}
        if entry:
            dosage.append(entry)
        return dosage

    @classmethod
    def _build_period(cls, statement: MedicationStatement) -> dict | None:
        if not statement.date_started and not statement.date_ended:
            return None
        period = {}
        if statement.date_started:
            period["start"] = statement.date_started.isoformat()
        if statement.date_ended:
            period["end"] = statement.date_ended.isoformat()
        return period
