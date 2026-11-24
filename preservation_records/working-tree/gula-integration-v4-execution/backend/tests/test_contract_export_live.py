"""Wave A evidence: served/exported OpenAPI reflects the live route surface."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.config import APP_VERSION
from tests.conftest import auth_headers


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPORTED_SPEC = REPO_ROOT / "contracts" / "export" / "openapi.json"


def test_contract_spec_and_schema_endpoints_are_live(
    client, make_lab, make_lab_user, monkeypatch
):
    lab = make_lab()
    user = make_lab_user(lab.id, role="admin")
    headers = auth_headers(user.id, lab.id, role="admin")

    response = client.get("/contracts/openapi.json", headers=headers)
    assert response.status_code == 200, response.text
    spec = response.json()
    assert spec["info"]["version"] == APP_VERSION
    assert len(spec["paths"]) >= 500
    for path in (
        "/health",
        "/document-management/",
        "/encounter-management/",
        "/provider-management/",
        "/healthcare-consent/",
    ):
        assert path in spec["paths"], path

    schema = client.get("/contracts/schemas/patient", headers=headers)
    assert schema.status_code == 200, schema.text
    patient_schema = schema.json()
    assert patient_schema["type"] == "object"
    assert patient_schema["properties"], "Patient schema has no properties"

    catalog = client.get("/contracts/catalog", headers=headers)
    assert catalog.status_code == 200
    assert catalog.json()["app_version"] == APP_VERSION

    # The Prometheus scrape route is deliberately hidden from OpenAPI, but it
    # must still be reachable and enforce the configured bearer token.
    monkeypatch.setenv("METRICS_BEARER_TOKEN", "wave-a-scrape-token")
    assert client.get("/metrics/prom").status_code == 401
    scraped = client.get(
        "/metrics/prom",
        headers={"Authorization": "Bearer wave-a-scrape-token"},
    )
    assert scraped.status_code == 200, scraped.text
    assert "gula_up 1" in scraped.text


def test_checked_in_openapi_export_matches_app_version_and_route_surface():
    from app.main import app as production_app

    spec = json.loads(EXPORTED_SPEC.read_text(encoding="utf-8"))
    assert spec["info"]["version"] == APP_VERSION
    assert len(spec["paths"]) >= 500
    assert "/document-management/" in spec["paths"]
    assert "/health" in spec["paths"]

    # C01/C15 drift guard: the checked-in contract must describe exactly the
    # route surface served by the production application factory, not merely a
    # minimum path count. app.main.app is the WSGI/ASGI entrypoint used in
    # deployment; create_app(test) intentionally omits a few probe routes.
    assert spec["paths"] == production_app.openapi()["paths"]


_STUB_MARKER = re.compile(
    r"\b(stub|simulation[- ]only|mock response|demo[- ]only|not implemented|placeholder)\b",
    re.IGNORECASE,
)
_AFFIRMATIVE_STUB_CLAIM = re.compile(
    r"(?:returns?|emits?|serves?|responds?\s+with|provides?|is\s+a)\s+"
    r"(?:a\s+|an\s+)?"
    r"(?:stub|mock|placeholder|demo[- ]only|simulation[- ]only|not implemented)\b",
    re.IGNORECASE,
)


def _string_values(value):
    """Yield every literal string nested in a JSON-like OpenAPI fragment."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _string_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _string_values(item)


def test_exported_operations_do_not_silently_advertise_stub_responses():
    """C01/C15: no operation may claim a STUB response in its wire contract.

    Negations in documentation are allowed: for example, the standards endpoint
    explicitly says that it emits no placeholder data. The guard rejects
    affirmative claims in summaries/descriptions and any marker in response
    descriptions, examples, or schema constants/enums.
    """
    spec = json.loads(EXPORTED_SPEC.read_text(encoding="utf-8"))
    violations: list[str] = []

    for path, item in spec["paths"].items():
        for method, operation in item.items():
            if not isinstance(operation, dict):
                continue
            location = f"{method.upper()} {path}"
            for field in ("summary", "description"):
                text = operation.get(field) or ""
                if _AFFIRMATIVE_STUB_CLAIM.search(text):
                    violations.append(f"{location}: {field}")

            for status, response in operation.get("responses", {}).items():
                if not isinstance(response, dict):
                    continue
                description = response.get("description") or ""
                if _STUB_MARKER.search(description) and description != "Successful Response":
                    violations.append(f"{location}: response {status} description")
                for text in _string_values(response.get("content", {})):
                    if _STUB_MARKER.search(text):
                        violations.append(f"{location}: response {status} content")

    assert not violations, "silent STUB markers in exported contract: " + ", ".join(violations)
