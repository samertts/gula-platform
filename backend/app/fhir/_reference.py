from __future__ import annotations

FHIR_RESOURCE_TYPES = {
    "Patient": {"status": "implemented", "routes": ["read", "search"]},
    "Encounter": {"status": "implemented", "routes": ["read", "search"]},
    "Observation": {"status": "implemented", "routes": ["read", "search"]},
    "Condition": {"status": "implemented", "routes": ["read", "search"]},
    "MedicationRequest": {"status": "implemented", "routes": ["read", "search"]},
    "MedicationStatement": {"status": "implemented", "routes": ["read", "search"]},
    "AllergyIntolerance": {"status": "implemented", "routes": ["read", "search"]},
    "Immunization": {"status": "implemented", "routes": ["read", "search"]},
    "CarePlan": {"status": "implemented", "routes": ["read", "search"]},
    "DocumentReference": {"status": "implemented", "routes": ["read", "search"]},
    "Composition": {"status": "implemented", "routes": ["read", "search"]},
    "DiagnosticReport": {"status": "implemented", "routes": ["read", "search"]},
    "Specimen": {"status": "implemented", "routes": ["read", "search"]},
    "ServiceRequest": {"status": "implemented", "routes": ["read", "search"]},
    "Organization": {"status": "implemented", "routes": ["read", "search"]},
    "Practitioner": {"status": "implemented", "routes": ["read", "search"]},
    "Procedure": {"status": "stub", "routes": ["read"]},
    "Bundle": {"status": "stub", "routes": ["read"]},
    "Goal": {"status": "planned", "routes": []},
    "Device": {"status": "planned", "routes": []},
    "Location": {"status": "planned", "routes": []},
    "Provenance": {"status": "planned", "routes": []},
}

REQUIRED_FIELDS = {
    "Patient": ["resourceType", "id", "name", "gender", "birthDate"],
    "Encounter": ["resourceType", "id", "status", "class", "subject", "period"],
    "Observation": ["resourceType", "id", "status", "code", "subject", "effectiveDateTime", "issued"],
    "Condition": ["resourceType", "id", "subject", "code"],
    "MedicationRequest": ["resourceType", "id", "status", "intent", "medicationCodeableConcept", "subject"],
    "MedicationStatement": ["resourceType", "id", "status", "medicationCodeableConcept", "subject"],
    "AllergyIntolerance": ["resourceType", "id", "patient", "code"],
    "Immunization": ["resourceType", "id", "status", "vaccineCode", "patient", "occurrenceDateTime"],
    "CarePlan": ["resourceType", "id", "status", "intent", "subject"],
    "DocumentReference": ["resourceType", "id", "status", "type", "subject", "content"],
    "Composition": ["resourceType", "id", "status", "type", "subject", "date", "author", "title"],
    "DiagnosticReport": ["resourceType", "id", "status", "code", "subject", "issued", "result"],
    "Specimen": ["resourceType", "id", "type", "subject"],
    "ServiceRequest": ["resourceType", "id", "status", "intent", "code", "subject"],
    "Organization": ["resourceType", "id", "name"],
    "Practitioner": ["resourceType", "id", "name"],
}

VALID_CODE_SYSTEMS = {
    "http://loinc.org": "LOINC",
    "http://snomed.info/sct": "SNOMED CT",
    "http://hl7.org/fhir/sid/icd-10": "ICD-10",
    "http://hl7.org/fhir/sid/icd-10-am": "ICD-10-AM",
    "http://terminology.hl7.org/CodeSystem/v3-ActCode": "v3 ActCode",
    "http://terminology.hl7.org/CodeSystem/condition-clinical": "ConditionClinical",
    "http://terminology.hl7.org/CodeSystem/condition-ver-status": "ConditionVerStatus",
    "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical": "AllergyIntoleranceClinical",
    "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification": "AllergyIntoleranceVerification",
    "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation": "ObservationInterpretation",
    "http://terminology.hl7.org/CodeSystem/observation-status": "ObservationStatus",
    "http://terminology.hl7.org/CodeSystem/diagnostic-report-status": "DiagnosticReportStatus",
    "http://terminology.hl7.org/CodeSystem/request-intent": "RequestIntent",
    "http://terminology.hl7.org/CodeSystem/request-status": "RequestStatus",
    "http://unitsofmeasure.org": "UCUM",
    "urn:gula:health-number": "GULA Health Number",
}


def validate_resource_coverage() -> dict:
    implemented = {
        k: v for k, v in FHIR_RESOURCE_TYPES.items() if v["status"] == "implemented"
    }
    stubs = {k: v for k, v in FHIR_RESOURCE_TYPES.items() if v["status"] == "stub"}
    planned = {k: v for k, v in FHIR_RESOURCE_TYPES.items() if v["status"] == "planned"}

    return {
        "total_resource_types": len(FHIR_RESOURCE_TYPES),
        "implemented": implemented,
        "stubs_requiring_completion": stubs,
        "planned": planned,
        "coverage_pct": round(len(implemented) / len(FHIR_RESOURCE_TYPES) * 100, 1),
        "fhir_version": "R4 (4.0.1)",
    }
