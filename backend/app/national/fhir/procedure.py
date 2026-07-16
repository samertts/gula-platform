from __future__ import annotations

from typing import Any


class FHIRProcedureMapper:
    RESOURCE_TYPE = "Procedure"

    @classmethod
    def from_dict(cls, data: dict, patient_id: str, encounter_id: str | None = None) -> dict[str, Any]:
        resource = {
            "resourceType": cls.RESOURCE_TYPE,
            "id": str(data.get("id", "")),
            "status": cls._map_status(data.get("status", "completed")),
            "category": {"coding": [{"code": data.get("category", "")}]} if data.get("category") else None,
            "code": {
                "coding": [{"system": data.get("code_system", "http://snomed.info/sct"), "code": data.get("code", ""), "display": data.get("display", "")}],
                "text": data.get("display_ar", data.get("display", "")),
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "encounter": {"reference": f"Encounter/{encounter_id}"} if encounter_id else None,
            "performer": cls._build_performers(data),
            "location": {"reference": f"Location/{data.get('location_id')}"} if data.get("location_id") else None,
            "reasonCode": [{"coding": [{"code": data.get("reason_code", "")}], "text": data.get("reason_description", "")}] if data.get("reason_code") else [],
            "bodySite": [{"coding": [{"code": data.get("body_site", "")}]}] if data.get("body_site") else [],
            "outcome": data.get("outcome", ""),
            "report": [{"reference": data.get("report_reference", "")}] if data.get("report_reference") else [],
            "usedReference": [{"reference": ref} for ref in (data.get("used_references") or [])],
            "note": [{"text": data.get("notes", "")}] if data.get("notes") else [],
            "performedPeriod": cls._build_performed_period(data),
        }
        if data.get("performed_date"):
            resource["performedDateTime"] = data["performed_date"]
        if data.get("focal_device") or data.get("used_device"):
            resource["usedReference"] = resource.get("usedReference", [])
            if data.get("focal_device"):
                resource["usedReference"].append({"reference": f"Device/{data['focal_device']}"})
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def from_surgical(cls, data: dict, patient_id: str, encounter_id: str | None = None) -> dict[str, Any]:
        resource = cls.from_dict(data, patient_id, encounter_id)
        resource["category"] = {"coding": [{"system": "http://snomed.info/sct", "code": "387713003", "display": "Surgical procedure"}]}
        if data.get("surgeon_id"):
            resource.setdefault("performer", []).append({
                "actor": {"reference": f"Practitioner/{data['surgeon_id']}"},
                "function": {"coding": [{"code": "primary_surgeon"}]},
            })
        if data.get("anesthesia"):
            resource["followUp"] = [{"text": data["anesthesia"]}]
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def _map_status(cls, status: str) -> str:
        mapping = {"preparation": "preparation", "in_progress": "in-progress", "on_hold": "on-hold", "completed": "completed", "discontinued": "discontinued", "entered_in_error": "entered-in-error", "unknown": "unknown"}
        return mapping.get(status, "completed")

    @classmethod
    def _build_performers(cls, data: dict) -> list[dict]:
        performers = []
        practitioner_id = data.get("practitioner_id") or data.get("performer_id")
        if practitioner_id:
            performers.append({"actor": {"reference": f"Practitioner/{practitioner_id}"}, "function": {"coding": [{"code": data.get("performer_function", "prf")}]}})
        return performers

    @classmethod
    def _build_performed_period(cls, data: dict) -> dict | None:
        start = data.get("performed_start")
        end = data.get("performed_end")
        if not start and not end:
            return None
        period = {}
        if start:
            period["start"] = start
        if end:
            period["end"] = end
        return period
