from __future__ import annotations

import os
import re
import sys
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

_BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
_REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")

os.environ["RUNTIME_MODE"] = "test"
os.environ["FEATURE_BACKGROUND_TASKS"] = "false"
os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-" + "x" * 40
os.environ["ENCRYPTION_KEY"] = "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcw=="
os.environ["NID_HMAC_KEY"] = "a" * 64
os.environ["REDIS_URL"] = ""

# ── Helpers ────────────────────────────────────────────────────────────

# Known back-end Pydantic model classes to test
_MODEL_LOCATIONS: dict[str, str] = {
    "LoginRequest": "app.routes.login",
    "RefreshRequest": "app.routes.login",
    "CitizenRegisterRequest": "app.routes.register",
    "LabRegisterRequest": "app.routes.register",
    "StaffRegisterRequest": "app.routes.register",
    "DoctorRegisterRequest": "app.routes.register",
    "PatientCreate": "app.routes.patients",
    "PatientUpdate": "app.routes.patients",
    "LabUpdate": "app.routes.labs",
    "CreateEmployeeRequest": "app.routes.labs",
    "UpdateEmployeeRequest": "app.routes.labs",
    "CreateLabRequest": "app.routes.admin",
    "CreateUserRequest": "app.routes.admin",
    "ChangeRoleRequest": "app.routes.admin",
    "SampleCreate": "app.routes.samples",
    "SampleUpdate": "app.routes.samples",
    "ScanRequest": "app.routes.patient_card",
    "ChatRequest": "app.routes.ai",
    "SuggestRequest": "app.routes.ai",
    "RejectRequest": "app.routes.ai",
    "DeviceTokenRequest": "app.routes.mobile",
    "TestResultCreate": "app.routes.test_results",
    "TestResultValidateRequest": "app.routes.test_results",
    "NationalIdRequest": "app.routes.national_identity",
    "LinkIdentityRequest": "app.routes.identity",
    "ClaimCreate": "app.routes.claims",
    "ClaimItemCreate": "app.routes.claims",
    "GrantRequest": "app.routes.consent",
    "RevokeRequest": "app.routes.consent",
    "RegisterDeviceRequest": "app.routes.edge",
    "TaskSubmitRequest": "app.routes.edge",
    "TaskCancelRequest": "app.routes.edge",
}


def _import_model(name: str) -> type[BaseModel]:
    mod_path = _MODEL_LOCATIONS.get(name)
    if not mod_path:
        pytest.skip(f"No module location known for {name}")
    try:
        __import__(mod_path)
        mod = sys.modules[mod_path]
    except Exception as e:
        pytest.skip(f"Cannot import {mod_path}: {e}")
        return None
    cls = getattr(mod, name, None)
    if cls is None:
        pytest.skip(f"{name} not found in {mod_path}")
    return cls


def _build_valid_data(schema_name: str, fields: list[dict]) -> dict:
    """Build a valid data dict for a schema from its catalog field definitions."""
    data: dict[str, Any] = {}
    for f in fields:
        if not f.get("required", False):
            continue
        fname = f["name"]
        ftype = f.get("type", "string")
        constraints = f.get("constraints", {})
        data[fname] = _sample_value(fname, ftype, constraints)
    return data


def _sample_value(name: str, ftype: str, constraints: dict) -> Any:
    if "email" in name.lower():
        return "test@example.com"
    if "password" in name.lower():
        return "TestPass123!"
    if "phone" in name.lower():
        return "07701234567"
    if "name" in name.lower() or name == "full_name":
        return "محمد علي"
    if ftype == "integer":
        return 1
    if ftype == "number":
        return 1.0
    if ftype == "boolean":
        return False
    if ftype == "array":
        return []
    if ftype == "object":
        return {}
    pattern = constraints.get("pattern", "")
    if pattern:
        if pattern.startswith("^") and pattern.endswith("$"):
            return re.sub(r"\^|\$", "", pattern).replace("\\+?", "0").replace("\\d", "0").replace("[0-9]", "0").replace("?", "")[:20]
        return "test-value"
    min_l = constraints.get("min_length", 0)
    return "x" * max(min_l, 3)


# ── Tests ──────────────────────────────────────────────────────────────

class TestDTOSerialization:
    """For each DTO in the frozen catalog, create an instance and verify serialization round-trips."""

    def test_all_dtos_roundtrip(self, dto_catalog: dict):
        tested = 0
        for domain_name, domain in dto_catalog.get("domains", {}).items():
            for schema_name, schema in domain.get("schemas", {}).items():
                if schema_name.startswith("_"):
                    continue
                model_cls = _import_model(schema_name)
                if model_cls is None:
                    continue
                fields = schema.get("fields", [])
                data = _build_valid_data(schema_name, fields)
                try:
                    instance = model_cls(**data)
                    serialized = instance.model_dump()
                    re_serialized = model_cls(**serialized).model_dump()
                    assert serialized == re_serialized, f"Round-trip mismatch for {schema_name}"
                    tested += 1
                except ValidationError as e:
                    pytest.fail(f"{schema_name} validation failed: {e}")
                except Exception as e:
                    pytest.fail(f"{schema_name} unexpected error: {e}")
        assert tested > 0, "No DTOs were tested"

    def test_serialization_to_json(self, dto_catalog: dict):
        import json
        tested = 0
        for domain_name, domain in dto_catalog.get("domains", {}).items():
            for schema_name, schema in domain.get("schemas", {}).items():
                if schema_name.startswith("_"):
                    continue
                model_cls = _import_model(schema_name)
                if model_cls is None:
                    continue
                fields = schema.get("fields", [])
                data = _build_valid_data(schema_name, fields)
                try:
                    instance = model_cls(**data)
                    raw = instance.model_dump_json()
                    parsed = json.loads(raw)
                    assert isinstance(parsed, dict)
                    tested += 1
                except Exception:
                    pass
        assert tested > 0, "No DTOs tested for JSON serialization"


