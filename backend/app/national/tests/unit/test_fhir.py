from __future__ import annotations

from datetime import date

from app.national.enums import Gender, MaritalStatus
from app.national.fhir.bundle import FHIRBundle, FHIRBundleEntry
from app.national.fhir.observation import FHIRObservationMapper
from app.national.fhir.patient import FHIRPatientMapper
from app.national.fhir.search import FHIRSearchEngine
from app.national.fhir.validation import FHIRValidationEngine


class TestFHIRPatientMapper:
    def test_from_citizen(self):
        citizen = MockCitizen()
        result = FHIRPatientMapper.from_citizen(citizen)
        assert result["resourceType"] == "Patient"
        assert result["id"] == "CIT001"
        assert result["gender"] == "male"
        assert len(result["identifier"]) > 0

    def test_identifiers_include_health_number(self):
        citizen = MockCitizen()
        result = FHIRPatientMapper.from_citizen(citizen)
        identifiers = result.get("identifier", [])
        health_ids = [i for i in identifiers if "health-number" in i.get("system", "")]
        assert len(health_ids) > 0


class MockCitizen:
    id = "CIT001"
    fhir_id = None
    health_number = "IQ12345678"
    national_id_hash = "abc123hash"
    first_name = "Ali"
    father_name = "Ahmed"
    last_name = "Hassan"
    full_name_ar = "علي أحمد حسن"
    date_of_birth = date(1990, 1, 15)
    gender = Gender.MALE
    marital_status = MaritalStatus.MARRIED
    phone = "+9647701234567"
    email = "ali@example.com"
    governorate = "Baghdad"
    district = "Karkh"
    street = "Main Street"
    nationality = "Iraqi"
    is_deleted = False
    is_deceased = False
    deceased_date = None


class TestFHIRValidation:
    def test_valid_patient(self):
        engine = FHIRValidationEngine()
        resource = {"resourceType": "Patient", "id": "PAT001"}
        result = engine.validate(resource)
        assert result.valid is True

    def test_missing_required_field(self):
        engine = FHIRValidationEngine()
        resource = {"id": "PAT001"}
        result = engine.validate(resource)
        assert result.valid is False

    def test_invalid_encounter_status(self):
        engine = FHIRValidationEngine()
        resource = {"resourceType": "Encounter", "id": "ENC001", "status": "invalid_status"}
        result = engine.validate(resource)
        assert result.valid is False


class TestFHIRBundle:
    def test_create_bundle(self):
        bundle = FHIRBundle(bundle_type="searchset")
        bundle.id = "bundle-1"
        entry = FHIRBundleEntry(full_url="http://example.com/Patient/1", resource={"resourceType": "Patient", "id": "1"})
        bundle.add_entry(entry)
        result = bundle.to_dict()
        assert result["resourceType"] == "Bundle"
        assert result["total"] == 1
        assert len(result["entry"]) == 1

    def test_empty_bundle(self):
        bundle = FHIRBundle()
        result = bundle.to_dict()
        assert result["total"] == 0
        assert result["entry"] == []


class TestFHIRSearch:
    def test_search_parameters_for_patient(self):
        engine = FHIRSearchEngine()
        params = engine.get_search_parameters("Patient")
        assert len(params) > 0
        assert any(p.name == "identifier" for p in params)

    def test_build_search_query(self):
        engine = FHIRSearchEngine()
        query = engine.build_search_query("Patient", {"name": "Ali", "_count": "10"})
        assert query["limit"] == 10
        assert len(query["filters"]) == 1


class TestFHIRObservation:
    def test_from_lab_result(self):
        result = {
            "id": "RES001", "test_code": "4544-3", "test_name": "Hemoglobin",
            "value": "13.5", "unit": "g/dL", "flag": "normal",
            "normal_range_low": "12.0", "normal_range_high": "16.0",
            "created_at": "2026-05-01T10:00:00",
        }
        fhir = FHIRObservationMapper.from_lab_result(result, "PAT001")
        assert fhir["resourceType"] == "Observation"
        assert fhir["code"]["coding"][0]["code"] == "4544-3"
        assert fhir["valueQuantity"]["value"] == 13.5
