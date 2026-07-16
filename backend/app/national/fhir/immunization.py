from __future__ import annotations

from typing import Any

from app.ehr.models.immunization import ImmunizationRecord


class FHIRImmunizationMapper:
    RESOURCE_TYPE = "Immunization"

    @classmethod
    def from_model(cls, record: ImmunizationRecord) -> dict[str, Any]:
        resource = {
            "resourceType": cls.RESOURCE_TYPE,
            "id": record.fhir_id or record.id,
            "status": cls._map_status(record.status),
            "statusReason": {"coding": [{"code": record.reason_not_given}]} if record.reason_not_given else None,
            "vaccineCode": {
                "coding": cls._build_codings(record),
                "text": record.vaccine_name_ar or record.vaccine_name,
            },
            "patient": {"reference": f"Patient/{record.patient_id}"},
            "encounter": {"reference": f"Encounter/{record.encounter_id}"} if record.encounter_id else None,
            "occurrenceDateTime": record.administration_date.isoformat() if record.administration_date else None,
            "recorded": record.recorded_date.isoformat() if record.recorded_date else None,
            "primarySource": True,
            "manufacturer": {"display": record.manufacturer} if record.manufacturer else None,
            "lotNumber": record.lot_number,
            "expirationDate": record.expiry_date.isoformat() if record.expiry_date else None,
            "site": {"coding": [{"code": record.site}]} if record.site else None,
            "route": {"coding": [{"code": record.route}]} if record.route else None,
            "doseQuantity": {"value": float(record.dose_quantity), "unit": record.dose_unit} if record.dose_quantity else None,
            "performer": cls._build_performers(record),
            "location": {"reference": f"Location/{record.facility_id}"} if record.facility_id else None,
            "note": [{"text": record.notes}] if record.notes else [],
            "protocolApplied": cls._build_protocol(record),
        }
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def _map_status(cls, status: str) -> str:
        mapping = {"completed": "completed", "not_done": "not-done", "entered_in_error": "entered-in-error"}
        return mapping.get(status, "completed")

    @classmethod
    def _build_codings(cls, record: ImmunizationRecord) -> list[dict]:
        codings = []
        if record.vaccine_code and record.vaccine_code_system:
            system_map = {"cvx": "http://hl7.org/fhir/sid/cvx", "snomed": "http://snomed.info/sct", "atc": "http://www.whocc.no/atc"}
            codings.append({"system": system_map.get(record.vaccine_code_system, "http://gula.health/code"), "code": record.vaccine_code, "display": record.vaccine_name})
        return codings

    @classmethod
    def _build_performers(cls, record: ImmunizationRecord) -> list[dict]:
        performers = []
        if record.administrator_id:
            performers.append({"actor": {"reference": f"Practitioner/{record.administrator_id}"}, "function": {"coding": [{"code": "AP"}]}})
        return performers

    @classmethod
    def _build_protocol(cls, record: ImmunizationRecord) -> list[dict] | None:
        if not record.dose_number and not record.dose_series and not record.total_doses:
            return None
        protocol: dict[str, Any] = {}
        if record.dose_number is not None:
            protocol["doseNumberPositiveInt"] = record.dose_number
        if record.total_doses is not None:
            protocol["seriesDosesPositiveInt"] = record.total_doses
        if record.dose_series:
            protocol["series"] = record.dose_series
        return [protocol]
