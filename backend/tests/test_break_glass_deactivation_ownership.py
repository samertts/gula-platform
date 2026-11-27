"""Synthetic tests for break-glass deactivation ownership.

The deactivation route now supplies the trusted authenticated user id. These
tests prove that a session belonging to another user cannot be deactivated by
guessing its numeric id. No database, real identity, or production config is
used.
"""

from __future__ import annotations

from types import SimpleNamespace

from app.services.authorization_service import BreakGlassService


class _FakeQuery:
    def __init__(self, record) -> None:
        self._record = record
        self._criteria: list[object] = []

    def filter(self, *criteria) -> _FakeQuery:
        self._criteria.extend(criteria)
        return self

    def first(self):
        if self._record is None:
            return None
        for criterion in self._criteria:
            column = getattr(getattr(criterion, "left", None), "key", None)
            expected = getattr(getattr(criterion, "right", None), "value", None)
            if column is None or expected is None:
                continue
            if getattr(self._record, column, None) != expected:
                return None
        return self._record


class _FakeDatabase:
    def __init__(self, record) -> None:
        self._record = record
        self.commits = 0

    def query(self, _model):
        return _FakeQuery(self._record)

    def commit(self) -> None:
        self.commits += 1


def _record() -> SimpleNamespace:
    return SimpleNamespace(
        id=17,
        user_id=42,
        status="active",
        deactivated_at=None,
    )


def test_owner_can_deactivate_own_break_glass_session() -> None:
    record = _record()
    db = _FakeDatabase(record)

    assert BreakGlassService(db).deactivate(17, 42) is True
    assert record.status == "deactivated"
    assert record.deactivated_at is not None
    assert db.commits == 1


def test_other_user_cannot_deactivate_break_glass_session() -> None:
    record = _record()
    db = _FakeDatabase(record)

    assert BreakGlassService(db).deactivate(17, 99) is False
    assert record.status == "active"
    assert record.deactivated_at is None
    assert db.commits == 0


def test_unknown_or_inactive_session_is_not_deactivated() -> None:
    db = _FakeDatabase(None)
    assert BreakGlassService(db).deactivate(17, 42) is False
    assert db.commits == 0

    inactive = _record()
    inactive.status = "deactivated"
    inactive_db = _FakeDatabase(inactive)
    assert BreakGlassService(inactive_db).deactivate(17, 42) is False
    assert inactive_db.commits == 0
