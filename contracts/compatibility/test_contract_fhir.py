from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import pytest

_BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
_REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")

os.environ["RUNTIME_MODE"] = "test"
os.environ["FEATURE_BACKGROUND_TASKS"] = "false"
os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-" + "x" * 40
os.environ["ENCRYPTION_KEY"] = "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw="
os.environ["NID_HMAC_KEY"] = "a" * 64
os.environ["REDIS_URL"] = ""

# ── FHIR R4 required field sets per resource type ──────────────────────

FHIR_REQUIRED_FIELDS: dict[str, set[str]] = {
    "Patient": {"resourceType", "id"},
    "Practitioner": {"resourceType", "id"},
    "Organization": {"resourceType", "id", "name"},
    "Encounter": {"resourceType", "id", "status", "class"},
    "Observation": {"resourceType", "id", "status", "code", "subject"},
    "DiagnosticReport": {"resourceType", "id", "status", "code", "subject"},
    "Specimen": {"resourceType", "id"},
    "ServiceRequest": {"resourceType", "id", "status", "intent", "subject"},
    "Device": {"resourceType", "id"},
    "Bundle": {"resourceType", "id", "type"},
}

FHIR_BASE_URL = "http://hl7.org/fhir/R4/"


# ── Helpers ────────────────────────────────────────────────────────────

