from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app._compat import UTC

logger = logging.getLogger("gula.knowledge_graph.fhir_catalog")

_FHIR_VERSIONS = {
    "R4": {
        "version": "4.0.1",
        "url": "http://hl7.org/fhir/R4",
    },
    "R5": {
        "version": "5.0.0",
        "url": "http://hl7.org/fhir/R5",
    },
}

_REQUIRED_FHIR_ELEMENTS = {
    "Patient": ["identifier", "name", "gender", "birthDate"],
    "Observation": ["status", "code", "subject", "issued"],
    "ServiceRequest": ["status", "intent", "code", "subject"],
    "Specimen": ["status", "type", "subject"],
    "Organization": ["name"],
    "Practitioner": ["name"],
    "Encounter": ["status", "class", "subject"],
    "Condition": ["subject", "code", "clinicalStatus"],
    "MedicationRequest": ["status", "intent", "medication", "subject"],
    "AllergyIntolerance": ["patient", "code"],
    "CarePlan": ["status", "intent", "subject"],
    "Device": ["type", "patient"],
    "Location": ["name", "type"],
    "Immunization": ["status", "vaccineCode", "patient", "occurrenceDateTime"],
    "ClinicalNote": ["status", "author", "subject"],
    "Bundle": ["type", "entry"],
    "DocumentReference": ["status", "type", "content", "subject"],
}


@dataclass
class FHIRSearchParam:
    name: str
    type: str
    description: str = ""
    target: list[str] | None = None


@dataclass
class FHIROperation:
    name: str
    description: str = ""
    http_method: str = "GET"
    path: str = ""


@dataclass
class FHIRResourceEntry:
    resource_type: str
    profile_url: str | None = None
    version: str = "4.0.1"
    description: str = ""
    search_params: list[FHIRSearchParam] = field(default_factory=list)
    operations: list[FHIROperation] = field(default_factory=list)
    required_elements: list[str] = field(default_factory=list)
    is_custom_profile: bool = False
    source_path: str = ""

    def to_dict(self) -> dict:
        return {
            "resource_type": self.resource_type,
            "profile_url": self.profile_url,
            "version": self.version,
            "description": self.description,
            "search_params": [{"name": p.name, "type": p.type, "description": p.description} for p in self.search_params],
            "operations": [{"name": o.name, "description": o.description, "http_method": o.http_method} for o in self.operations],
            "required_elements": self.required_elements,
            "is_custom_profile": self.is_custom_profile,
            "source_path": self.source_path,
        }


@dataclass
class FHIRCapabilityRest:
    mode: str = "server"
    resources: list[FHIRResourceEntry] = field(default_factory=list)
    operations: list[FHIROperation] = field(default_factory=list)
    security: dict | None = None

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "resources": [r.to_dict() for r in self.resources],
            "operations": [{"name": o.name, "description": o.description} for o in self.operations],
            "security": self.security,
        }


