"""Platform Authority bootstrap (Workstream 2).

Proves: fresh environment -> bootstrap -> first assignment exists ->
repeated bootstrap -> no duplicate; and that revocation remains
effective (bootstrap never re-grants a capability it already handled,
even after revocation). Same established fake-session pattern as
test_platform_authority_phase10.py / test_platform_authority_workstream1.py.
"""

from __future__ import annotations

import pytest
from app.identity.models.account import Account, AccountStatus
from app.identity.platform_authority.bootstrap import ensure_platform_authority_bootstrap
from app.identity.platform_authority.models import (
    PlatformAuthorityAssignment,
    PlatformAuthorityAssignmentStatus,
    PlatformCapability,
)


class _Result:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def scalar_one_or_none(self):
        return self._row

    def scalars(self):
        return self

    def all(self):
        return self._rows


class _FakeDb:
    def __init__(self, *, account=None, existing_assignments=None):
        self.account = account
        self.assignments: list[PlatformAuthorityAssignment] = list(existing_assignments or [])
        self.added: list = []
        self.commit_count = 0
        self.flush_count = 0
        self._counter = 0

    def add(self, obj):
        self._counter += 1
        if getattr(obj, "id", None) is None:
            obj.id = f"GEN-{self._counter:04d}"
        self.added.append(obj)
        if isinstance(obj, PlatformAuthorityAssignment):
            self.assignments.append(obj)

    async def flush(self):
        self.flush_count += 1

    async def commit(self):
        self.commit_count += 1

    async def rollback(self):
        pass

    async def execute(self, stmt):
        table = stmt.get_final_froms()[0].name
        if table == "niam_accounts":
            return _Result(self.account)
        if table == "niam_platform_authority_assignments":
            # existence-check query (bootstrap's _already_handled) selects
            # only .id with no status filter; PlatformAuthorityService's
            # own _active_assignment selects the full row with a status
            # filter baked into the compiled statement's params.
            params = {k.rsplit("_", 1)[0]: v for k, v in stmt.compile().params.items()}
            matches = [
                a for a in self.assignments
                if a.identity_id == params.get("identity_id") and a.capability == params.get("capability")
            ]
            if "status" in params:
                matches = [a for a in matches if a.status == params["status"]]
            return _Result(matches[0] if matches else None)
        return _Result(None)  # audit hash-chain lookup etc.


def _account(email="admin@example.iq", identity_id="IDENTITY0000000000000001"):
    return Account(
        id="ACCOUNT0000000000000001", uuid="account-uuid-1", identity_id=identity_id,
        email=email, status=AccountStatus.active.value, is_active=True, is_locked=False,
    )


# ── Unconfigured / malformed input -- fail closed, never crash ──────────────


@pytest.mark.asyncio
async def test_unconfigured_is_a_complete_noop(monkeypatch):
    monkeypatch.delenv("PLATFORM_AUTHORITY_BOOTSTRAP_ACCOUNT_EMAIL", raising=False)
    monkeypatch.delenv("PLATFORM_AUTHORITY_BOOTSTRAP_CAPABILITIES", raising=False)
    db = _FakeDb()
    granted = await ensure_platform_authority_bootstrap(db)
    assert granted == []
    assert db.added == []


@pytest.mark.asyncio
async def test_unresolvable_account_grants_nothing(monkeypatch):
    monkeypatch.setenv("PLATFORM_AUTHORITY_BOOTSTRAP_ACCOUNT_EMAIL", "nobody@example.iq")
    monkeypatch.setenv("PLATFORM_AUTHORITY_BOOTSTRAP_CAPABILITIES", "platform.trust.manage")
    db = _FakeDb(account=None)
    granted = await ensure_platform_authority_bootstrap(db)
    assert granted == []
    assert db.added == []


