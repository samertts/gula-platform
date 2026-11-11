"""Coverage proof for the NHOP trust boundary (F1/X-Role/F2 closure, Mission 4).

Enumerates the ACTUALLY SERVED route surface via app.openapi()["paths"] —
not by walking router objects, which can include phantom entries or miss
routes registered through include_router — and proves every /v1/* path
requires the trusted context dependency with no bypass, while /health stays
open (it is mounted on the app directly, not on api_router, by design).

This also exercises doctor.py and outbreak.py specifically: on this branch
(unlike the upstream branch this pattern was reviewed against) both routers
are actually included in api_router, so their pre-fix X-Actor-Role/X-Role
header-trust bugs were live and reachable, not dead code. This file proves
that gap is closed too, not just citizens.py/notifications.py/test_results.py.
"""
from __future__ import annotations


def _drop_identity_shim(client):
    """See test_rbac_is_not_a_trust_boundary.py's copy of this helper for why
    the import happens here rather than at module level: app_client purges
    and re-imports app.* on every fixture call, so a module-level reference
    can silently go stale and turn this into a no-op."""
    from app.core.trusted_context import require_trusted_context

    client.app.dependency_overrides.pop(require_trusted_context, None)


def test_every_v1_path_fails_closed_with_no_override(app_client):
    client, _ = app_client
    _drop_identity_shim(client)

    app = client.app
    paths = app.openapi()["paths"]
    v1_paths = [p for p in paths if p.startswith("/v1/")]

    # Guard against a vacuous pass: this must actually enumerate a
    # meaningful surface, or the "every path" claim below is untested.
    assert len(v1_paths) >= 10, (
        f"expected the v1 surface to have grown past its historical 10 "
        f"operations; got {len(v1_paths)}: {sorted(v1_paths)}"
    )

    # Every module must be represented — this is what would fail if
    # doctor.py or outbreak.py were ever unregistered from api_router again,
    # since then their paths simply would not appear here at all.
    for prefix in ("/v1/citizens", "/v1/test-results", "/v1/notifications",
                   "/v1/doctor", "/v1/outbreak"):
        assert any(p.startswith(prefix) for p in v1_paths), (
            f"no served path under {prefix} — router not mounted?"
        )

    failures = []
    for path, operations in paths.items():
        if not path.startswith("/v1/"):
            continue
        for method in operations:
            if method.upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                continue
            # A templated path (e.g. /v1/citizens/{health_id}) is fine to
            # probe with a literal placeholder: routing happens before body
            # validation, and the dependency runs before either.
            concrete = path
            for segment in path.split("/"):
                if segment.startswith("{") and segment.endswith("}"):
                    concrete = concrete.replace(segment, "probe-value", 1)
            resp = client.request(method.upper(), concrete)
            if resp.status_code != 503:
                failures.append((method.upper(), path, resp.status_code))

    assert failures == [], (
        f"these v1 operations did NOT fail closed with no trusted context: "
        f"{failures}"
    )


def test_health_stays_open(app_client):
    """/health must NOT require a trusted context — it is mounted on the
    app directly, not on api_router, specifically so liveness checks are
    never blocked by identity federation status."""
    client, _ = app_client
    _drop_identity_shim(client)

    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_no_duplicate_app_factory_bypasses_the_boundary():
    """app/main.py must define exactly one create_app()/app, mounting
    api_router (which carries the dependency) rather than the bare
    sub-routers individually. A second, forgotten app factory that mounted
    citizens_router/doctor_router/etc. directly would silently reopen every
    route this file just proved closed."""
    import ast
    import pathlib

    main_path = pathlib.Path(__file__).resolve().parent.parent / "app" / "main.py"
    tree = ast.parse(main_path.read_text())

    app_factories = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name in {"create_app", "make_app"}
    ]
    assert len(app_factories) == 1, (
        f"expected exactly one app factory in app/main.py, found "
        f"{[f.name for f in app_factories]} — a second one could mount "
        f"routers without the trusted-context dependency"
    )

    source = main_path.read_text()
    assert "include_router(api_router)" in source, (
        "app/main.py must mount api_router (which carries the "
        "require_trusted_context dependency), not individual sub-routers"
    )
    for leaf in ("citizens_router", "doctor_router", "notifications_router",
                 "outbreak_router", "test_results_router"):
        assert f"include_router({leaf})" not in source, (
            f"app/main.py includes {leaf} directly, bypassing api_router's "
            f"trusted-context dependency"
        )
