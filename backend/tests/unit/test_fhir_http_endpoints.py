"""Focused HTTP evidence for the local T6 FHIR R4 router.

The router under test is deliberately NOT registered on the application
factory. Every test mounts it explicitly with ``FastAPI()`` +
``app.include_router(router)`` and drives it with ``TestClient``. All data is
synthetic; no external endpoint or authority is contacted.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from app.health_core.fhir.errors import FHIR_R4_ISSUE_TYPES
from app.interoperability.fhir_http import reset_repository, router
from app.interoperability.fhir_http.capability import SUPPORTED_INTERACTIONS
from app.interoperability.fhir_http.repository import (
    FACILITY_A,
    FACILITY_B,
    TENANT_A,
    TENANT_B,
    get_repository,
)
from app.interoperability.fhir_http.versioning import etag_for, normalise_etag, version_from_meta
from fastapi import FastAPI
from fastapi.testclient import TestClient

_BACKEND_DIR = Path(__file__).resolve().parents[2]

_PRINCIPAL = "SYN-USR-0001"
_ALL_SCOPES = "fhir.read,fhir.write"


@pytest.fixture(autouse=True)
def _reset_shared_repository() -> None:
    """Each test starts and ends with the deterministic synthetic seed."""
    reset_repository()
    yield
    reset_repository()


@pytest.fixture()
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(router)
    return application


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=True)


def _headers(
    *,
    scopes: str = "fhir.read",
    tenant: str = TENANT_A,
    facility: str = FACILITY_A,
    principal: str = _PRINCIPAL,
) -> dict[str, str]:
    return {
        "X-GULA-Principal": principal,
        "X-GULA-Scopes": scopes,
        "X-GULA-Tenant": tenant,
        "X-GULA-Facility": facility,
    }


def _read_headers(**kwargs: Any) -> dict[str, str]:
    return _headers(scopes="fhir.read", **kwargs)


def _write_headers(**kwargs: Any) -> dict[str, str]:
    return _headers(scopes=_ALL_SCOPES, **kwargs)


def _observation_payload(
    observation_id: str = "SYN-OBS-0100",
    value: float = 99.0,
    *,
    tenant: str = TENANT_A,
    facility: str = FACILITY_A,
) -> dict[str, object]:
    """Derive a valid synthetic Observation from the canonical serializer output."""
    base = get_repository().current("Observation", "SYN-OBS-0002")
    assert base is not None
    payload = deepcopy(base.resource)
    payload["id"] = observation_id
    identifiers = payload["identifier"]
    assert isinstance(identifiers, list)
    assert isinstance(identifiers[0], dict)
    identifiers[0]["value"] = observation_id
    meta = payload["meta"]
    assert isinstance(meta, dict)
    meta["versionId"] = "1"
    quantity = payload["valueQuantity"]
    assert isinstance(quantity, dict)
    quantity["value"] = value
    extensions = payload["extension"]
    assert isinstance(extensions, list)
    for extension in extensions:
        assert isinstance(extension, dict)
        if extension.get("url", "").endswith("/tenant"):
            extension["valueCode"] = tenant
        if extension.get("url", "").endswith("/facility"):
            extension["valueCode"] = facility
    return payload


def _assert_operation_outcome(
    response: Any,
    status_code: int,
    *,
    issue_code: str | None = None,
) -> dict[str, object]:
    """Assert a bare, structured, stack-trace-free FHIR OperationOutcome."""
    assert response.status_code == status_code
    assert response.headers["content-type"].startswith("application/fhir+json")
    body = response.json()
    assert isinstance(body, dict)
    assert body["resourceType"] == "OperationOutcome"
    issues = body["issue"]
    assert isinstance(issues, list)
    assert issues
    for issue in issues:
        assert isinstance(issue, dict)
        assert set(issue) >= {"severity", "code", "diagnostics"}
        assert issue["severity"] in {"fatal", "error"}
        assert issue["code"] in FHIR_R4_ISSUE_TYPES
        assert isinstance(issue["diagnostics"], str)
        assert issue["diagnostics"]
    if issue_code is not None:
        assert issues[0]["code"] == issue_code
    serialised = json.dumps(body)
    assert "Traceback" not in serialised
    assert 'File "' not in serialised
    return body


# ---------------------------------------------------------------------------
# CapabilityStatement
# ---------------------------------------------------------------------------


def test_capability_statement_declares_r4_conformance(client: TestClient) -> None:
    response = client.get("/fhir/metadata", headers=_read_headers())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/fhir+json")
    capability = response.json()
    assert capability["resourceType"] == "CapabilityStatement"
    assert capability["fhirVersion"] == "4.0.1"
    assert capability["status"] == "active"
    assert "json" in capability["format"]
    assert "application/fhir+json" in capability["format"]

    rest = capability["rest"]
    assert len(rest) == 1
    assert rest[0]["mode"] == "server"
    declared = {item["type"]: {op["code"] for op in item["interaction"]} for item in rest[0]["resource"]}
    assert set(declared) == set(SUPPORTED_INTERACTIONS)
    for resource_type, interactions in SUPPORTED_INTERACTIONS.items():
        assert set(interactions) == declared[resource_type]
    assert {"read", "vread", "search-type", "create"} <= declared["Observation"]
    assert {"read", "vread", "search-type"} <= declared["Patient"]


# ---------------------------------------------------------------------------
# read / vread
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("path", "resource_type"),
    [
        ("/fhir/Patient/SYN-PAT-0001", "Patient"),
        ("/fhir/Observation/SYN-OBS-0002", "Observation"),
    ],
)
def test_read_resource_success(client: TestClient, path: str, resource_type: str) -> None:
    response = client.get(path, headers=_read_headers())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/fhir+json")
    body = response.json()
    assert body["resourceType"] == resource_type
    assert body["id"].startswith("SYN-")
    assert body["meta"]["versionId"].isdigit()
    assert int(body["meta"]["versionId"]) >= 1


@pytest.mark.parametrize(
    ("path", "issue_code"),
    [
        ("/fhir/Patient/SYN-PAT-DOES-NOT-EXIST", "not-found"),
        ("/fhir/Observation/SYN-OBS-DOES-NOT-EXIST", "not-found"),
    ],
)
def test_read_missing_resource_is_structured_404(
    client: TestClient, path: str, issue_code: str
) -> None:
    _assert_operation_outcome(client.get(path, headers=_read_headers()), 404, issue_code=issue_code)


def test_vread_patient_returns_the_exact_historical_version(client: TestClient) -> None:
    first = client.get("/fhir/Patient/SYN-PAT-0001/_history/1", headers=_read_headers())
    second = client.get("/fhir/Patient/SYN-PAT-0001/_history/2", headers=_read_headers())
    current = client.get("/fhir/Patient/SYN-PAT-0001", headers=_read_headers())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["meta"]["versionId"] == "1"
    assert second.json()["meta"]["versionId"] == "2"
    assert first.json()["active"] is True
    assert second.json()["active"] is False
    assert current.json() == second.json()


def test_vread_observation_returns_the_exact_historical_version(client: TestClient) -> None:
    first = client.get("/fhir/Observation/SYN-OBS-0001/_history/1", headers=_read_headers())
    second = client.get("/fhir/Observation/SYN-OBS-0001/_history/2", headers=_read_headers())

    assert first.status_code == 200
    assert second.status_code == 200
    first_value = first.json()["valueQuantity"]["value"]
    second_value = second.json()["valueQuantity"]["value"]
    assert first_value != second_value
    assert first.json()["meta"]["versionId"] == "1"
    assert second.json()["meta"]["versionId"] == "2"


def test_vread_missing_version_is_structured_404(client: TestClient) -> None:
    response = client.get("/fhir/Patient/SYN-PAT-0001/_history/99", headers=_read_headers())
    _assert_operation_outcome(response, 404, issue_code="not-found")


def test_vread_invalid_version_is_structured_400(client: TestClient) -> None:
    response = client.get("/fhir/Patient/SYN-PAT-0001/_history/not-a-number", headers=_read_headers())
    _assert_operation_outcome(response, 400, issue_code="invalid")


# ---------------------------------------------------------------------------
# create / update
# ---------------------------------------------------------------------------


def test_create_observation_returns_201_location_etag_and_stores_resource(client: TestClient) -> None:
    payload = _observation_payload()

    response = client.post("/fhir/Observation", headers=_write_headers(), json=payload)

    assert response.status_code == 201
    assert response.headers["content-type"].startswith("application/fhir+json")
    assert response.headers["location"] == "/fhir/Observation/SYN-OBS-0100/_history/1"
    assert response.headers["etag"] == etag_for(response.json())
    body = response.json()
    assert body["resourceType"] == "Observation"
    assert body["id"] == "SYN-OBS-0100"
    assert body["meta"]["versionId"] == "1"

    read_back = client.get("/fhir/Observation/SYN-OBS-0100", headers=_read_headers())
    assert read_back.status_code == 200
    assert read_back.json() == body


def test_create_observation_increments_version_for_existing_id(client: TestClient) -> None:
    payload = _observation_payload("SYN-OBS-0101", 11.0)

    first = client.post("/fhir/Observation", headers=_write_headers(), json=payload)
    second = client.post("/fhir/Observation", headers=_write_headers(), json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["meta"]["versionId"] == "1"
    assert second.json()["meta"]["versionId"] == "2"
    assert first.headers["etag"] != second.headers["etag"]


def test_create_observation_rejects_wrong_resource_type(client: TestClient) -> None:
    payload = _observation_payload()
    payload["resourceType"] = "Patient"

    response = client.post("/fhir/Observation", headers=_write_headers(), json=payload)

    body = _assert_operation_outcome(response, 400, issue_code="invalid")
    assert "resourceType" in body["issue"][0]["diagnostics"]


@pytest.mark.parametrize(
    "missing_field",
    ["identifier", "status", "code", "subject", "valueQuantity", "effectiveDateTime"],
)
def test_create_observation_rejects_missing_required_fields(
    client: TestClient, missing_field: str
) -> None:
    payload = _observation_payload()
    del payload[missing_field]

    response = client.post("/fhir/Observation", headers=_write_headers(), json=payload)

    _assert_operation_outcome(response, 400, issue_code="invalid")


def test_create_observation_rejects_national_identifier_without_echoing_it(
    client: TestClient,
) -> None:
    secret_nid = "NID-9876543210987"
    payload = _observation_payload()
    identifiers = payload["identifier"]
    assert isinstance(identifiers, list)
    identifiers.append({"system": "urn:gula:synthetic:fhir:R4:identifier", "value": secret_nid})

    response = client.post("/fhir/Observation", headers=_write_headers(), json=payload)

    body = _assert_operation_outcome(response, 400, issue_code="invalid")
    assert secret_nid not in json.dumps(body)
    assert secret_nid not in response.text


def test_create_observation_rejects_contained_identifier_without_echoing_it(
    client: TestClient,
) -> None:
    secret_token = "BEARER-SUPERSECRET-TOKEN-ABC"
    payload = _observation_payload()
    payload["contained"] = [{"resourceType": "Patient", "id": secret_token}]

    response = client.post("/fhir/Observation", headers=_write_headers(), json=payload)

    body = _assert_operation_outcome(response, 400, issue_code="invalid")
    assert secret_token not in json.dumps(body)
    assert secret_token not in response.text


def test_create_observation_rejects_unsupported_extension(client: TestClient) -> None:
    payload = _observation_payload()
    extensions = payload["extension"]
    assert isinstance(extensions, list)
    extensions.append({"url": "urn:attacker:identifier-leak", "valueString": "SHOULD-NOT-LEAK"})

    response = client.post("/fhir/Observation", headers=_write_headers(), json=payload)

    body = _assert_operation_outcome(response, 400, issue_code="invalid")
    assert "SHOULD-NOT-LEAK" not in json.dumps(body)


def test_update_observation_succeeds_with_matching_etag(client: TestClient) -> None:
    original = client.get("/fhir/Observation/SYN-OBS-0002", headers=_read_headers())
    assert original.status_code == 200
    original_etag = etag_for(original.json())
    payload = deepcopy(original.json())
    quantity = payload["valueQuantity"]
    assert isinstance(quantity, dict)
    quantity["value"] = 123.0

    response = client.put(
        "/fhir/Observation/SYN-OBS-0002",
        headers={**_write_headers(), "If-Match": original_etag},
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["meta"]["versionId"] == "2"
    assert response.json()["valueQuantity"]["value"] == 123.0
    assert response.headers["etag"] == etag_for(response.json())
    assert response.headers["etag"] != original_etag
    assert response.headers["location"] == "/fhir/Observation/SYN-OBS-0002/_history/2"

    historical = client.get("/fhir/Observation/SYN-OBS-0002/_history/1", headers=_read_headers())
    assert historical.status_code == 200
    assert historical.json() == original.json()


def test_update_observation_without_if_match_is_structured_428(client: TestClient) -> None:
    payload = _observation_payload("SYN-OBS-0002")

    response = client.put("/fhir/Observation/SYN-OBS-0002", headers=_write_headers(), json=payload)

    _assert_operation_outcome(response, 428, issue_code="invariant")


def test_update_observation_with_stale_etag_is_structured_409(client: TestClient) -> None:
    payload = _observation_payload("SYN-OBS-0002")

    response = client.put(
        "/fhir/Observation/SYN-OBS-0002",
        headers={**_write_headers(), "If-Match": '"deadbeef"'},
        json=payload,
    )

    _assert_operation_outcome(response, 409, issue_code="invariant")


def test_update_observation_accepts_weak_etag_prefix(client: TestClient) -> None:
    original = client.get("/fhir/Observation/SYN-OBS-0002", headers=_read_headers())
    weak = "W/" + etag_for(original.json())

    response = client.put(
        "/fhir/Observation/SYN-OBS-0002",
        headers={**_write_headers(), "If-Match": weak},
        json=original.json(),
    )

    assert response.status_code == 200
    assert normalise_etag(weak) == normalise_etag(etag_for(original.json()))


def test_update_missing_observation_is_structured_404(client: TestClient) -> None:
    response = client.put(
        "/fhir/Observation/SYN-OBS-MISSING",
        headers={**_write_headers(), "If-Match": "*"},
        json=_observation_payload("SYN-OBS-MISSING"),
    )
    _assert_operation_outcome(response, 404, issue_code="not-found")


def test_update_observation_id_mismatch_is_structured_400(client: TestClient) -> None:
    response = client.put(
        "/fhir/Observation/SYN-OBS-0002",
        headers={**_write_headers(), "If-Match": "*"},
        json=_observation_payload("SYN-OBS-9999"),
    )
    _assert_operation_outcome(response, 400, issue_code="invalid")


# ---------------------------------------------------------------------------
# search bundles
# ---------------------------------------------------------------------------


def test_search_patients_by_identifier_returns_bundle(client: TestClient) -> None:
    response = client.get(
        "/fhir/Patient", headers=_read_headers(), params={"identifier": "SYN-PAT-0003"}
    )

    assert response.status_code == 200
    bundle = response.json()
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "searchset"
    assert bundle["total"] == 1
    assert len(bundle["entry"]) == 1
    assert bundle["entry"][0]["resource"]["id"] == "SYN-PAT-0003"
    assert bundle["entry"][0]["fullUrl"].startswith("/fhir/Patient/")


def test_search_patients_by_name_returns_bundle(client: TestClient) -> None:
    response = client.get("/fhir/Patient", headers=_read_headers(), params={"name": "patient 4"})

    assert response.status_code == 200
    bundle = response.json()
    assert bundle["type"] == "searchset"
    assert bundle["total"] == 1
    assert bundle["entry"][0]["resource"]["id"] == "SYN-PAT-0004"


def test_search_patients_count_cap_limits_entries_not_total(client: TestClient) -> None:
    response = client.get("/fhir/Patient", headers=_read_headers(), params={"_count": "2"})

    assert response.status_code == 200
    bundle = response.json()
    assert bundle["total"] == 5
    assert len(bundle["entry"]) == 2
    assert {entry["resource"]["id"] for entry in bundle["entry"]} <= {
        f"SYN-PAT-000{index}" for index in range(1, 6)
    }


def test_search_patients_invalid_count_is_structured_400(client: TestClient) -> None:
    for bad_count in ("0", "101", "not-a-number"):
        response = client.get("/fhir/Patient", headers=_read_headers(), params={"_count": bad_count})
        body = _assert_operation_outcome(response, 400, issue_code="invalid")
        assert bad_count not in json.dumps(body)


def test_search_observations_returns_bundle(client: TestClient) -> None:
    response = client.get(
        "/fhir/Observation", headers=_read_headers(), params={"identifier": "SYN-OBS-0001"}
    )

    assert response.status_code == 200
    bundle = response.json()
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "searchset"
    assert bundle["total"] == 1
    assert bundle["entry"][0]["resource"]["id"] == "SYN-OBS-0001"
    assert bundle["entry"][0]["resource"]["meta"]["versionId"] == "2"


# ---------------------------------------------------------------------------
# authorization (fail closed)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/fhir/metadata"),
        ("get", "/fhir/Patient"),
        ("get", "/fhir/Patient/SYN-PAT-0001"),
        ("get", "/fhir/Observation/SYN-OBS-0001"),
        ("post", "/fhir/Observation"),
        ("put", "/fhir/Observation/SYN-OBS-0001"),
    ],
)
def test_no_principal_is_denied_401(client: TestClient, method: str, path: str) -> None:
    if method == "post":
        response = client.post(path, headers={}, json={})
    elif method == "put":
        response = client.put(path, headers={}, json={})
    else:
        response = client.get(path, headers={})
    _assert_operation_outcome(response, 401, issue_code="login")


def test_wrong_scope_on_read_is_denied_403(client: TestClient) -> None:
    response = client.get("/fhir/Patient/SYN-PAT-0001", headers=_headers(scopes="fhir.write"))
    _assert_operation_outcome(response, 403, issue_code="denied")


def test_wrong_scope_on_write_is_denied_403(client: TestClient) -> None:
    response = client.post("/fhir/Observation", headers=_headers(scopes="fhir.read"), json={})
    _assert_operation_outcome(response, 403, issue_code="denied")


@pytest.mark.parametrize(
    ("tenant", "facility"),
    [("", FACILITY_A), (TENANT_A, ""), ("", "")],
)
def test_missing_tenant_or_facility_claim_is_denied_403(
    client: TestClient, tenant: str, facility: str
) -> None:
    response = client.get(
        "/fhir/Patient/SYN-PAT-0001", headers=_read_headers(tenant=tenant, facility=facility)
    )
    _assert_operation_outcome(response, 403, issue_code="denied")


def test_malformed_claims_are_denied_without_echo(client: TestClient) -> None:
    secret = "REAL-NID-123456789"
    response = client.get(
        "/fhir/Patient/SYN-PAT-0001",
        headers=_read_headers(tenant=secret, facility=secret),
    )
    body = _assert_operation_outcome(response, 403, issue_code="denied")
    assert secret not in json.dumps(body)


def test_cross_tenant_read_is_denied_403(client: TestClient) -> None:
    response = client.get(
        "/fhir/Patient/SYN-PAT-0001",
        headers=_read_headers(tenant=TENANT_B, facility=FACILITY_B),
    )
    _assert_operation_outcome(response, 403, issue_code="denied")


def test_cross_facility_read_is_denied_403(client: TestClient) -> None:
    response = client.get(
        "/fhir/Observation/SYN-OBS-0002",
        headers=_read_headers(tenant=TENANT_A, facility=FACILITY_B),
    )
    _assert_operation_outcome(response, 403, issue_code="denied")


def test_cross_tenant_write_is_denied_403(client: TestClient) -> None:
    payload = _observation_payload("SYN-OBS-0200", tenant=TENANT_B, facility=FACILITY_B)

    response = client.post("/fhir/Observation", headers=_write_headers(), json=payload)

    _assert_operation_outcome(response, 403, issue_code="denied")


def test_cross_tenant_update_of_existing_resource_is_denied_403(client: TestClient) -> None:
    response = client.put(
        "/fhir/Observation/SYN-OBS-0003",
        headers={**_write_headers(), "If-Match": "*"},
        json=_observation_payload("SYN-OBS-0003"),
    )
    _assert_operation_outcome(response, 403, issue_code="denied")


def test_search_hides_resources_from_other_tenants(client: TestClient) -> None:
    own = client.get("/fhir/Patient", headers=_read_headers())
    other = client.get(
        "/fhir/Patient", headers=_read_headers(tenant=TENANT_B, facility=FACILITY_B)
    )

    assert own.status_code == 200
    assert other.status_code == 200
    own_ids = {item["resource"]["id"] for item in own.json()["entry"]}
    other_ids = {item["resource"]["id"] for item in other.json()["entry"]}
    assert "SYN-PAT-0006" not in own_ids
    assert own_ids.isdisjoint(other_ids)
    assert other_ids == {"SYN-PAT-0006"}


# ---------------------------------------------------------------------------
# ETag determinism and activation boundary
# ---------------------------------------------------------------------------


def test_etag_is_deterministic_and_version_sensitive(client: TestClient) -> None:
    resource = get_repository().current("Observation", "SYN-OBS-0001")
    assert resource is not None
    assert etag_for(resource.resource) == etag_for(resource.resource)
    assert version_from_meta(resource.resource) == 2
    assert normalise_etag("W/" + etag_for(resource.resource)) == etag_for(resource.resource)

    response = client.get("/fhir/Observation/SYN-OBS-0001", headers=_read_headers())
    assert response.headers["etag"] == etag_for(response.json())

    first = get_repository().version("Observation", "SYN-OBS-0001", 1)
    second = get_repository().version("Observation", "SYN-OBS-0001", 2)
    assert first is not None and second is not None
    assert etag_for(first.resource) != etag_for(second.resource)


def test_router_is_not_registered_in_factory_or_main() -> None:
    for relative_path in ("app/factory.py", "app/main.py"):
        path = _BACKEND_DIR / relative_path
        if path.exists():
            assert "fhir_http" not in path.read_text(encoding="utf-8")