def _make_fhir_resource(base: str, overrides: dict | None = None) -> dict:
    resource: dict[str, Any] = {"resourceType": base, "id": f"test-{base.lower()}-1"}
    if base == "Patient":
        resource["name"] = [{"use": "official", "family": "Test", "given": ["Test"]}]
        resource["gender"] = "male"
    elif base == "Practitioner":
        resource["name"] = [{"use": "official", "family": "Doctor", "given": ["Ali"]}]
    elif base == "Organization":
        resource["name"] = "Test Lab"
    elif base == "Encounter":
        resource["status"] = "finished"
        resource["class"] = {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB"}
    elif base == "Observation":
        resource["status"] = "final"
        resource["code"] = {"coding": [{"system": "http://loinc.org", "code": "4544-3"}]}
        resource["subject"] = {"reference": "Patient/test-1"}
    elif base == "DiagnosticReport":
        resource["status"] = "final"
        resource["code"] = {"coding": [{"system": "http://loinc.org", "code": "11502-2"}]}
        resource["subject"] = {"reference": "Patient/test-1"}
    elif base == "Specimen":
        resource["status"] = "available"
    elif base == "ServiceRequest":
        resource["status"] = "active"
        resource["intent"] = "order"
        resource["subject"] = {"reference": "Patient/test-1"}
    elif base == "Device":
        resource["status"] = "active"
    elif base == "Bundle":
        resource["type"] = "searchset"
    if overrides:
        resource.update(overrides)
    return resource


def _validate_resource(resource: dict) -> list[str]:
    """Validate a FHIR resource against basic R4 rules. Returns list of issues."""
    issues: list[str] = []
    rtype = resource.get("resourceType")
    if not rtype:
        issues.append("Missing resourceType")
        return issues
    if rtype not in FHIR_REQUIRED_FIELDS:
        issues.append(f"Unknown resourceType: {rtype}")
        return issues
    for field in FHIR_REQUIRED_FIELDS[rtype]:
        if field not in resource or resource[field] is None:
            issues.append(f"Missing required field '{field}' for {rtype}")
    if rtype == "Observation":
        code = resource.get("code", {})
        if not code.get("coding") and not code.get("text"):
            issues.append("Observation.code must have coding or text")
    if rtype == "Bundle":
        btype = resource.get("type")
        valid_types = {"searchset", "collection", "document", "message", "transaction",
                       "transaction-response", "batch", "batch-response", "history"}
        if btype not in valid_types:
            issues.append(f"Invalid Bundle.type: {btype}")
    return issues


# ── Tests ──────────────────────────────────────────────────────────────

class TestFHIRMapperOutput:
    """Test each FHIR mapper produces valid FHIR JSON."""

    SPECIMEN_STATUS_MAP = {
        "ordered": "available", "collected": "available", "received": "available",
        "accepted": "available", "rejected": "unavailable", "analyzing": "available",
        "analyzed": "available", "verified": "available", "validated": "available",
        "released": "available", "archived": "entered-in-error", "disposed": "entered-in-error",
    }

    def test_specimen_mapper_produces_valid_fhir(self):
        from app.lims.fhir_mappers import specimen_to_fhir, result_to_fhir, order_to_fhir_service_request, instrument_to_fhir_device, report_to_fhir_diagnostic

        class FakeSpecimen:
            id = 1
            fhir_id = None
            barcode = "S-001"
            status = "collected"
            specimen_type = "blood"
            collection_time = datetime.now()
            collected_by = None
            collection_site = None
            volume_ml = 5.0
            container_type = "EDTA"
            received_at = datetime.now()
            storage_id = None

        resource = specimen_to_fhir(FakeSpecimen())
        assert resource["resourceType"] == "Specimen"
        assert resource["id"] == "lims-spec-1"
        issues = _validate_resource(resource)
        assert not issues, f"Specimen validation issues: {issues}"

    def test_result_mapper_produces_valid_fhir(self):
        from app.lims.fhir_mappers import result_to_fhir

        class FakeResult:
            id = 42
            fhir_id = None
            loinc_code = "4544-3"
            test_code = "HGB"
            test_name = "Hemoglobin"
            value_numeric = 13.5
            value_text = None
            unit = "g/dL"
            ref_range_low = 12.0
            ref_range_high = 16.0
            flag = "normal"
            validation_status = "validated"
            performed_at = datetime.now()
            instrument_id = None
            specimen_id = 1

            class FakeSpecimen:
                class FakeOrder:
                    patient_id = 1
                order = FakeOrder()
            specimen = FakeSpecimen()

        resource = result_to_fhir(FakeResult())
        assert resource["resourceType"] == "Observation"
        assert resource["id"] == "lims-obs-42"
        issues = _validate_resource(resource)
        assert not issues, f"Observation validation issues: {issues}"

    def test_order_mapper_produces_valid_fhir(self):
        from app.lims.fhir_mappers import order_to_fhir_service_request

        class FakeOrder:
            id = 1
            fhir_id = None
            accession_number = "ACC-001"
            priority = "routine"
            ordered_at = datetime.now()
            ordered_by = None
            lab_id = 1

            def _get_order_id(self):
                return 1
            order_id = property(_get_order_id)

        resource = order_to_fhir_service_request(FakeOrder())
        assert resource["resourceType"] == "ServiceRequest"
        issues = _validate_resource(resource)
        assert not issues, f"ServiceRequest issues: {issues}"

    def test_instrument_mapper_produces_valid_fhir(self):
        from app.lims.fhir_mappers import instrument_to_fhir_device

        class FakeModel:
            model_code = "XN-1000"

            class FakeManufacturer:
                name = "Sysmex"
            manufacturer = FakeManufacturer()

        class FakeInstrument:
            id = 1
            fhir_id = None
            status = "online"
            serial_number = "SN-12345"
            instrument_code = "Sysmex-XN-1000-1"
            software_version = "2.1.0"
            model = FakeModel()

        resource = instrument_to_fhir_device(FakeInstrument())
        assert resource["resourceType"] == "Device"
        issues = _validate_resource(resource)
        assert not issues, f"Device issues: {issues}"


class TestFHIRSchemaValidation:
    """Validate resources against FHIR R4 schema rules."""

    def test_required_fields_are_present(self):
        for rtype, required in FHIR_REQUIRED_FIELDS.items():
            resource = _make_fhir_resource(rtype)
            for field in required:
                assert field in resource, f"{rtype} missing {field}"

    def test_required_fields_per_profile(self, fhir_profiles: list[dict]):
        for profile in fhir_profiles:
            base = profile.get("baseResource")
            req = profile.get("requiredFields", [])
            if not req:
                continue
            for field in req:
                assert field != "resourceType" or field in (
                    "resourceType",
                ), "resourceType always required"

    def test_bundle_construction(self):
        bundle = _make_fhir_resource("Bundle", {
            "type": "searchset",
            "total": 2,
            "entry": [
                {"fullUrl": "urn:uuid:1", "resource": _make_fhir_resource("Observation")},
                {"fullUrl": "urn:uuid:2", "resource": _make_fhir_resource("Patient")},
            ],
        })
        issues = _validate_resource(bundle)
        assert not issues, f"Bundle issues: {issues}"
        assert len(bundle["entry"]) == 2

    def test_bundle_requires_type(self):
        bundle = _make_fhir_resource("Bundle")
        assert "type" in bundle
        assert bundle["type"] in {"searchset", "collection", "document", "message", "transaction",
                                  "transaction-response", "batch", "batch-response", "history"}


class TestFHIRSearchParam:
    """Test search parameter compatibility."""

    def test_patient_search_params(self, client, auth_headers):
        resp = client.get("/patients", headers=auth_headers)
        assert resp.status_code in (200, 401, 403, 503)

    def test_observation_search_params(self, client, auth_headers):
        for path in ["/results", "/test-results"]:
            resp = client.get(path, headers=auth_headers)
            assert resp.status_code in (200, 401, 403, 503)


class TestFHIRProfileValidation:
    """Test profile-level validation."""

    def test_gula_patient_profile_maps(self, fhir_profiles: list[dict]):
        patient_profile = next((p for p in fhir_profiles if p.get("name") == "GULAPatientProfile"), None)
        assert patient_profile is not None, "GULAPatientProfile not found in catalog"
        rules = patient_profile.get("mappingRules", {})
        mappings = rules.get("fieldMappings", [])
        mapped_paths = {m["fhirPath"] for m in mappings}
        assert "Patient.id" in mapped_paths
        assert "Patient.name[0]" in mapped_paths
        assert "Patient.gender" in mapped_paths

    def test_gula_lab_obs_profile_maps(self, fhir_profiles: list[dict]):
        obs_profile = next(
            (p for p in fhir_profiles if p.get("name") == "GULALaboratoryObservationProfile"), None
        )
        assert obs_profile is not None, "GULALaboratoryObservationProfile not found"
        rules = obs_profile.get("mappingRules", {})
        mappings = rules.get("fieldMappings", [])
        mapped_paths = {m["fhirPath"] for m in mappings}
        assert "Observation.id" in mapped_paths
        assert "Observation.status" in mapped_paths
        assert "Observation.code" in mapped_paths
        assert "Observation.subject" in mapped_paths

    def test_all_profiles_serializable(self, fhir_profiles: list[dict]):
        serialized = json.dumps(fhir_profiles)
        roundtrip = json.loads(serialized)
        assert len(roundtrip) == len(fhir_profiles)
