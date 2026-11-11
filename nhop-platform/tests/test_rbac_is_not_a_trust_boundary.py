"""F1 / X-Role trust-boundary closure proof for core/rbac.py.

This file used to PROVE a real vulnerability: require_roles() read X-Role
straight off the incoming request with no verification against any session,
token, or server-side identity, so a bare self-asserted header granted
whatever authority it claimed. That code path no longer exists — role now
comes exclusively from app.core.trusted_context, which fails closed (503)
until a real identity provider is federated (see that module's docstring).

These tests prove the closure directly against the production app, bypassing
the test suite's own legacy-header compatibility shim (conftest.py's
app_client override) on purpose: that shim exists only so pre-existing
positive-path tests didn't all need rewriting, and honoring X-Role there
would make this file indistinguishable from the original vulnerability. To
prove headers carry no authority in production, the override must be
removed for the duration of the test, not merely fed a value.
"""
from __future__ import annotations


def _drop_identity_shim(client):
    """Remove conftest's legacy-header override so the route is exercised
    exactly as production serves it: require_trusted_context() unconditionally
    503s, and nothing published on request.state.trusted_context.

    Imports require_trusted_context here, not at module level: app_client
    purges and re-imports app.* on every fixture call, so a reference
    captured at module-collection time can be a stale object that no
    longer matches the dependency_overrides key the current app actually
    uses — silently turning this into a no-op. Importing at call time,
    after app_client has already run for this test, keeps it current.
    """
    from app.core.trusted_context import require_trusted_context

    client.app.dependency_overrides.pop(require_trusted_context, None)


def test_x_role_header_no_longer_has_any_effect_on_the_outcome(
    app_client, make_citizen
):
    """Two identical requests, two different self-asserted roles, against the
    real production dependency (no override): both must fail the same way.
    If X-Role still swung the outcome, the header would still be authority."""
    client, Session = app_client
    with Session() as s:
        make_citizen(s, health_id="HID-SPOOF-1")
    _drop_identity_shim(client)

    as_citizen = client.get("/v1/citizens/HID-SPOOF-1", headers={"X-Role": "CITIZEN"})
    as_admin = client.get("/v1/citizens/HID-SPOOF-1", headers={"X-Role": "ADMIN"})

    assert as_citizen.status_code == 503
    assert as_admin.status_code == 503
    assert as_citizen.status_code == as_admin.status_code


def test_self_declared_admin_can_no_longer_write_pii(app_client):
    """The exact forged request that used to succeed (F1's original PoC):
    X-Role: ADMIN with no prior authentication step. Must now be refused,
    not merely re-labeled — no citizen record may be created."""
    client, Session = app_client
    _drop_identity_shim(client)

    resp = client.post(
        "/v1/citizens/register",
        json={"full_name": "لا يوجد مصادقة هنا"},
        headers={"X-Role": "ADMIN"},
    )
    assert resp.status_code == 503

    with Session() as s:
        from app.models.citizen import Citizen

        assert s.query(Citizen).filter(
            Citizen.full_name == "لا يوجد مصادقة هنا"
        ).first() is None


def test_missing_role_header_and_forged_role_header_fail_identically(app_client):
    """Before the fix, "missing header" (401) and "forged header" (200/403)
    were distinguishable outcomes — that distinguishability is exactly what
    let a caller discover the shape of the gate and defeat it. Now both must
    produce the same fail-closed response."""
    client, _ = app_client
    _drop_identity_shim(client)

    no_header = client.post("/v1/citizens/register", json={"full_name": "بلا رأس"})
    forged = client.post(
        "/v1/citizens/register",
        json={"full_name": "رأس مزوّر"},
        headers={"X-Role": "MINISTRY"},
    )

    assert no_header.status_code == 503
    assert forged.status_code == 503