class FHIRCatalog:
    def __init__(self):
        self._resources: dict[str, FHIRResourceEntry] = {}
        self._project_root: str = os.path.abspath(
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        )

    def discover_fhir_resources(self) -> list[FHIRResourceEntry]:
        fhir_paths = self._find_fhir_dirs()
        for fhir_dir in fhir_paths:
            self._scan_fhir_dir(fhir_dir)
        if not self._resources:
            self._register_builtin()
        logger.info("Discovered %d FHIR resources", len(self._resources))
        return list(self._resources.values())

    def validate_resource_conformance(self, resource_type: str) -> dict:
        resource = self._resources.get(resource_type)
        if not resource:
            return {"valid": False, "errors": [f"Resource '{resource_type}' not found"]}
        errors = []
        warnings = []
        required = _REQUIRED_FHIR_ELEMENTS.get(resource_type, [])
        for elem in required:
            if elem not in [p.name for p in resource.search_params] and elem not in resource.required_elements:
                warnings.append(f"Required element '{elem}' not documented in search params or required elements")
        if resource.version not in _FHIR_VERSIONS:
            warnings.append(f"Unknown FHIR version '{resource.version}'")
        if not resource.search_params and resource_type in _REQUIRED_FHIR_ELEMENTS:
            warnings.append("No search parameters defined for standard resource")
        return {
            "valid": len(errors) == 0,
            "resource_type": resource_type,
            "fhir_version": resource.version,
            "errors": errors,
            "warnings": warnings,
        }

    def get_capability_statement(self) -> dict:
        rest = FHIRCapabilityRest(
            mode="server",
            resources=list(self._resources.values()),
            security={
                "cors": True,
                "service": [
                    {"coding": [{"system": "http://hl7.org/fhir/restful-security-service", "code": "Bearer"}]},
                ],
                "description": "JWT-based authentication with RBAC",
            },
        )
        return {
            "resourceType": "CapabilityStatement",
            "id": "gula-platform-fhir",
            "name": "GULA_Platform_FHIR",
            "title": "GULA Platform FHIR Capabilities",
            "status": "active",
            "date": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "publisher": "GULA Platform",
            "kind": "instance",
            "software": {
                "name": "GULA Platform",
                "version": "2.1.0",
                "releaseDate": datetime.now(UTC).strftime("%Y-%m-%d"),
            },
            "fhirVersion": "4.0.1",
            "acceptUnknown": "no",
            "format": ["json", "application/fhir+json"],
            "rest": [rest.to_dict()],
        }

    def get_resource(self, resource_type: str) -> FHIRResourceEntry | None:
        return self._resources.get(resource_type)

    def search(self, query: str) -> list[FHIRResourceEntry]:
        q = query.lower()
        return [
            r for r in self._resources.values()
            if q in r.resource_type.lower() or q in r.description.lower()
        ]

    def get_summary(self) -> dict:
        return {
            "total_resources": len(self._resources),
            "fhir_version": "4.0.1",
            "resource_types": sorted(self._resources.keys()),
            "custom_profiles": [r.resource_type for r in self._resources.values() if r.is_custom_profile],
        }

    def _find_fhir_dirs(self) -> list[str]:
        paths: list[str] = []
        potential = [
            os.path.join(self._project_root, "backend", "app", "fhir"),
            os.path.join(self._project_root, "backend", "app", "national", "fhir"),
            os.path.join(self._project_root, "services", "fhir"),
            os.path.join(self._project_root, "docs", "fhir"),
        ]
        for p in potential:
            if os.path.isdir(p):
                paths.append(p)
        return paths

    def _scan_fhir_dir(self, directory: str) -> None:
        for root, _dirs, files in os.walk(directory):
            for fname in files:
                if fname.endswith(".json"):
                    self._parse_fhir_json(os.path.join(root, fname))
                elif fname.endswith(".py") and not fname.startswith("__"):
                    self._parse_fhir_python(os.path.join(root, fname))

    def _parse_fhir_json(self, filepath: str) -> None:
        try:
            data = json.loads(Path(filepath).read_text())
            resource_type = data.get("resourceType") or data.get("type", "")
            if not resource_type:
                return
            name = resource_type
            profile_url = data.get("url") or data.get("baseDefinition")
            entry = FHIRResourceEntry(
                resource_type=name,
                profile_url=profile_url,
                description=data.get("description", data.get("purpose", "")),
                is_custom_profile=profile_url is not None,
                source_path=os.path.relpath(filepath, self._project_root),
                search_params=[
                    FHIRSearchParam(name=sp.get("name", ""), type=sp.get("type", ""), description=sp.get("documentation", ""))
                    for sp in data.get("searchParam", [])
                ],
                operations=[
                    FHIROperation(name=op.get("name", ""), description=op.get("documentation", ""))
                    for op in data.get("operation", [])
                ],
            )
            self._resources[name] = entry
        except (json.JSONDecodeError, KeyError) as exc:
            logger.debug("Error parsing FHIR JSON %s: %s", filepath, exc)

    def _parse_fhir_python(self, filepath: str) -> None:
        try:
            import ast
            with open(filepath, encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    resource_type = node.name.replace("Profile", "").replace("Resource", "")
                    if resource_type and resource_type[0].isupper():
                        self._resources[resource_type] = FHIRResourceEntry(
                            resource_type=resource_type,
                            description=ast.get_docstring(node) or "",
                            is_custom_profile="Profile" in node.name,
                            source_path=os.path.relpath(filepath, self._project_root),
                        )
        except SyntaxError:
            pass

    def _register_builtin(self) -> None:
        for resource_type, elements in _REQUIRED_FHIR_ELEMENTS.items():
            self._resources[resource_type] = FHIRResourceEntry(
                resource_type=resource_type,
                description=f"FHIR {resource_type} resource",
                version="4.0.1",
                required_elements=elements,
                search_params=[
                    FHIRSearchParam(name="identifier", type="token", description="External identifier"),
                    FHIRSearchParam(name="_id", type="token", description="Logical resource ID"),
                ],
            )


fhir_catalog = FHIRCatalog()
