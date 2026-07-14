from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

_BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
_REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
_SRC_DIR = os.path.join(_BACKEND_DIR, "app")
sys.path.insert(0, _BACKEND_DIR)
sys.path.insert(0, _REPO_ROOT)

os.environ["RUNTIME_MODE"] = "test"
os.environ["FEATURE_BACKGROUND_TASKS"] = "false"
os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-" + "x" * 40
os.environ["ENCRYPTION_KEY"] = "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw="
os.environ["NID_HMAC_KEY"] = "a" * 64
os.environ["REDIS_URL"] = ""

_CONTRACTS_DIR = Path(os.path.dirname(__file__)).parent


@pytest.fixture(scope="session")
def contracts_dir() -> Path:
    return _CONTRACTS_DIR


@pytest.fixture(scope="session")
def dto_catalog() -> dict:
    path = _CONTRACTS_DIR / "dto" / "catalog.json"
    return json.loads(path.read_text())


@pytest.fixture(scope="session")
def api_catalog() -> dict:
    path = _CONTRACTS_DIR / "api" / "v1" / "catalog.json"
    return json.loads(path.read_text())


@pytest.fixture(scope="session")
def events_catalog() -> dict:
    path = _CONTRACTS_DIR / "events" / "catalog.json"
    return json.loads(path.read_text())


@pytest.fixture(scope="session")
def fhir_profiles() -> list[dict]:
    path = _CONTRACTS_DIR / "fhir" / "profiles.json"
    return json.loads(path.read_text())


@pytest.fixture(scope="session")
def platform_version() -> str:
    path = _BACKEND_DIR / "app" / "config.py"
    for line in path.read_text().splitlines():
        if "APP_VERSION" in line and "=" in line and not line.strip().startswith("#"):
            return line.split('"')[1] if '"' in line else line.split("'")[1]
    return "unknown"


@pytest.fixture()
def app():
    os.environ["RUNTIME_MODE"] = "test"
    os.environ["ENV"] = "test"
    from app.main import app as _app
    return _app


@pytest.fixture()
def client(app) -> TestClient:
    return TestClient(app)


@pytest.fixture()
def auth_token() -> str:
    from app.security.auth import create_token
    return create_token(user_id=1, lab_id=1, role="lab_admin")


@pytest.fixture()
def auth_headers(auth_token: str) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture()
def sample_patient_data() -> dict:
    return {
        "full_name": "محمد علي",
        "phone": "07701234567",
        "birth_date": "1990-01-15",
        "gender": "M",
        "email": "mohammed@example.com",
    }


@pytest.fixture()
def sample_order_data() -> dict:
    return {
        "patient_id": 1,
        "doctor_name": "د. أحمد",
        "results": [
            {
                "test_name": "Hemoglobin",
                "value": 13.5,
                "unit": "g/dL",
                "normal_range_low": 12.0,
                "normal_range_high": 16.0,
            }
        ],
    }


@pytest.fixture()
def sample_result_data() -> dict:
    return {
        "health_id": "HN-12345",
        "test_name": "Glucose",
        "value": 95.0,
        "unit": "mg/dL",
    }


@pytest.fixture()
def report_path() -> Path:
    return Path(os.path.dirname(__file__)) / "report.json"


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))
