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

def _iter_api_routes(router_routes, prefix: str = ""):
    """Flatten FastAPI routes, including the lazy ``_IncludedRouter`` wrappers.

    IA-069. A flat walk of ``app.routes`` sees 11 of this app's routes. The
    other 119 entries are ``fastapi.routing._IncludedRouter`` wrappers -- the
    lazy form FastAPI uses for ``include_router`` -- which carry neither
    ``.path`` nor ``.methods``, so ``hasattr(route, "path")`` silently drops
    every router-included route. That is how this test came to report ``/login``
    and ``/patients`` as unregistered while its own sibling test reached
    ``/login`` over HTTP in the same file.

    The nested prefix is concatenated, not replaced: a router included inside
    an already-prefixed router must keep both prefixes, or the paths come out
    wrong rather than merely missing.
    """
    from fastapi.routing import APIRoute

    for route in router_routes:
        if isinstance(route, APIRoute):
            yield route, f"{prefix.rstrip('/')}{route.path or '/'}"
            continue
        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            include_context = getattr(route, "include_context", None)
            own = getattr(include_context, "prefix", None) or ""
            yield from _iter_api_routes(original_router.routes, f"{prefix.rstrip('/')}{own}")
        elif hasattr(route, "routes"):
            own = getattr(route, "path", "") or ""
            yield from _iter_api_routes(route.routes, f"{prefix.rstrip('/')}{own}")


def _get_registered_routes():
    from app.main import app

    routes: dict[str, set[str]] = {}
    for route, path in _iter_api_routes(app.routes):
        for method in route.methods or set():
            if method in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                routes.setdefault(path, set()).add(method.upper())
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


def _load_gap_ledger() -> dict:
    """The recorded catalog-vs-reality gap (IA-069)."""
    import json

    path = os.path.join(os.path.dirname(__file__), "KNOWN_CATALOG_GAP.json")
    return json.loads(open(path, encoding="utf-8").read())


# ── Tests ──────────────────────────────────────────────────────────────

class TestEndpointReachability:
    """For each endpoint in the catalog, verify it's reachable at the expected path."""

    def test_the_route_census_is_not_inert(self):
        """Positive control. Every assertion below is vacuous without this.

        IA-069: the previous census saw 11 routes and reported /login and
        /patients as unregistered. A census that silently finds almost nothing
        makes a "not found" result meaningless, so pin both a plausible
        magnitude and a few paths that are certainly registered.
        """
        routes = _get_registered_routes()
        assert len(routes) > 1000, f"census collapsed to {len(routes)} paths"
        for certain in ("/login", "/patients", "/health", "/metrics/prom"):
            assert certain in routes, f"{certain} missing from the census"

    def test_catalog_gap_matches_the_recorded_ledger(self, api_catalog: dict):
        """The catalog and the app disagree. The ledger says by how much.

        IA-069. 254 of the catalog's 313 paths are not registered -- verified by
        a 16-path random sample, all 16 absent from the resolved census. This
        does not assert the gap is acceptable; it asserts the gap is *known*.
        It fails if the gap grows (new drift) and if it shrinks (a real fix, or
        a catalog edit) without KNOWN_CATALOG_GAP.json being updated to match.

        Note on method: for this app a non-404 HTTP response does NOT prove a
        documented path exists. GET /insurance/claims answers 401, but only
        because /insurance/{insurance_id} matches with insurance_id="claims";
        the documented path is absent. Parameterised siblings swallow concrete
        segments, so the resolved census is the decisive evidence, not a probe.
        """
        ledger = _load_gap_ledger()
        routes = _get_registered_routes()
        catalog = api_catalog.get("catalog", {})

        unmatched = set()
        for group_name, group in catalog.items():
            for path in group:
                if not any(_path_match(r_path, path) for r_path in routes):
                    unmatched.add(f"{group_name}: {path}")

        recorded = set(ledger["unmatched_catalog_paths"])
        new_gaps = sorted(unmatched - recorded)
        closed = sorted(recorded - unmatched)

        assert not new_gaps, (
            f"{len(new_gaps)} catalog path(s) became unreachable and are not in "
            f"KNOWN_CATALOG_GAP.json:\n" + "\n".join(new_gaps[:20])
        )
        assert not closed, (
            f"{len(closed)} recorded gap(s) are no longer gaps -- good, but the "
            f"ledger must be regenerated so the remaining count stays honest:\n"
            + "\n".join(closed[:20])
        )

    def test_health_endpoints_are_public(self, client):
        """Public means no credential is demanded -- not that readiness passes.

        IA-069: this asserted 200 on all five. /health/ready answers 503 here,
        which is correct and by design: ReadinessMiddleware holds non-whitelisted
        paths at 503 until startup_guard sets system_ready, and the guard does
        not complete in a test app with no migrated database. Asserting 200
        conflated "reachable without auth" with "this deployment is ready", so
        the test could only pass against a fully started stack.

        What publicness actually requires: the path exists (not 404) and no
        credential is demanded (not 401/403). /health and /health/live must
        additionally be 200, since liveness does not depend on readiness.
        """
        for path in ("/health", "/health/live"):
            resp = client.get(path)
            assert resp.status_code == 200, f"{path} returned {resp.status_code}"

        for path in ("/health/ready", "/health/status", "/health/deep"):
            resp = client.get(path)
            assert resp.status_code != 404, f"{path} is not registered"
            assert resp.status_code not in (401, 403), (
                f"{path} demanded a credential ({resp.status_code}); the health "
                "whitelist must stay public or orchestration cannot probe it"
            )

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
        # IA-069: this was `len(mismatches) <= 3`, a magic tolerance that hid up
        # to three real mismatches and said nothing about which. The ledger
        # names all 27 instead, and ratchets both ways.
        ledger = _load_gap_ledger()
        recorded = set(ledger["method_mismatches"])
        measured = {m.split(" not registered")[0] for m in mismatches}

        new_mismatches = sorted(measured - recorded)
        fixed = sorted(recorded - measured)
        assert not new_mismatches, (
            f"{len(new_mismatches)} method mismatch(es) not in "
            f"KNOWN_CATALOG_GAP.json:\n" + "\n".join(new_mismatches[:20])
        )
        assert not fixed, (
            f"{len(fixed)} recorded mismatch(es) are resolved -- regenerate "
            f"KNOWN_CATALOG_GAP.json:\n" + "\n".join(fixed[:20])
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
