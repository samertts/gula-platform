from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.integration.standards.fhir")

FHIR_VERSION = "R4"


@dataclass
class FHIRResource:
    resource_type: str = ""
    id: str = ""
    data: dict[str, Any] = field(default_factory=dict)


class FHIRService:
    def __init__(self):
        self._version = FHIR_VERSION
        self._parsers: dict[str, Any] = {}

    def parse_resource(self, resource_type: str, data: dict[str, Any]) -> FHIRResource:
        return FHIRResource(resource_type=resource_type, id=data.get("id", ""), data=data)

    def serialize(self, resource: FHIRResource) -> dict[str, Any]:
        result = {"resourceType": resource.resource_type, "id": resource.id}
        result.update(resource.data)
        return result

    def validate(self, resource: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if "resourceType" not in resource:
            errors.append("Missing resourceType")
        return errors

    def create_bundle(
        self, resources: list[FHIRResource], bundle_type: str = "collection"
    ) -> dict[str, Any]:
        return {
            "resourceType": "Bundle",
            "type": bundle_type,
            "entry": [{"resource": self.serialize(r)} for r in resources],
        }

    def supports_interaction(self, interaction: str) -> bool:
        return interaction in {"read", "search", "create", "update", "delete", "history"}

    def version(self) -> str:
        return self._version
