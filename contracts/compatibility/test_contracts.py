from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import BaseModel

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


# ── Helper ─────────────────────────────────────────────────────────────

def _discover_backend_models() -> dict[str, type[BaseModel]]:
    """Scan backend route and service modules for pydantic BaseModel subclasses."""
    models: dict[str, type[BaseModel]] = {}
    scan_dirs = [
        Path(_BACKEND_DIR) / "app" / "routes",
        Path(_BACKEND_DIR) / "app" / "services",
        Path(_BACKEND_DIR) / "app" / "lims",
    ]
    for scan_dir in scan_dirs:
        if not scan_dir.is_dir():
            continue
        for fpath in sorted(scan_dir.glob("*.py")):
            mod_name = f"app.{fpath.relative_to(Path(_BACKEND_DIR) / 'app').with_suffix('').as_posix().replace('/', '.')}"
            try:
                __import__(mod_name)
                mod = sys.modules[mod_name]
                for name in dir(mod):
                    obj = getattr(mod, name)
                    if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel:
                        models[f"{mod_name}.{name}"] = obj
            except Exception:
                pass
    return models


def _get_backend_routes() -> list[dict]:
    """Return (method, path) dicts from the FastAPI app.

    IA-069: this was a second, independent copy of the flat
    ``hasattr(route, "path")`` walk, which sees 11 of this app's routes and
    reports the rest as unregistered. It now delegates to the single corrected
    census in ``test_contract_api``, which resolves FastAPI's lazy
    ``_IncludedRouter`` wrappers -- one walker, not two that can drift apart.
    """
    from test_contract_api import _get_registered_routes

    return [
        {"method": method, "path": path, "name": path}
        for path, methods in _get_registered_routes().items()
        for method in sorted(methods)
    ]


# ── Tests ──────────────────────────────────────────────────────────────

class TestModelMatching:
    """Verify Pydantic models exist for every schema in the DTO catalog."""

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "IA-069: 19 DTO schemas in contracts/dto have no backend model -- "
            "orders_results/TestResult*, all 9 mpi/*, all 5 governance/*, all 3 "
            "tasks/*. This is the DTO projection of the same catalog drift "
            "recorded in KNOWN_CATALOG_GAP.json: the /mpi/* endpoints these DTOs "
            "describe are themselves among the 254 unregistered catalog paths. "
            "strict=True so that closing the gap fails this xfail and forces the "
            "ledger and this marker to be updated together."
        ),
    )
    def test_all_dto_schemas_have_backend_models(self, dto_catalog: dict):
        models = _discover_backend_models()
        model_names = {k.split(".")[-1] for k in models}
        missing = []
        for domain_name, domain in dto_catalog.get("domains", {}).items():
            for schema_name in domain.get("schemas", {}):
                if schema_name.startswith("_"):
                    continue
                if schema_name not in model_names:
                    missing.append(f"{domain_name}/{schema_name}")
        assert not missing, f"DTO schemas missing backend models: {missing}"

    def test_dto_catalog_version_present(self, dto_catalog: dict):
        assert "dto_version" in dto_catalog, "dto catalog missing version field"
        assert dto_catalog["dto_version"] == "1.0"


class TestAPIContract:
    """Verify all API catalog endpoints are registered in the backend."""

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "IA-069: the (method, path) projection of the catalog gap recorded in "
            "KNOWN_CATALOG_GAP.json -- 254 of the catalog's 313 paths are not "
            "registered, verified by a 16-path random sample all absent from the "
            "resolved route census. The ratcheted assertion lives in "
            "test_contract_api.py::test_catalog_gap_matches_the_recorded_ledger; "
            "this one is left failing-by-record rather than duplicated. "
            "strict=True so it cannot start passing unnoticed."
        ),
    )
    def test_all_catalog_endpoints_registered(self, api_catalog: dict):
        routes = _get_backend_routes()
        route_set = {(r["method"], r["path"]) for r in routes}
        catalog = api_catalog.get("catalog", {})
        missing = []
        for group_name, group in catalog.items():
            for path, methods in group.items():
                for method in methods:
                    catalog_entry = (method.upper(), path)
                    found = False
                    for r_method, r_path in route_set:
                        if r_method == catalog_entry[0] and self._path_matches(r_path, catalog_entry[1]):
                            found = True
                            break
                    if not found:
                        missing.append(f"{method} {path}")
        assert not missing, f"Catalog endpoints not found in backend: {missing}"

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "IA-069: contracts/api/v1/catalog.json declares platform_version "
            "2.1.0; config.py is at 2.5.0. The catalog is stale by four minor "
            "versions, which corroborates the 254-path gap -- it describes the "
            "2.1.0 surface. Deliberately NOT fixed by editing the version string: "
            "relabelling it 2.5.0 would assert the catalog is current while 81% "
            "of its paths do not exist, which is a worse lie than the mismatch. "
            "It is fixed by regenerating the catalog, which is a contract change."
        ),
    )
    def test_platform_version_matches(self, api_catalog: dict, platform_version: str):
        catalog_version = api_catalog.get("platform_version", "")
        assert catalog_version == platform_version, (
            f"Platform version mismatch: catalog={catalog_version}, backend={platform_version}"
        )

    def test_health_endpoints_reachable(self, client):
        """Reachable, not necessarily ready. See IA-069.

        ``/health/ready`` answers 503 until ``startup_guard`` sets
        ``system_ready``, which it cannot do in a test app with no migrated
        database. That 503 is the designed behaviour, so asserting 200 made
        this test a readiness check on a stack that was never started.
        """
        for path in ("/health", "/health/live"):
            resp = client.get(path)
            assert resp.status_code == 200, f"{path} returned {resp.status_code}"

        resp = client.get("/health/ready")
        assert resp.status_code != 404, "/health/ready is not registered"
        assert resp.status_code not in (401, 403), (
            f"/health/ready demanded a credential ({resp.status_code})"
        )

    def test_auth_required_endpoints_reject_unauthorized(self, client, api_catalog: dict):
        catalog = api_catalog.get("catalog", {})
        tested = 0
        for group_name, group in catalog.items():
            for path, methods in group.items():
                for method, details in methods.items():
                    if details.get("auth", {}).get("auth_required", False):
                        fn = getattr(client, method.lower(), None)
                        if fn:
                            resp = fn(path)
                            assert resp.status_code in (401, 403, 503), (
                                f"{method} {path} should reject unauth, got {resp.status_code}"
                            )
                            tested += 1
                            if tested >= 5:
                                return
        assert tested > 0, "No auth-required endpoints tested"

    @staticmethod
    def _path_matches(route_path: str, catalog_path: str) -> bool:
        """Compare a FastAPI route path (with {param}) to a catalog path (with {param})."""
        r_parts = route_path.strip("/").split("/")
        c_parts = catalog_path.strip("/").split("/")
        if len(r_parts) != len(c_parts):
            return False
        for rp, cp in zip(r_parts, c_parts):
            if rp.startswith("{") and rp.endswith("}"):
                if not (cp.startswith("{") and cp.endswith("}")):
                    return False
            elif rp != cp:
                return False
        return True


