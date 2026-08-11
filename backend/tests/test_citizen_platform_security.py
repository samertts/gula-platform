from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app._compat import UTC
from app.citizen_platform.routes import require_citizen_relationship
from app.identity.models.citizen_relationship import (
    CitizenRelationship,
    CitizenRelationshipStatus,
)
from app.models.user import User


class _FakeQuery:
    def __init__(self, result):
        self.result = result

    def filter(self, *conditions):
        return self

    def order_by(self, *ordering):
        return self

    def first(self):
        return self.result

    def all(self):
        if self.result is None:
            return []
        return self.result if isinstance(self.result, list) else [self.result]


class _FakeDb:
    def __init__(self, result):
        self.result = result
        self.commits = 0

    def query(self, model):
        return _FakeQuery(self.result)

    def commit(self):
        self.commits += 1


def _request(path: str = "/citizen-platform/profile/CITIZEN01", method: str = "GET"):
    return SimpleNamespace(
        url=SimpleNamespace(path=path),
        method=method,
        client=SimpleNamespace(host="127.0.0.1"),
        state=SimpleNamespace(),
    )


def _user() -> User:
    return User(id=41, role="citizen", is_active=True, is_verified=True)


def _relationship(**overrides) -> CitizenRelationship:
    values = {
        "citizen_id": "CITIZEN01",
        "legacy_user_id": 41,
        "status": CitizenRelationshipStatus.active.value,
        "valid_from": datetime.now(UTC) - timedelta(minutes=1),
        "scope": {"resources": ["profile", "health-summary:read"]},
    }
    values.update(overrides)
    return CitizenRelationship(**values)


def test_relationship_allows_explicit_read_and_rejects_write() -> None:
    relationship = _relationship()

    assert relationship.allows("profile") is True
    assert relationship.allows("health-summary") is True
    assert relationship.allows("appointments") is False
    assert relationship.allows("profile", write=True) is False


def test_relationship_denies_missing_scope_by_default() -> None:
    relationship = _relationship(scope=None)

    assert relationship.allows("profile") is False
    assert relationship.allows("profile", write=True) is False


def test_relationship_requires_active_unexpired_state() -> None:
    expired = _relationship(expires_at=datetime.now(UTC) - timedelta(seconds=1))
    revoked = _relationship(revoked_at=datetime.now(UTC), revoked_reason="user_request")

    assert expired.is_active_at() is False
    assert revoked.is_active_at() is False
    assert expired.allows("profile") is False
    assert revoked.allows("profile") is False


def test_route_guard_denies_when_no_explicit_relationship(monkeypatch: pytest.MonkeyPatch) -> None:
    decisions: list[str] = []
    monkeypatch.setattr(
        "app.citizen_platform.routes._record_access_decision",
        lambda *args, **kwargs: decisions.append(kwargs.get("outcome", args[3] if len(args) > 3 else "unknown")),
    )

    with pytest.raises(HTTPException) as exc_info:
        require_citizen_relationship(
            _request(),
            "CITIZEN01",
            _FakeDb(None),
            _user(),
        )

    assert exc_info.value.status_code == 403
    assert decisions == ["denied"]


def test_route_guard_uses_relationship_scope_and_audits_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    decisions: list[str] = []
    monkeypatch.setattr(
        "app.citizen_platform.routes._record_access_decision",
        lambda *args, **kwargs: decisions.append(kwargs.get("outcome", args[3] if len(args) > 3 else "unknown")),
    )
    db = _FakeDb(_relationship())

    result = require_citizen_relationship(
        _request(),
        "CITIZEN01",
        db,
        _user(),
    )

    assert result.citizen_id == "CITIZEN01"
    assert decisions == ["allowed"]
    assert db.commits == 0


def test_route_guard_supports_one_unambiguous_own_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.citizen_platform.routes._record_access_decision", lambda *args, **kwargs: None)
    relationship = _relationship(relationship_type="self", scope={"resources": ["profile"]})

    result = require_citizen_relationship(
        _request("/citizen-platform/me/profile"),
        None,
        _FakeDb(relationship),
        _user(),
    )

    assert result.citizen_id == "CITIZEN01"


def test_route_guard_rejects_ambiguous_own_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.citizen_platform.routes._record_access_decision", lambda *args, **kwargs: None)
    first = _relationship(relationship_type="self", scope={"resources": ["profile"]})
    second = _relationship(citizen_id="CITIZEN02", relationship_type="self", scope={"resources": ["profile"]})

    with pytest.raises(HTTPException) as exc_info:
        require_citizen_relationship(
            _request("/citizen-platform/me/profile"),
            None,
            _FakeDb([first, second]),
            _user(),
        )

    assert exc_info.value.status_code == 403


def test_route_guard_rejects_write_without_explicit_write_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.citizen_platform.routes._record_access_decision", lambda *args, **kwargs: None)

    with pytest.raises(HTTPException) as exc_info:
        require_citizen_relationship(
            _request("/citizen-platform/appointments/CITIZEN01", method="POST"),
            "CITIZEN01",
            _FakeDb(_relationship(scope={"resources": ["appointments"]})),
            _user(),
        )

    assert exc_info.value.status_code == 403
