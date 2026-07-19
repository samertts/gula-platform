from __future__ import annotations

from typing import Any

CAPABILITY_STATEMENT: dict[str, Any] = {
    "resourceType": "CapabilityStatement",
    "status": "active",
    "date": "2026-07-18",
    "publisher": "GULA Health Platform",
    "kind": "instance",
    "software": {
        "name": "GULA Platform FHIR Server",
        "version": "2.1.0",
        "releaseDate": "2026-07-18",
    },
    "fhirVersion": "4.0.1",
    "acceptUnknown": "no",
    "format": ["json"],
    "rest": [
        {
            "mode": "server",
            "documentation": "GULA Platform FHIR R4 API — National Digital Health Ecosystem",
            "security": {
                "cors": True,
                "service": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/restful-security-service",
                                "code": "SMART-on-FHIR",
                            }
                        ],
                        "text": "OAuth2 / JWT Bearer Token (SMART-on-FHIR compatible)",
                    }
                ],
                "description": "All FHIR endpoints require JWT Bearer authentication. Tenant isolation enforced via lab_id claims.",
            },
            "resource": [
                {
                    "type": "Patient",
                    "profile": "https://gula.health/fhir/StructureDefinition/GULAPatientProfile",
                    "interaction": [{"code": "read"}, {"code": "search-type"}],
                    "searchParam": [
                        {"name": "_id", "type": "token", "documentation": "Patient ID"},
                        {"name": "identifier", "type": "token", "documentation": "Health number or national ID"},
                        {"name": "name", "type": "string", "documentation": "Patient name"},
                        {"name": "birthdate", "type": "date", "documentation": "Date of birth"},
                        {"name": "gender", "type": "token", "documentation": "Gender"},
                    ],
                },
                {
                    "type": "Encounter",
                    "profile": "https://gula.health/fhir/StructureDefinition/GULAEncounterProfile",
                    "interaction": [{"code": "read"}, {"code": "search-type"}],
                    "searchParam": [
                        {"name": "patient", "type": "reference", "documentation": "Patient reference"},
                        {"name": "date", "type": "date", "documentation": "Encounter date"},
                        {"name": "status", "type": "token", "documentation": "Encounter status"},
                        {"name": "type", "type": "token", "documentation": "Encounter type"},
                    ],
                },
                {
                    "type": "Observation",
                    "profile": "https://gula.health/fhir/StructureDefinition/GULALaboratoryObservationProfile",
                    "interaction": [{"code": "read"}, {"code": "search-type"}],
                    "searchParam": [
                        {"name": "patient", "type": "reference", "documentation": "Patient reference"},
                        {"name": "code", "type": "token", "documentation": "LOINC or local test code"},
                        {"name": "category", "type": "token", "documentation": "Observation category"},
                        {"name": "date", "type": "date", "documentation": "Effective date"},
                        {"name": "status", "type": "token", "documentation": "Observation status"},
                    ],
                },
                {
                    "type": "Condition",
                    "profile": "https://gula.health/fhir/StructureDefinition/GULAConditionProfile",
                    "interaction": [{"code": "read"}, {"code": "search-type"}],
                    "searchParam": [
                        {"name": "patient", "type": "reference", "documentation": "Patient reference"},
                        {"name": "encounter", "type": "reference", "documentation": "Encounter reference"},
                        {"name": "clinical-status", "type": "token", "documentation": "Clinical status"},
                    ],
                },
                {
                    "type": "MedicationRequest",
                    "profile": "https://gula.health/fhir/StructureDefinition/GULAMedicationRequestProfile",
                    "interaction": [{"code": "read"}, {"code": "search-type"}],
                    "searchParam": [
                        {"name": "patient", "type": "reference", "documentation": "Patient reference"},
                        {"name": "status", "type": "token", "documentation": "Medication request status"},
                    ],
                },
                {
                    "type": "MedicationStatement",
                    "profile": "https://gula.health/fhir/StructureDefinition/GULAMedicationStatementProfile",
                    "interaction": [{"code": "read"}, {"code": "search-type"}],
                    "searchParam": [
                        {"name": "patient", "type": "reference", "documentation": "Patient reference"},
                        {"name": "status", "type": "token", "documentation": "Statement status"},
                    ],
                },
                {
                    "type": "AllergyIntolerance",
                    "profile": "https://gula.health/fhir/StructureDefinition/GULAAllergyIntoleranceProfile",
                    "interaction": [{"code": "read"}, {"code": "search-type"}],
                    "searchParam": [
                        {"name": "patient", "type": "reference", "documentation": "Patient reference"},
                        {"name": "clinical-status", "type": "token", "documentation": "Clinical status"},
                    ],
                },
                {
                    "type": "Immunization",
                    "profile": "https://gula.health/fhir/StructureDefinition/GULAImmunizationProfile",
                    "interaction": [{"code": "read"}, {"code": "search-type"}],
                    "searchParam": [
                        {"name": "patient", "type": "reference", "documentation": "Patient reference"},
                        {"name": "status", "type": "token", "documentation": "Immunization status"},
                    ],
                },
                {
                    "type": "CarePlan",
                    "profile": "https://gula.health/fhir/StructureDefinition/GULACarePlanProfile",
                    "interaction": [{"code": "read"}, {"code": "search-type"}],
                    "searchParam": [
                        {"name": "patient", "type": "reference", "documentation": "Patient reference"},
                        {"name": "status", "type": "token", "documentation": "Care plan status"},
                    ],
                },
                {
                    "type": "DocumentReference",
                    "profile": "https://gula.health/fhir/StructureDefinition/GULADocumentReferenceProfile",
                    "interaction": [{"code": "read"}, {"code": "search-type"}],
                    "searchParam": [
                        {"name": "patient", "type": "reference", "documentation": "Patient reference"},
                        {"name": "category", "type": "token", "documentation": "Document category"},
                    ],
                },
                {
                    "type": "Composition",
                    "profile": "https://gula.health/fhir/StructureDefinition/GULACompositionProfile",
                    "interaction": [{"code": "read"}, {"code": "search-type"}],
                    "searchParam": [
                        {"name": "patient", "type": "reference", "documentation": "Patient reference"},
                        {"name": "status", "type": "token", "documentation": "Composition status"},
                    ],
                },
                {
                    "type": "DiagnosticReport",
                    "profile": "https://gula.health/fhir/StructureDefinition/GULADiagnosticReportProfile",
                    "interaction": [{"code": "read"}, {"code": "search-type"}],
                    "searchParam": [
                        {"name": "patient", "type": "reference", "documentation": "Patient reference"},
                        {"name": "status", "type": "token", "documentation": "Report status"},
                    ],
                },
                {
                    "type": "Specimen",
                    "profile": "https://gula.health/fhir/StructureDefinition/GULASpecimenProfile",
                    "interaction": [{"code": "read"}, {"code": "search-type"}],
                },
                {
                    "type": "ServiceRequest",
                    "profile": "https://gula.health/fhir/StructureDefinition/GULAServiceRequestProfile",
                    "interaction": [{"code": "read"}, {"code": "search-type"}],
                },
                {
                    "type": "Organization",
                    "profile": "https://gula.health/fhir/StructureDefinition/GULAOrganizationProfile",
                    "interaction": [{"code": "read"}, {"code": "search-type"}],
                },
                {
                    "type": "Practitioner",
                    "profile": "https://gula.health/fhir/StructureDefinition/GULAPractitionerProfile",
                    "interaction": [{"code": "read"}, {"code": "search-type"}],
                },
            ],
        }
    ],
}

