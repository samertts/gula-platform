from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchParameter:
    name: str = ""
    type: str = "string"
    description: str = ""
    resource_types: list[str] = field(default_factory=list)
    path: str = ""


SEARCH_PARAMETERS: dict[str, list[SearchParameter]] = {
    "Patient": [
        SearchParameter(name="identifier", type="token", description="Patient identifier", path="Patient.identifier"),
        SearchParameter(name="name", type="string", description="Patient name", path="Patient.name"),
        SearchParameter(name="birthdate", type="date", description="Patient birth date", path="Patient.birthDate"),
        SearchParameter(name="gender", type="token", description="Patient gender", path="Patient.gender"),
        SearchParameter(name="phone", type="token", description="Patient phone", path="Patient.telecom"),
        SearchParameter(name="address", type="string", description="Patient address", path="Patient.address"),
    ],
    "Practitioner": [
        SearchParameter(name="identifier", type="token", path="Practitioner.identifier"),
        SearchParameter(name="name", type="string", path="Practitioner.name"),
    ],
    "Organization": [
        SearchParameter(name="identifier", type="token", path="Organization.identifier"),
        SearchParameter(name="name", type="string", path="Organization.name"),
        SearchParameter(name="type", type="token", path="Organization.type"),
    ],
    "Encounter": [
        SearchParameter(name="patient", type="reference", path="Encounter.subject"),
        SearchParameter(name="date", type="date", path="Encounter.period"),
        SearchParameter(name="status", type="token", path="Encounter.status"),
    ],
}


class FHIRSearchEngine:
    def get_search_parameters(self, resource_type: str) -> list[SearchParameter]:
        return SEARCH_PARAMETERS.get(resource_type, [])

    def build_search_query(self, resource_type: str, params: dict[str, str]) -> dict[str, Any]:
        query: dict[str, Any] = {"filters": [], "sort": None, "limit": 50, "offset": 0}
        if "_count" in params:
            query["limit"] = min(int(params["_count"]), 100)
        if "_offset" in params:
            query["offset"] = int(params["_offset"])
        for key, value in params.items():
            if key.startswith("_"):
                continue
            query["filters"].append({"field": key, "value": value, "type": "exact"})
        return query
