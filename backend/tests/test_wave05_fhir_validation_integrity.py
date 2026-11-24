"""Wave 05 — FHIR structural validation must fail closed on detected errors.

The repository's FHIRValidationEngine previously recorded errors for malformed
Patient.identifier and invalid Encounter.status while leaving ``valid=True``.
These tests use synthetic resources only (no PHI/PII) and do not claim full FHIR
conformance; they verify that the structural pre-check reports failure when it
detects an error.
"""

from __future__ import annotations

from app.national.fhir.validation import FHIRValidationEngine


def test_patient_identifier_shape_error_marks_resource_invalid() -> None:
    result = FHIRValidationEngine().validate(
        {"resourceType": "Patient", "id": "synthetic-patient", "identifier": {"value": "x"}}
    )
    assert result.valid is False
    assert "Patient.identifier must be a list" in result.errors


def test_encounter_invalid_status_error_marks_resource_invalid_even_with_all_required_fields() -> None:
    result = FHIRValidationEngine().validate(
        {
            "resourceType": "Encounter",
            "id": "synthetic-encounter",
            "status": "not-a-fhir-status",
            "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB"},
        }
    )
    assert result.valid is False
    assert any("Invalid Encounter status" in error for error in result.errors)


def test_well_formed_required_fields_remain_valid() -> None:
    result = FHIRValidationEngine().validate(
        {
            "resourceType": "Encounter",
            "id": "synthetic-encounter",
            "status": "finished",
            "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB"},
        }
    )
    assert result.valid is True
    assert result.errors == []


def test_missing_required_field_still_fails_closed() -> None:
    result = FHIRValidationEngine().validate({"resourceType": "Observation", "id": "synthetic-obs"})
    assert result.valid is False
    assert any("Missing required field" in error for error in result.errors)
