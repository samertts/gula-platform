"""Phase G (D-023) — canonical patient merge security regression, synthetic only.

Proves: role guard, cross-tenant merge prevention, missing-record handling,
and audit logging. No real patient data, no DB, no network.

Evidence id: E-057 (see GOVERNANCE/GECS/EVIDENCE_REGISTRY.md).
"""

from __future__ import annotations

from types import SimpleNamespace

import logging

import pytest
from fastapi import HTTPException

from app.routes import canonical_patient as route


class _FakeDB:
    """Returns records by call order: first target lookup, then source lookup."""

    def __init__(self, *rows):
        self._rows = list(rows)
        self.committed = False

    def query(self, model):
        rows = self._rows
        return _SeqQuery(rows.pop(0) if rows else None)

    def commit(self):
        self.committed = True


class _SeqQuery:
    def __init__(self, row):
        self._row = row

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._row


def _record(id, lab_id):
    return SimpleNamespace(id=id, lab_id=lab_id)


def _call_merge(db, user, target=1, source=2):
    return route.merge(
        data=route.CanonicalPatientMerge(target_id=target, source_id=source),
        current_user=user,
        db=db,
    )


class TestMergeRoleGuard:
    def test_ordinary_user_denied_by_role_dependency(self):
        checker = route.require_role("master_admin", "ministry_admin", "admin", "lab_admin")
        with pytest.raises(HTTPException) as exc:
            checker(current_user=SimpleNamespace(role="technician"))
        assert exc.value.status_code == 403
        with pytest.raises(HTTPException) as exc:
            checker(current_user=SimpleNamespace(role="citizen"))
        assert exc.value.status_code == 403

    def test_admin_roles_allowed_by_dependency(self):
        checker = route.require_role("master_admin", "ministry_admin", "admin", "lab_admin")
        for role in ("master_admin", "ministry_admin", "admin", "lab_admin"):
            user = SimpleNamespace(role=role)
            assert checker(current_user=user) is user

    def test_merge_route_declares_admin_guard(self):
        # Guard against regression: the merge route must not use bare get_current_user.
        source = __import__("inspect").getsource(route.merge)
        assert "require_role" in source
        assert "get_current_user" not in source


class TestMergeTenantIsolation:
    def test_cross_lab_merge_rejected(self):
        db = _FakeDB(_record(1, 1), _record(2, 2))
        with pytest.raises(HTTPException) as exc:
            _call_merge(db, SimpleNamespace(id=9, role="master_admin"))
        assert exc.value.status_code == 403
        assert exc.value.detail["error"] == "cross_lab_merge_denied"
        assert not db.committed

    def test_missing_record_rejected(self):
        db = _FakeDB(_record(1, 1), None)
        with pytest.raises(HTTPException) as exc:
            _call_merge(db, SimpleNamespace(id=9, role="master_admin"))
        assert exc.value.status_code == 404
        assert not db.committed

    def test_lab_admin_from_other_lab_denied_even_same_lab_records(self, monkeypatch):
        db = _FakeDB(_record(1, 2), _record(2, 2))
        user = SimpleNamespace(id=9, role="admin", lab_id=1)
        # Non-platform role bound to lab 1 cannot merge lab 2 records.
        with pytest.raises(HTTPException) as exc:
            _call_merge(db, user)
        assert exc.value.status_code == 403
        assert exc.value.detail["error"] == "cross_lab_access_denied"
        assert not db.committed

    def test_same_lab_merge_succeeds_and_audits(self, monkeypatch):
        calls = []
        monkeypatch.setattr(route, "merge_canonicals",
                            lambda db, **kw: calls.append(kw))
        db = _FakeDB(_record(1, 1), _record(2, 1))
        user = SimpleNamespace(id=9, role="admin", lab_id=1)
        result = _call_merge(db, user)
        assert result.target_id == 1 and result.source_id == 2
        assert calls == [{"target_id": 1, "source_id": 2}]
        assert db.committed

    def test_merge_is_not_silently_unaudited(self, monkeypatch, caplog):
        monkeypatch.setattr(route, "merge_canonicals", lambda db, **kw: None)
        db = _FakeDB(_record(1, 1), _record(2, 1))
        with caplog.at_level(logging.INFO, logger="gula.routes.canonical_patient"):
            _call_merge(db, SimpleNamespace(id=9, role="master_admin", lab_id=None))
        assert any("canonical_merge audit" in r.message for r in caplog.records)
