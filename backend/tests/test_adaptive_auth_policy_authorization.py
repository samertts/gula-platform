"""backend/app/identity/adaptive_auth/routes.py: create_risk_policy,
update_risk_policy, create_session_policy, and update_session_policy
required nothing beyond the parent router's group-level
Depends(get_current_niam_actor) (backend/app/identity/api/router.py) — ANY
authenticated NIAM account, of any role, could rewrite platform-wide risk
thresholds, mitigation actions, MFA requirements, and session limits for
every tenant. update_risk_policy in particular ran an unrestricted
`for k, v in body.items(): setattr(entity, k, v)` with no field exclusion
at all.

RiskPolicy/SessionPolicy (niam_adaptive_risk_policies /
niam_adaptive_session_policies) are genuinely global — no organization_id,
no lab_id. The canonical NIAM authorization engine,
AuthorizationDecisionService, is organization-scoped by design: it denies
whenever organization_id is absent unless the resource_type is in its
NON_ORGANIZATIONAL_READS allowlist (currently role_catalog/
permission_catalog only), so it cannot correctly express "may manage a
platform-wide policy" today, and widening that allowlist would be a change
to canonical NIAM authorization semantics this branch is not authorized to
make on its own (a protected decision, not an implementation detail).

Rather than invent a parallel authorization mechanism, this fails closed —
the same choice already made for nhop-platform's trusted context: an
endpoint with no correct answer yet is unavailable, not guessed at.

A full HTTP-level proof (mint a real NIAM account + session + token, call
the route, assert 403 before and 200 after a real decision exists) needs a
NIAM actor test harness this suite does not yet have — no existing test
exercises these routes via HTTP at all (test_niam_v2.py is model-level
only). This is a source-level proof of the same kind
test_care_continuum_tenant_scope.py already used for an analogous
infrastructure gap, stated rather than hidden.
"""
from __future__ import annotations

import inspect

import pytest
from fastapi import HTTPException


def test_require_policy_admin_always_denies():
    from app.identity.adaptive_auth.routes import _require_policy_admin

    with pytest.raises(HTTPException) as exc:
        _require_policy_admin()
    assert exc.value.status_code == 403


@pytest.mark.parametrize("handler", [
    "create_risk_policy",
    "update_risk_policy",
    "create_session_policy",
    "update_session_policy",
])
def test_every_global_policy_mutation_route_carries_the_guard(handler):
    """Pins the wiring: removing Depends(_require_policy_admin) from any of
    these four routes fails here by name, rather than silently reopening
    the gap."""
    from app.identity.adaptive_auth import routes

    source = inspect.getsource(getattr(routes, handler))
    assert "_require_policy_admin" in source, (
        f"{handler}() no longer depends on _require_policy_admin — global "
        f"risk/session policy mutation is open to any authenticated NIAM "
        f"actor again"
    )
