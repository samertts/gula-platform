from __future__ import annotations

import os

import pytest

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

def _get_registered_routes():
    from app.main import app
    routes = {}
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            for method in route.methods:
                if method in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                    path = route.path
                    if path not in routes:
                        routes[path] = set()
                    routes[path].add(method.upper())
    return routes


def _path_match(route_path: str, catalog_path: str) -> bool:
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


# ── Tests ──────────────────────────────────────────────────────────────

class TestEndpointReachability:
    """For each endpoint in the catalog, verify it's reachable at the expected path."""

    def test_all_catalog_paths_registered(self, api_catalog: dict):
        routes = _get_registered_routes()
        catalog = api_catalog.get("catalog", {})
        unmatched = []
        for group_name, group in catalog.items():
            for path, methods in group.items():
                matched = False
                for r_path, r_methods in routes.items():
                    if _path_match(r_path, path):
                        matched = True
                        break
                if not matched:
                    unmatched.append(f"{group_name}: {path}")
        assert not unmatched, f"Catalog paths not found in backend:\n" + "\n".join(unmatched)

    def test_health_endpoints_public(self, client):
        public_paths = ["/health", "/health/live", "/health/ready", "/health/status", "/health/deep"]
        for path in public_paths:
            resp = client.get(path)
            assert resp.status_code == 200, f"{path} returned {resp.status_code}"

    def test_login_endpoint_public(self, client):
        resp = client.post("/login", json={"email": "test@test.com", "password": "test"})
        assert resp.status_code != 404, "/login endpoint not found"


class TestHTTPMethodMatching:
    """Test that HTTP methods match what's expected."""

    def test_methods_match_catalog(self, api_catalog: dict):
        routes = _get_registered_routes()
        catalog = api_catalog.get("catalog", {})
        mismatches = []
        for group_name, group in catalog.items():
            for path, methods in group.items():
                for method in methods:
                    for r_path, r_methods in routes.items():
                        if _path_match(r_path, path):
                            if method.upper() not in r_methods:
                                mismatches.append(
                                    f"{method.upper()} {path} not registered (backend has {r_methods})"
                                )
        allowed_mismatches = 3
        assert len(mismatches) <= allowed_mismatches, (
            f"Method mismatches (>{allowed_mismatches}):\n" + "\n".join(mismatches[:10])
        )


class TestPaginationContract:
    """Test pagination contracts."""

    def test_pagination_endpoints_respect_default_limit(self, api_catalog: dict):
        catalog = api_catalog.get("catalog", {})
        paginated = []
        for group_name, group in catalog.items():
            for path, methods in group.items():
                for method, details in methods.items():
                    pag = details.get("pagination", {})
                    if pag.get("enabled"):
                        paginated.append((method, path, pag))
        assert len(paginated) > 0, "No paginated endpoints found in catalog"
        for method, path, pag in paginated:
            assert "default_limit" in pag, f"{method} {path} missing default_limit"
            assert "max_limit" in pag, f"{method} {path} missing max_limit"

    def test_cursor_pagination_not_used(self, api_catalog: dict):
        catalog = api_catalog.get("catalog", {})
        for group_name, group in catalog.items():
            for path, methods in group.items():
                for method, details in methods.items():
                    pag = details.get("pagination", {})
                    if pag.get("cursor", False):
                        pytest.fail(f"{method} {path} uses cursor pagination (not yet supported)")


class TestAuthRequirements:
    """Test auth requirements match."""

    def test_public_endpoints_no_auth_needed(self, client, api_catalog: dict):
        catalog = api_catalog.get("catalog", {})
        public_paths = []
        for group_name, group in catalog.items():
            for path, methods in group.items():
                for method, details in methods.items():
                    if not details.get("auth", {}).get("auth_required", True):
                        public_paths.append((method, path))
        for method, path in public_paths[:5]:
            fn = getattr(client, method.lower())
            resp = fn(path)
            assert resp.status_code not in (401, 403), f"Public {method} {path} requires auth"

    def test_auth_endpoints_require_bearer(self, client, api_catalog: dict):
        catalog = api_catalog.get("catalog", {})
        authed = []
        for group_name, group in catalog.items():
            for path, methods in group.items():
                for method, details in methods.items():
                    if details.get("auth", {}).get("auth_required", False):
                        authed.append((method, path))
                        break
        for method, path in authed[:3]:
            fn = getattr(client, method.lower())
            resp = fn(path)
            assert resp.status_code in (401, 403, 503), (
                f"Authed {method} {path} allowed without token (got {resp.status_code})"
            )


class TestDeprecationContract:
    """Test deprecation metadata."""

    def test_no_deprecated_endpoints_remain(self, api_catalog: dict):
        catalog = api_catalog.get("catalog", {})
        deprecated = []
        for group_name, group in catalog.items():
            for path, methods in group.items():
                for method, details in methods.items():
                    if details.get("deprecated", False):
                        deprecated.append(f"{method} {path}")
        assert len(deprecated) == 0, f"Deprecated endpoints remain in catalog: {deprecated}"