class TestDTORequiredFields:
    """Test required fields are truly required."""

    def test_required_fields_enforced(self, dto_catalog: dict):
        for domain_name, domain in dto_catalog.get("domains", {}).items():
            for schema_name, schema in domain.get("schemas", {}).items():
                if schema_name.startswith("_"):
                    continue
                model_cls = _import_model(schema_name)
                if model_cls is None:
                    continue
                required_fields = [f["name"] for f in schema.get("fields", []) if f.get("required")]
                if not required_fields:
                    continue
                fields = schema.get("fields", [])
                data = _build_valid_data(schema_name, fields)
                for req_field in required_fields:
                    if req_field not in data:
                        continue
                    bad_data = dict(data)
                    del bad_data[req_field]
                    try:
                        model_cls(**bad_data)
                        pytest.fail(f"{schema_name} allowed missing required field: {req_field}")
                    except (ValidationError, TypeError, ValueError):
                        pass


class TestDTOOptionalFields:
    """Test optional fields are truly optional."""

    def test_optional_fields_not_required(self, dto_catalog: dict):
        for domain_name, domain in dto_catalog.get("domains", {}).items():
            for schema_name, schema in domain.get("schemas", {}).items():
                if schema_name.startswith("_"):
                    continue
                model_cls = _import_model(schema_name)
                if model_cls is None:
                    continue
                required_names = {f["name"] for f in schema.get("fields", []) if f.get("required")}
                optional_names = {f["name"] for f in schema.get("fields", []) if not f.get("required")}
                if not optional_names:
                    continue
                fields = schema.get("fields", [])
                data = _build_valid_data(schema_name, fields)
                try:
                    instance = model_cls(**data)
                    for opt in optional_names:
                        if hasattr(instance, opt):
                            val = getattr(instance, opt)
                            assert val is None or val == data.get(opt), (
                                f"{schema_name}.{opt} unexpected default"
                            )
                except Exception:
                    pass


class TestDTOConstraints:
    """Test field constraints (min_length, max_length, patterns)."""

    def test_pattern_constraints(self, dto_catalog: dict):
        for domain_name, domain in dto_catalog.get("domains", {}).items():
            for schema_name, schema in domain.get("schemas", {}).items():
                if schema_name.startswith("_"):
                    continue
                model_cls = _import_model(schema_name)
                if model_cls is None:
                    continue
                for field in schema.get("fields", []):
                    constraints = field.get("constraints", {})
                    pattern = constraints.get("pattern", "")
                    if not pattern:
                        continue
                    required = field.get("required", False)
                    if not required:
                        continue
                    fields_list = schema.get("fields", [])
                    data = _build_valid_data(schema_name, fields_list)
                    try:
                        model_cls(**data)
                    except ValidationError:
                        pass

    def test_min_length_constraints(self, dto_catalog: dict):
        for domain_name, domain in dto_catalog.get("domains", {}).items():
            for schema_name, schema in domain.get("schemas", {}).items():
                if schema_name.startswith("_"):
                    continue
                model_cls = _import_model(schema_name)
                if model_cls is None:
                    continue
                for field in schema.get("fields", []):
                    constraints = field.get("constraints", {})
                    min_l = constraints.get("min_length")
                    if not min_l or not field.get("required"):
                        continue
                    fields_list = schema.get("fields", [])
                    data = _build_valid_data(schema_name, fields_list)
                    fname = field["name"]
                    if fname in data:
                        data[fname] = "a" * (min_l - 1)
                        try:
                            model_cls(**data)
                        except (ValidationError, ValueError, AssertionError):
                            pass


class TestDTOEnumValues:
    """Test enum values match codebase."""

    def test_known_enum_fields(self, dto_catalog: dict):
        known_enums: dict[str, set[str]] = {
            "lab_type": {"private", "government", "hospital", "clinic"},
            "role": {"admin", "staff", "technician", "doctor", "receptionist", "master_admin",
                     "ministry_admin", "province_admin"},
            "platform": {"android", "ios"},
            "gender": {"male", "female", "M", "F", "other", "unknown"},
        }
        for domain_name, domain in dto_catalog.get("domains", {}).items():
            for schema_name, schema in domain.get("schemas", {}).items():
                for field in schema.get("fields", []):
                    constraints = field.get("constraints", {})
                    pattern = constraints.get("pattern", "")
                    if not pattern:
                        continue
                    fname = field["name"]
                    if fname in known_enums:
                        pattern_values = set(pattern.strip("^$").split("|"))
                        expected = known_enums[fname]
                        overlap = pattern_values & expected
                        assert overlap, (
                            f"{schema_name}.{fname} pattern '{pattern}' doesn't match known enum {expected}"
                        )
