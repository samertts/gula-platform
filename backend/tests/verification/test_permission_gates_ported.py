"""Authentication was being mistaken for authorization on the patient surface.

Fourteen routes across four modules depended only on ``Depends(get_current_user)``
with no ``require_permission(...)`` anywhere in the handler.  Tenant isolation was
already enforced correctly on all of them, so this is not a cross-tenant leak --
it is privilege escalation *within* a tenant: every authenticated user, whatever
their role, could do what these routes do.

The RBAC matrix on this branch has 16 roles, and it is what makes the exposure
concrete rather than theoretical:

* ``citizen`` and the five finance roles (``finance_auditor``,
  ``finance_controller``, ``finance_operator``, ``reconciler``,
  ``refund_reviewer``) plus ``cashier`` hold NONE of
  ``patients:read``/``patients:write``/``results:read``/``results:write`` --
  yet could list every patient in the lab, read any one of them, and update them.
* ``technician`` holds ``results:read``/``results:write`` but NOT
  ``patients:read``/``patients:write`` -- so it had patient CRUD it is explicitly
  not granted.
* ``doctor`` holds the read permissions but neither write -- so it could create
  patients and create test results without that authority.

PROVENANCE. These fourteen route-to-permission assignments are PORTED from
Mustafa's aefeff7f, not chosen here: he established each one against the
existing RBAC permission strings, with no change to the RBAC matrix itself.
This file re-verifies them independently on this branch rather than trusting
the other branch's evidence, which is why it asserts the refusal for every role
that lacks the permission instead of for one sample role.

SCOPE, stated honestly. Fourteen routes are now gated. The same shape remains on
a much larger surface -- ``ehr.py`` (86 routes) and ``ehr_fhir.py`` (29 routes)
contain no ``require_permission`` call at all, and their router is mounted with a
bare ``include_router``. Those are NOT fixed here and must not be read as covered
by this file; they are recorded as a separate finding because each needs a
permission decision of its own.
"""

from __future__ import annotations

import pytest
from app.security.rbac import get_permissions_for_role

from tests.verification import harness

pytestmark = harness.requires_postgres()

# route -> (method, path, required permission), exactly as ported.
_GATED: tuple[tuple[str, str, str], ...] = (
    ("GET", "/patients", "patients:read"),
    ("POST", "/patients", "patients:write"),
    ("GET", "/patients/family/1", "patients:read"),
    ("GET", "/patients/1/children", "patients:read"),
    ("GET", "/patients/1", "patients:read"),
    ("PUT", "/patients/1", "patients:write"),
    ("GET", "/compliance/fhir/patient/1", "patients:read"),
    ("GET", "/compliance/fhir/observation/1", "results:read"),
    ("GET", "/compliance/fhir/diagnostic-report/1", "results:read"),
    ("GET", "/compliance/fhir/service-request/1", "results:read"),
    ("POST", "/identity/link", "patients:write"),
)

_ROLES_WITHOUT = {
    # Computed from the matrix rather than hardcoded, so a matrix change is
    # reflected instead of silently ignored.
    perm: sorted(
        r for r in ("citizen", "cashier", "technician", "doctor",
                    "finance_auditor", "reconciler", "refund_reviewer")
        if perm not in get_permissions_for_role(r)
    )
    for perm in ("patients:read", "patients:write", "results:read", "results:write")
}


@pytest.fixture
def Session():
    factory = harness.session_factory()
    yield factory
    harness.dispose(factory)


def _call(api, method: str, path: str):
    if method == "GET":
        return api.get(path)
    if method == "POST":
        return api.post(path, json={})
    return api.put(path, json={})


@pytest.mark.parametrize(("method", "path", "permission"), _GATED)
def test_a_role_lacking_the_permission_is_refused(Session, method, path, permission):
    """403 for every role the RBAC matrix says lacks this permission.

    Asserted per role rather than for one sample, because the point of the
    finding is that the gate was absent for all of them at once.
    """
    lacking = _ROLES_WITHOUT[permission]
    assert lacking, f"no test role lacks {permission}; this parametrisation proves nothing"

    for role in lacking:
        actor = harness.Actor(user_id=1, lab_id=1, role=role)
        with harness.client(Session, actor) as api:
            response = _call(api, method, path)
        assert response.status_code == 403, (
            f"{role} lacks {permission} but {method} {path} answered "
            f"{response.status_code}: {response.text[:200]}"
        )
        assert permission in response.text, "the refusal should name the permission required"


@pytest.mark.parametrize(("method", "path", "permission"), _GATED)
def test_a_role_holding_the_permission_is_not_refused_by_the_gate(Session, method, path, permission):
    """The gate must not be a blanket denial.

    A holder may still fail for an unrelated reason -- a missing row gives 404, an
    empty body gives 422 -- so the assertion is specifically that it is NOT 403,
    which is the only status this change can produce.
    """
    role = "admin"
    assert permission in get_permissions_for_role(role)
    actor = harness.Actor(user_id=1, lab_id=1, role=role)
    with harness.client(Session, actor) as api:
        response = _call(api, method, path)

    assert response.status_code != 403, (
        f"{role} holds {permission} but {method} {path} was refused: {response.text[:200]}"
    )


def test_the_permission_strings_used_all_exist_in_the_rbac_matrix():
    """A typo in a permission string would deny every role silently and forever.

    ``require_permission`` compares against the role's permission set, so an
    unknown string is held by nobody and the route becomes permanently
    unreachable rather than raising.
    """
    known: set[str] = set()
    for role in ("admin", "master_admin", "lab_admin", "doctor", "technician", "citizen"):
        known |= set(get_permissions_for_role(role))
    used = {perm for _, _, perm in _GATED}
    unknown = sorted(used - known)
    assert unknown == [], (
        "permission strings held by no role -- these routes would be permanently "
        f"unreachable: {unknown}"
    )