IMPLEMENTED_RESOURCES = [
    "Patient",
    "Encounter",
    "Observation",
    "Condition",
    "MedicationRequest",
    "MedicationStatement",
    "AllergyIntolerance",
    "Immunization",
    "CarePlan",
    "DocumentReference",
    "Composition",
    "DiagnosticReport",
    "Specimen",
    "ServiceRequest",
    "Procedure",
    "Organization",
    "Practitioner",
]

PLANNED_RESOURCES = [
    "Procedure",
    "Bundle",
    "Goal",
    "Device",
    "Location",
    "Provenance",
]

STUBBED_RESOURCES = {
    "Bundle": "routes/ehr_fhir.py:997 — returns 501",
}


def get_capability_statement() -> dict[str, Any]:
    return CAPABILITY_STATEMENT


def get_implemented_resources() -> list[str]:
    return IMPLEMENTED_RESOURCES


def get_resource_endpoints_summary() -> dict[str, str]:
    return {
        "Patient": "GET /fhir/Patient/{id}, GET /fhir/Patient (search)",
        "Encounter": "GET /fhir/Encounter/{id}, GET /fhir/Encounter (search)",
        "Observation": "GET /fhir/Observation/{id}, GET /fhir/Observation (search)",
        "Condition": "GET /fhir/Condition/{id}, GET /fhir/Condition (search)",
        "MedicationRequest": "GET /fhir/MedicationRequest/{id}, GET /fhir/MedicationRequest (search)",
        "MedicationStatement": "GET /fhir/MedicationStatement/{id}, GET /fhir/MedicationStatement (search)",
        "AllergyIntolerance": "GET /fhir/AllergyIntolerance/{id}, GET /fhir/AllergyIntolerance (search)",
        "Immunization": "GET /fhir/Immunization/{id}, GET /fhir/Immunization (search)",
        "CarePlan": "GET /fhir/CarePlan/{id}, GET /fhir/CarePlan (search)",
        "DocumentReference": "GET /fhir/DocumentReference/{id}, GET /fhir/DocumentReference (search)",
        "Composition": "GET /fhir/Composition/{id}, GET /fhir/Composition (search)",
        "Procedure": "GET /fhir/Procedure/{id}, GET /fhir/Procedure (search)",
        "Bundle": "GET /fhir/Bundle/{id} (stub — 501)",
    }
