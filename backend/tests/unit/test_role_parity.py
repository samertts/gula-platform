"""Frontend ↔ backend role-parity regression gate.

The frontend mirror at frontend-v3/src/permissions/index.ts must stay in
lockstep with the canonical shared/rbac definition. This test parses the
TypeScript mirror and asserts every role and its permission set matches the
canonical Python source of truth, so a UI developer cannot silently drop a
role or permission and break RBAC alignment.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from shared.rbac import (
    EXTENDED_ROLE_LEVELS as CANONICAL_ROLE_LEVELS,
)
from shared.rbac import (
    EXTENDED_ROLE_PERMISSIONS as CANONICAL_ROLE_PERMISSIONS,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_PERMISSIONS = REPO_ROOT / "frontend-v3" / "src" / "permissions" / "index.ts"
BACKEND_TYPES = REPO_ROOT / "frontend-v3" / "src" / "types" / "backend.ts"

pytestmark = pytest.mark.governance


def _parse_ts_roles() -> dict[str, set[str]]:
    """Parse ROLE_PERMISSIONS from the frontend mirror without running TS."""
    src = FRONTEND_PERMISSIONS.read_text(encoding="utf-8")
    block = re.search(r"export const ROLE_PERMISSIONS:.*?= \{", src)
    assert block, "ROLE_PERMISSIONS block not found"
    body = src[block.end():]
    body = body.split("};", 1)[0]

    roles: dict[str, set[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        m = re.match(r"\s*([\w]+):\s*\[", line)
        if m:
            current = m.group(1)
            roles.setdefault(current, set())
            continue
        if current is None:
            continue
        for perm in re.findall(r'"([a-z]+:[a-z_]+)"', line):
            roles[current].add(perm)
        if "]," in line:
            current = None
    return roles


def test_frontend_permissions_mirror_exists():
    assert FRONTEND_PERMISSIONS.exists(), "frontend permissions module missing"
    assert BACKEND_TYPES.exists(), "frontend backend types module missing"


def test_all_canonical_roles_present_in_frontend():
    ts_roles = _parse_ts_roles()
    missing = set(CANONICAL_ROLE_PERMISSIONS) - set(ts_roles)
    assert not missing, f"frontend ROLE_PERMISSIONS missing roles: {sorted(missing)}"


def test_no_unknown_roles_in_frontend():
    ts_roles = _parse_ts_roles()
    extra = set(ts_roles) - set(CANONICAL_ROLE_PERMISSIONS)
    assert not extra, f"frontend ROLE_PERMISSIONS has roles unknown to shared/rbac: {sorted(extra)}"


def test_permission_sets_match_canonical():
    ts_roles = _parse_ts_roles()
    for role, canonical_perms in CANONICAL_ROLE_PERMISSIONS.items():
        expected = set(canonical_perms)
        actual = ts_roles.get(role, set())
        assert actual == expected, (
            f"role {role} mismatch:\n  canonical: {sorted(expected)}\n  frontend:  {sorted(actual)}"
        )


def test_user_role_type_includes_all_canonical_roles():
    src = BACKEND_TYPES.read_text(encoding="utf-8")
    type_block = re.search(r"export type UserRole =[\s\S]*?;\n", src)
    assert type_block, "UserRole type not found"
    for role in CANONICAL_ROLE_PERMISSIONS:
        assert role in type_block.group(0), f"UserRole type missing '{role}'"
