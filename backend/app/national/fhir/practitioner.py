from __future__ import annotations

from typing import Any

from app.national.domain.practitioner import Practitioner


class FHIRPractitionerMapper:
    RESOURCE_TYPE = "Practitioner"

    @classmethod
    def from_model(cls, practitioner: Practitioner) -> dict[str, Any]:
        resource = {
            "resourceType": cls.RESOURCE_TYPE,
            "id": practitioner.fhir_id or practitioner.id,
            "identifier": cls._build_identifiers(practitioner),
            "name": [
                {
                    "use": "official",
                    "text": practitioner.full_name,
                    "family": practitioner.full_name or "",
                },
            ],
            "telecom": cls._build_telecom(practitioner),
            "address": [{"text": practitioner.facility_id or ""}],
            "gender": practitioner.gender.value if practitioner.gender else None,
            "birthDate": practitioner.date_of_birth.isoformat()
            if practitioner.date_of_birth
            else None,
            "active": practitioner.is_active,
        }
        if practitioner.specialty:
            resource["specialty"] = [{"text": practitioner.specialty}]
        if practitioner.qualification:
            resource["qualification"] = [{"code": {"text": practitioner.qualification}}]
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def _build_identifiers(cls, practitioner: Practitioner) -> list[dict]:
        identifiers = []
        if practitioner.license_number:
            identifiers.append(
                {
                    "use": "official",
                    "system": "https://gula.health/identifier/license",
                    "value": practitioner.license_number,
                },
            )
        return identifiers

    @classmethod
    def _build_telecom(cls, practitioner: Practitioner) -> list[dict]:
        telecom = []
        if practitioner.phone:
            telecom.append({"system": "phone", "value": practitioner.phone})
        if practitioner.email:
            telecom.append({"system": "email", "value": practitioner.email})
        return telecom
