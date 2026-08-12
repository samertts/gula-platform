from __future__ import annotations

from typing import Any

from app.national.domain.organization import Organization


class FHIROrganizationMapper:
    RESOURCE_TYPE = "Organization"

    @classmethod
    def from_model(cls, org: Organization) -> dict[str, Any]:
        resource = {
            "resourceType": cls.RESOURCE_TYPE,
            "id": org.fhir_id or org.id,
            "identifier": [{"system": "https://gula.health/identifier/org", "value": org.id}],
            "name": org.name,
            "telecom": cls._build_telecom(org),
            "address": [{
                "line": [org.address_line] if org.address_line else [],
                "city": org.city or "",
                "state": org.governorate or "",
                "country": org.country or "IQ",
            }],
            "active": org.is_active,
        }
        if org.org_type:
            resource["type"] = [{"coding": [{"code": org.org_type.value}]}]
        if org.parent_organization_id:
            resource["partOf"] = {"reference": f"Organization/{org.parent_organization_id}"}
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def _build_telecom(cls, org: Organization) -> list[dict]:
        telecom = []
        if org.phone:
            telecom.append({"system": "phone", "value": org.phone})
        if org.email:
            telecom.append({"system": "email", "value": org.email})
        return telecom
