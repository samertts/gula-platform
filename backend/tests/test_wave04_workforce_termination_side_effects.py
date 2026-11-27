"""Wave 04 — workforce termination revokes authoritative state and sessions.

Synthetic in-memory objects only. Verifies that terminating a workforce request
also ends active Employment rows and active NIAM sessions for the same person,
so no old account/token can retain access. No new authorization engine or
schema is involved.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from types import SimpleNamespace

from app._compat import UTC
from app.identity.lifecycle.services import WorkforceService
from app.identity.models.account import Account
from app.identity.models.employment import Employment, EmploymentStatus
from app.identity.models.identity import IdentityRecord
from app.identity.models.session import UserSession


class _Query:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *_args, **_kwargs):
        return self

    def all(self):
        return list(self.rows)

    def first(self):
        return self.rows[0] if self.rows else None


class _Db:
    def __init__(self, req, employments, identities, accounts, sessions):
        self.tables = {
            "WorkforceRequest": [req],
            Employment: employments,
            IdentityRecord: identities,
            Account: accounts,
            UserSession: sessions,
        }
        self.flushes = 0

    def query(self, model):
        if model.__name__ == "WorkforceRequest":
            return _Query(self.tables["WorkforceRequest"])
        rows = list(self.tables.get(model, []))
        # Production filters these queries on is_active IS TRUE; mirror that so
        # the fake does not mutate rows the real query would never return.
        if model in (Employment, UserSession):
            rows = [row for row in rows if row.is_active is True]
        return _Query(rows)

    def flush(self):
        self.flushes += 1


def _request():
    return SimpleNamespace(
        request_id="REQ-W04-TERM",
        person_id="PERSON-W04",
        termination_reason=None,
        status="activated",
        is_active=True,
    )


def _employment(status="active", is_active=True):
    return SimpleNamespace(
        person_id="PERSON-W04",
        status=status,
        is_active=is_active,
        end_date=None,
        termination_date=None,
        termination_reason=None,
    )


def _session(is_active=True):
    return SimpleNamespace(
        account_id="ACCOUNT-W04",
        is_active=is_active,
        terminated_at=None,
        termination_reason=None,
    )


def test_termination_revokes_employment_and_sessions():
    req = _request()
    employment = _employment()
    session = _session()
    db = _Db(
        req=req,
        employments=[employment],
        identities=[SimpleNamespace(id="IDENTITY-W04", person_id="PERSON-W04")],
        accounts=[SimpleNamespace(id="ACCOUNT-W04", identity_id="IDENTITY-W04")],
        sessions=[session],
    )

    result = WorkforceService().terminate_employment(db, req.request_id, "contract_end")

    assert result is req
    assert req.status == "terminated"
    assert req.is_active is False
    assert employment.status == EmploymentStatus.terminated.value
    assert employment.is_active is False
    assert employment.end_date == date.today()
    assert employment.termination_date == date.today()
    assert employment.termination_reason == "contract_end"
    assert session.is_active is False
    assert session.termination_reason == "employment_terminated"
    assert session.terminated_at is not None


def test_termination_is_idempotent_and_leaves_inactive_rows_untouched():
    req = _request()
    already_ended = _employment(status="terminated", is_active=False)
    live = _employment()
    old_session = _session(is_active=False)
    live_session = _session()
    db = _Db(
        req=req,
        employments=[already_ended, live],
        identities=[SimpleNamespace(id="IDENTITY-W04", person_id="PERSON-W04")],
        accounts=[SimpleNamespace(id="ACCOUNT-W04", identity_id="IDENTITY-W04")],
        sessions=[old_session, live_session],
    )

    WorkforceService().terminate_employment(db, req.request_id, "security")

    assert already_ended.end_date is None  # inactive row was not rewritten
    assert live.status == EmploymentStatus.terminated.value
    assert old_session.termination_reason is None  # already inactive
    assert live_session.is_active is False


def test_termination_without_linked_person_does_not_touch_other_workforce():
    req = _request()
    req.person_id = None
    other = _employment()
    other_session = _session()
    db = _Db(
        req=req,
        employments=[other],
        identities=[],
        accounts=[],
        sessions=[other_session],
    )

    WorkforceService().terminate_employment(db, req.request_id, "admin")

    assert other.status == "active"
    assert other_session.is_active is True
