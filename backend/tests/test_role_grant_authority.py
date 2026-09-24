"""NR-140 — who may grant a role, and which roles they may grant.

POST /authz/assignments depended on get_current_user and nothing else, and
RoleAssignmentService.assign_role performs no authorization check of its own:
it wrote user_id, role_id and organization_id straight from the request body.

Measured against a live server before the fix: an ordinary lab admin's request
reached the INSERT carrying attacker-chosen values and was stopped only by
role_assignments_assigned_by_fkey. A foreign key is referential integrity, not
an authorization control -- it refuses an id that does not exist, not a caller
who may not act.

After the fix the same request is refused 403 by authorization, before any
write is attempted.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.routes.authorization import _require_role_granting_authority


def _actor(role):
    return SimpleNamespace(role=role, id=1, lab_id=1)


@pytest.mark.parametrize("role", ["admin", "lab_admin", "lab_tech", "doctor", "citizen", "", None])
def test_a_non_platform_role_may_not_grant_anything(role):
    with pytest.raises(HTTPException) as exc:
        _require_role_granting_authority(_actor(role), "lab_tech")
    assert exc.value.status_code == 403


def test_a_platform_role_may_grant_a_role_below_it():
    """Positive control: without it, every denial above could be a denial of everything."""
    _require_role_granting_authority(_actor("master_admin"), "lab_tech")


def test_a_platform_role_may_not_grant_at_or_above_its_own_level():
    """Otherwise a province_admin could mint a master_admin."""
    with pytest.raises(HTTPException) as exc:
        _require_role_granting_authority(_actor("province_admin"), "master_admin")
    assert exc.value.status_code == 403


def test_an_actor_with_no_role_attribute_is_refused():
    with pytest.raises(HTTPException) as exc:
        _require_role_granting_authority(SimpleNamespace(id=1), "lab_tech")
    assert exc.value.status_code == 403


def test_the_guard_runs_before_any_write_is_attempted():
    """The order matters: a refused caller must not reach the database at all.

    Before the fix the only thing standing between an ordinary caller and a
    role_assignments row was a foreign key, which means the INSERT was
    attempted with attacker-controlled values every time.
    """
    import inspect

    from app.routes.authorization import assign_role

    source = inspect.getsource(assign_role)
    guard = source.index("_require_role_granting_authority")
    service = source.index("RoleAssignmentService(db)")
    assert guard < service, "authorization must precede the write path"
