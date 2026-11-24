"""Wave 05.1 — structural FHIR R4 validation boundaries.

Synthetic resources only. This is a structural pre-check test suite, not a
claim of official FHIR conformance, terminology licensing or clinical acceptance.
"""

from __future__ import annotations

from app.national.fhir.validation import FHIRValidationEngine


def _meta() -> dict:
    return {"source": "synthetic://wave05-1"}


def test_patient_identifier_shape_still_fails_closed() -> None:
    result = FHIRValidationEngine().validate(
        {"resourceType": "Patient", "id": "syn-patient", "identifier": {"value": "SYN-1"}}
    )
    assert result.valid is False
    assert any("Patient.identifier must be a list" in error for error in result.errors)


def test_patient_identifier_entries_require_value() -> None:
    result = FHIRValidationEngine().validate(
        {"resourceType": "Patient", "id": "syn-patient", "identifier": [{"system": "synthetic"}]}
    )
    assert result.valid is False
    assert any("identifier[0].value is required" in error for error in result.errors)


def test_encounter_status_and_class_shape_are_validated() -> None:
    engine = FHIRValidationEngine()
    invalid = engine.validate(
        {"resourceType": "Encounter", "id": "syn-enc", "status": "not-a-status", "class": "AMB"}
    )
    assert invalid.valid is False
    assert any("Invalid Encounter status" in error for error in invalid.errors)
    assert any("Encounter.class must be a Coding object" in error for error in invalid.errors)


def test_clinical_resources_require_subject_references() -> None:
    engine = FHIRValidationEngine()
    for resource_type in ("Condition", "Procedure", "DiagnosticReport", "ServiceRequest"):
        resource = {"resourceType": resource_type, "id": "syn-resource", "meta": _meta()}
        result = engine.validate(resource)
        assert result.valid is False, resource_type
        assert any("Missing required field: subject" in error for error in result.errors)


def test_allergy_requires_patient_reference() -> None:
    result = FHIRValidationEngine().validate(
        {"resourceType": "AllergyIntolerance", "id": "syn-allergy", "meta": _meta()}
    )
    assert result.valid is False
    assert any("Missing required field: patient" in error for error in result.errors)


def test_broken_reference_shape_is_rejected() -> None:
    result = FHIRValidationEngine().validate(
        {
            "resourceType": "Observation",
            "id": "syn-obs",
            "status": "final",
            "code": {"coding": [{"system": "synthetic", "code": "SYN"}]},
            "subject": {"reference": "not-a-reference"},
            "meta": _meta(),
        }
    )
    assert result.valid is False
    assert any("Broken reference in subject" in error for error in result.errors)


def test_provenance_and_audit_event_required_elements() -> None:
    engine = FHIRValidationEngine()
    provenance = engine.validate({"resourceType": "Provenance", "id": "syn-prov"})
    assert provenance.valid is False
    assert any("Missing required field: target" in error for error in provenance.errors)

    audit = engine.validate({"resourceType": "AuditEvent", "id": "syn-audit"})
    assert audit.valid is False
    assert any("Missing required field: recorded" in error for error in audit.errors)


def test_bundle_duplicate_full_url_and_unresolved_local_reference_fail() -> None:
    bundle = {
        "resourceType": "Bundle",
        "id": "syn-bundle",
        "type": "collection",
        "meta": _meta(),
        "entry": [
            {
                "fullUrl": "urn:uuid:syn-1",
                "resource": {"resourceType": "Patient", "id": "syn-1"},
            },
            {
                "fullUrl": "urn:uuid:syn-1",
                "resource": {
                    "resourceType": "Observation",
                    "id": "syn-obs",
                    "status": "final",
                    "code": {"coding": [{"system": "synthetic", "code": "SYN"}]},
                    "subject": {"reference": "#missing"},
                    "meta": _meta(),
                },
            },
        ],
    }
    result = FHIRValidationEngine().validate(bundle)
    assert result.valid is False
    assert any("Duplicate Bundle.entry.fullUrl" in error for error in result.errors)
    assert any("Unresolved local Bundle reference" in error for error in result.errors)


def test_valid_synthetic_bundle_passes_and_preserves_provenance() -> None:
    bundle = {
        "resourceType": "Bundle",
        "id": "syn-bundle-valid",
        "type": "collection",
        "meta": _meta(),
        "entry": [
            {
                "fullUrl": "urn:uuid:syn-1",
                "resource": {
                    "resourceType": "Patient",
                    "id": "syn-1",
                    "identifier": [{"system": "synthetic", "value": "SYN-1"}],
                    "meta": _meta(),
                },
            },
            {
                "fullUrl": "urn:uuid:syn-obs",
                "resource": {
                    "resourceType": "Observation",
                    "id": "syn-obs",
                    "status": "final",
                    "code": {"coding": [{"system": "synthetic", "code": "SYN"}]},
                    "subject": {"reference": "#syn-1"},
                    "meta": _meta(),
                },
            },
        ],
    }
    result = FHIRValidationEngine().validate(bundle)
    assert result.valid is True
    assert result.errors == []
    assert result.warnings == []


def test_unknown_resource_type_remains_structural_precheck() -> None:
    result = FHIRValidationEngine().validate({"resourceType": "UnknownType"})
    assert result.valid is True