class TestFHIRContract:
    """Verify FHIR profiles are buildable."""

    def test_all_fhir_profiles_have_base_resource(self, fhir_profiles: list[dict]):
        for profile in fhir_profiles:
            assert "baseResource" in profile, f"Profile {profile.get('name')} missing baseResource"
            assert profile["baseResource"] in (
                "Patient", "Practitioner", "Organization", "Encounter",
                "Observation", "DiagnosticReport", "Specimen", "ServiceRequest",
                "Device", "Bundle",
            ), f"Unknown baseResource: {profile.get('baseResource')}"

    def test_all_fhir_profiles_have_required_fields(self, fhir_profiles: list[dict]):
        for profile in fhir_profiles:
            if profile.get("requiredFields"):
                req = profile["requiredFields"]
                assert "resourceType" in req, f"Profile {profile.get('name')} must require resourceType"
                assert "id" in req, f"Profile {profile.get('name')} must require id"

    def test_fhir_profiles_have_mapping_source(self, fhir_profiles: list[dict]):
        for profile in fhir_profiles:
            assert "mappingSource" in profile or "mappingSourceAlternative" in profile, (
                f"Profile {profile.get('name')} missing mapping source"
            )


class TestEventsContract:
    """Verify events catalog is valid and serializable."""

    def test_events_catalog_has_metadata(self, events_catalog: dict):
        meta = events_catalog.get("catalog_metadata", {})
        assert "version" in meta
        assert "outbox_config" in meta

    def test_events_have_schemas(self, events_catalog: dict):
        for domain_name, domain in events_catalog.get("domains", {}).items():
            for event_name, event in domain.get("events", {}).items():
                assert "schema" in event, f"Event {event_name} missing schema"
                assert "retry_policy" in event, f"Event {event_name} missing retry_policy"
                assert event.get("version"), f"Event {event_name} missing version"

    def test_events_serializable(self, events_catalog: dict):
        serialized = json.dumps(events_catalog)
        assert len(serialized) > 0
        roundtrip = json.loads(serialized)
        assert roundtrip["catalog_metadata"]["version"] == events_catalog["catalog_metadata"]["version"]


class TestReportGeneration:
    """Generate the compatibility report artifact."""

    @pytest.fixture()
    def report(self, request, api_catalog: dict, platform_version: str, report_path: Path):
        from conftest import load_json
        results = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "platform_version": platform_version,
                "contracts_version": api_catalog.get("api_version", "unknown"),
            },
            "results": [],
            "summary": {"total": 0, "passed": 0, "failed": 0},
        }
        yield results
        report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "IA-069: the same 2.1.0-vs-2.5.0 catalog drift as "
            "TestAPIContract::test_platform_version_matches, asserted a second "
            "time while also writing the report artifact. Until the datetime "
            "import was added this test errored at fixture setup rather than "
            "failing, so the report it exists to produce was never written at "
            "all. strict=True so regenerating the catalog surfaces both markers."
        ),
    )
    def test_version_match(self, api_catalog: dict, platform_version: str, report: dict):
        catalog_v = api_catalog.get("platform_version", "")
        ok = catalog_v == platform_version
        report["results"].append({
            "test": "version_match",
            "status": "PASS" if ok else "FAIL",
            "expected": platform_version,
            "actual": catalog_v,
        })
        report["summary"]["total"] += 1
        if ok:
            report["summary"]["passed"] += 1
        else:
            report["summary"]["failed"] += 1
        assert ok, f"Version mismatch: backend={platform_version}, catalog={catalog_v}"
