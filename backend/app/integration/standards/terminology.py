from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("gula.integration.standards.terminology")


@dataclass
class CodeSystem:
    id: str = ""
    name: str = ""
    version: str = ""
    oid: str = ""
    url: str = ""
    concepts: dict[str, str] = field(default_factory=dict)

    def lookup(self, code: str) -> str | None:
        return self.concepts.get(code)

    def validate(self, code: str) -> bool:
        return code in self.concepts


class TerminologyService:
    def __init__(self):
        self._systems: dict[str, CodeSystem] = {}
        self._supported_systems: dict[str, str] = {
            "LOINC": "http://loinc.org",
            "SNOMED-CT": "http://snomed.info/sct",
            "ICD-10": "http://hl7.org/fhir/sid/icd-10",
            "ICD-10-CM": "http://hl7.org/fhir/sid/icd-10-cm",
            "CPT": "http://www.ama-assn.org/go/cpt",
            "UCUM": "http://unitsofmeasure.org",
            "RXNORM": "http://www.nlm.nih.gov/research/umls/rxnorm",
            "ATC": "http://www.whocc.no/atc",
            "ISO-3166": "urn:iso:std:iso:3166",
            "IETF-LANGUAGE": "urn:ietf:bcp:47",
        }

    def register_system(self, system: CodeSystem) -> None:
        self._systems[system.id] = system
        logger.info("Code system registered: %s (%s)", system.id, system.name)

    def get_system(self, system_id: str) -> CodeSystem | None:
        if system_id in self._systems:
            return self._systems[system_id]
        if system_id in self._supported_systems:
            cs = CodeSystem(id=system_id, name=system_id, url=self._supported_systems[system_id])
            self._systems[system_id] = cs
            return cs
        return None

    def lookup(self, system_id: str, code: str) -> str | None:
        system = self.get_system(system_id)
        if system:
            return system.lookup(code)
        return None

    def validate(self, system_id: str, code: str) -> bool:
        system = self.get_system(system_id)
        if system:
            return system.validate(code)
        return system_id in self._supported_systems

    def list_systems(self) -> list[str]:
        return list(self._supported_systems.keys()) + [s.id for s in self._systems.values() if s.id not in self._supported_systems]

    def is_supported(self, system_id: str) -> bool:
        return system_id in self._supported_systems or system_id in self._systems