@pytest.mark.asyncio
async def test_unknown_capability_is_skipped_not_fatal(monkeypatch):
    monkeypatch.setenv("PLATFORM_AUTHORITY_BOOTSTRAP_ACCOUNT_EMAIL", "admin@example.iq")
    monkeypatch.setenv(
        "PLATFORM_AUTHORITY_BOOTSTRAP_CAPABILITIES",
        "platform.not_a_real_capability,platform.trust.manage",
    )
    db = _FakeDb(account=_account())
    granted = await ensure_platform_authority_bootstrap(db)
    assert granted == ["platform.trust.manage"]  # the bad entry didn't block the good one


# ── Fresh environment -> bootstrap -> first assignment exists ──────────────


@pytest.mark.asyncio
async def test_fresh_bootstrap_grants_and_audits(monkeypatch):
    monkeypatch.setenv("PLATFORM_AUTHORITY_BOOTSTRAP_ACCOUNT_EMAIL", "admin@example.iq")
    monkeypatch.setenv(
        "PLATFORM_AUTHORITY_BOOTSTRAP_CAPABILITIES",
        "platform.federation.manage,platform.trust.manage",
    )
    db = _FakeDb(account=_account())
    granted = await ensure_platform_authority_bootstrap(db)

    assert granted == ["platform.federation.manage", "platform.trust.manage"]
    real_assignments = [a for a in db.added if isinstance(a, PlatformAuthorityAssignment)]
    assert len(real_assignments) == 2
    assert all(a.status == PlatformAuthorityAssignmentStatus.active.value for a in real_assignments)
    audit_entries = [o for o in db.added if type(o).__name__ == "IdentityAuditEntry"]
    event_types = {e.event_type for e in audit_entries}
    assert "bootstrap_started" in event_types
    assert "bootstrap_completed" in event_types
    assert "PLATFORM_AUTHORITY_GRANTED" in event_types  # grant()'s own entry, not suppressed


# ── Repeated bootstrap -> no duplicate assignment ───────────────────────────


@pytest.mark.asyncio
async def test_repeated_bootstrap_grants_nothing_new(monkeypatch):
    monkeypatch.setenv("PLATFORM_AUTHORITY_BOOTSTRAP_ACCOUNT_EMAIL", "admin@example.iq")
    monkeypatch.setenv("PLATFORM_AUTHORITY_BOOTSTRAP_CAPABILITIES", "platform.trust.manage")
    account = _account()

    db1 = _FakeDb(account=account)
    first = await ensure_platform_authority_bootstrap(db1)
    assert first == ["platform.trust.manage"]

    # Second "restart": a fresh session, but the same assignment now exists
    # (as it would in a real database across process restarts).
    existing = [a for a in db1.added if isinstance(a, PlatformAuthorityAssignment)]
    db2 = _FakeDb(account=account, existing_assignments=existing)
    second = await ensure_platform_authority_bootstrap(db2)

    assert second == []  # no duplicate
    assert [a for a in db2.added if isinstance(a, PlatformAuthorityAssignment)] == []


# ── Revocation remains effective: bootstrap never re-grants ─────────────────


@pytest.mark.asyncio
async def test_revoked_capability_is_never_re_bootstrapped(monkeypatch):
    """Once bootstrap-granted, a capability is never re-granted by bootstrap
    again, even after it's later revoked -- the design's deliberate choice
    (Section 7/8): bootstrap is a true one-time-per-capability event, not a
    standing recovery mechanism."""
    monkeypatch.setenv("PLATFORM_AUTHORITY_BOOTSTRAP_ACCOUNT_EMAIL", "admin@example.iq")
    monkeypatch.setenv("PLATFORM_AUTHORITY_BOOTSTRAP_CAPABILITIES", "platform.governance.manage")
    account = _account()

    revoked_assignment = PlatformAuthorityAssignment(
        id="PA-REVOKED-0001", uuid="pa-revoked-1", identity_id=account.identity_id,
        capability=PlatformCapability.governance_manage.value,
        status=PlatformAuthorityAssignmentStatus.revoked.value,
    )
    db = _FakeDb(account=account, existing_assignments=[revoked_assignment])
    granted = await ensure_platform_authority_bootstrap(db)

    assert granted == []  # revocation remains effective; not silently re-granted
    assert [a for a in db.added if isinstance(a, PlatformAuthorityAssignment)] == []
