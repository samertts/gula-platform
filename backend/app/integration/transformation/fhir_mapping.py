from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from backend.app.national.fhir import (
    FHIRBundle,
    FHIRHumanName,
    FHIRIdentifier,
    FHIRPatientMapper,
)

logger = logging.getLogger("gula.integration.transformation.fhir_mapping")


@dataclass
class MappingRule:
    source_path: str = ""
    target_path: str = ""
    default: Any = None
    required: bool = False


@dataclass
class FHIRProfile:
    name: str = ""
    resource_type: str = ""
    rules: list[MappingRule] = field(default_factory=list)


class FHIRMappingEngine:
    def __init__(self):
        self._profiles: dict[str, FHIRProfile] = {}
        self._patient_mapper = FHIRPatientMapper()

    def register_profile(self, profile: FHIRProfile) -> None:
        self._profiles[profile.name] = profile
        logger.info("FHIR mapping profile registered: %s", profile.name)

    def map_to_patient(self, data: dict[str, Any]) -> dict[str, Any]:
        FHIRHumanName(
            family=data.get("last_name", ""),
            text=data.get("full_name", ""),
        )
        FHIRIdentifier(
            system="urn:oid:1.2.3.4.5.6.7",
            value=data.get("national_id", ""),
        )
        return self._patient_mapper.to_fhir(data)

    def map_from_patient(self, fhir_patient: dict[str, Any]) -> dict[str, Any]:
        return self._patient_mapper.from_fhir(fhir_patient)

    def map(self, data: dict[str, Any], profile_name: str) -> dict[str, Any]:
        profile = self._profiles.get(profile_name)
        if not profile:
            raise ValueError(f"FHIR mapping profile not found: {profile_name}")

        resource: dict[str, Any] = {"resourceType": profile.resource_type}
        for rule in profile.rules:
            value = self._resolve_path(data, rule.source_path)
            if value is None and rule.required:
                logger.warning("Required field missing: %s", rule.source_path)
                continue
            if value is None:
                value = rule.default
            self._set_path(resource, rule.target_path, value)
        return resource

    def _resolve_path(self, data: dict[str, Any], path: str) -> Any:
        parts = path.split(".")
        current: Any = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def _set_path(self, target: dict[str, Any], path: str, value: Any) -> None:
        parts = path.split(".")
        current = target
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                current[part] = value
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]

    def create_bundle(
        self, resources: list[dict[str, Any]], bundle_type: str = "collection"
    ) -> dict[str, Any]:
        return FHIRBundle(
            type=bundle_type,
            entry=[FHIRBundle(resource=r) for r in resources]
            if hasattr(FHIRBundle, "entry")
            else [{"resource": r} for r in resources],
        )
