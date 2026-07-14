from __future__ import annotations

from enum import Enum


class Fhir_interoperabilityPermission(Enum):
    FHIR.READ = "fhir_interoperability:fhir.read"
    FHIR.WRITE = "fhir_interoperability:fhir.write"
    FHIR.ADMIN = "fhir_interoperability:fhir.admin"
    TERMINOLOGY.READ = "fhir_interoperability:terminology.read"

    def describe(self) -> str:
        descriptions = {        "fhir_interoperability:fhir.read": "Fhir.Read",
                "fhir_interoperability:fhir.write": "Fhir.Write",
                "fhir_interoperability:fhir.admin": "Fhir.Admin",
                "fhir_interoperability:terminology.read": "Terminology.Read"}
        return descriptions.get(self, self.value)
