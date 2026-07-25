from __future__ import annotations

from typing import Any

from app.national.domain.citizen import Citizen
from app.national.domain.patient import Patient


class FHIRPatientMapper:
    RESOURCE_TYPE = "Patient"

    @classmethod
    def from_citizen(cls, citizen: Citizen) -> dict[str, Any]:
        resource = {
            "resourceType": cls.RESOURCE_TYPE,
            "id": citizen.fhir_id or citizen.id,
            "identifier": cls._build_identifiers(citizen),
            "name": cls._build_names(citizen),
            "gender": citizen.gender.value if citizen.gender else "unknown",
            "birthDate": citizen.date_of_birth.isoformat() if citizen.date_of_birth else None,
            "address": cls._build_addresses(citizen),
            "telecom": cls._build_telecom(citizen),
            "maritalStatus": {"text": citizen.marital_status.value}
            if citizen.marital_status
            else None,
            "active": not citizen.is_deleted,
        }
        if citizen.is_deceased:
            resource["deceasedDateTime"] = (
                citizen.deceased_date.isoformat() if citizen.deceased_date else None
            )
            resource["deceasedBoolean"] = True
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def from_patient(cls, patient: Patient, citizen: Citizen | None = None) -> dict[str, Any]:
        resource = cls.from_citizen(citizen) if citizen else {}
        resource.update(
            {
                "id": patient.fhir_id or patient.id,
                "generalPractitioner": [{"reference": f"Practitioner/{patient.created_by}"}]
                if patient.created_by
                else [],
                "managingOrganization": [{"reference": f"Organization/{patient.lab_id}"}]
                if patient.lab_id
                else [],
            },
        )
        return resource

    @classmethod
    def _build_identifiers(cls, citizen: Citizen) -> list[dict]:
        identifiers = []
        if citizen.health_number:
            identifiers.append(
                {
                    "use": "usual",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "MR",
                            },
                        ],
                        "text": "Health Number",
                    },
                    "system": "https://gula.health/identifier/health-number",
                    "value": citizen.health_number,
                },
            )
        if citizen.national_id_hash:
            identifiers.append(
                {
                    "use": "official",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "NI",
                            },
                        ],
                        "text": "National ID",
                    },
                    "system": "https://gula.health/identifier/national-id",
                    "value": f"hash:{citizen.national_id_hash[:16]}...",
                },
            )
        return identifiers

    @classmethod
    def _build_names(cls, citizen: Citizen) -> list[dict]:
        name = {
            "use": "official",
            "family": citizen.last_name or "",
            "given": [citizen.first_name or ""],
        }
        if citizen.father_name:
            name["given"].append(citizen.father_name)
        if citizen.full_name_ar:
            name["text"] = citizen.full_name_ar
        return [name]

    @classmethod
    def _build_addresses(cls, citizen: Citizen) -> list[dict]:
        address = {"use": "home", "city": citizen.governorate or "", "country": "IQ"}
        if citizen.district:
            address["district"] = citizen.district
        if citizen.street:
            address["line"] = [citizen.street]
        return [address]

    @classmethod
    def _build_telecom(cls, citizen: Citizen) -> list[dict]:
        telecom = []
        if citizen.phone:
            telecom.append({"system": "phone", "value": citizen.phone, "use": "mobile"})
        if citizen.email:
            telecom.append({"system": "email", "value": citizen.email, "use": "home"})
        return telecom
