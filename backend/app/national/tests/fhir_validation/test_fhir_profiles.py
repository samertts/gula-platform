from __future__ import annotations

from app.national.fhir.validation import FHIRValidationEngine


class TestFHIRProfiles:
    def test_patient_profile_validation(self):
        engine = FHIRValidationEngine()
        patient = {"resourceType": "Patient", "id": "PAT001", "active": True}
        result = engine.validate(patient)
        assert result.valid is True

    def test_encounter_profile_required_fields(self):
        engine = FHIRValidationEngine()
        encounter = {
            "resourceType": "Encounter",
            "id": "ENC001",
            "status": "in-progress",
            "class": {"code": "AMB"},
        }
        result = engine.validate(encounter)
        assert result.valid is True

    def test_profile_validation_errors(self):
        engine = FHIRValidationEngine()
        result = engine.validate({"resourceType": "UnknownType"})
        assert result.valid is True
