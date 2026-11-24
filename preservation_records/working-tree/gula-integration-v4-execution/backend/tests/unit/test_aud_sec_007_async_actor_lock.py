"""AUD-SEC-007 — async NIAM actor must enforce the account-lock check.

The auditor found that ``get_current_niam_actor_sync`` filtered on
``Account.is_locked.is_(False)`` but the async variant ``get_current_niam_actor``
(which guards every async NIAM route) omitted it. A locked account could therefore
keep using all async NIAM routes until token expiry.

Falsification axes:
1. The async query must carry an equivalent fail-closed lock predicate.
2. A real, otherwise-active but LOCKED account must be rejected by the async actor
   dependency; an unlocked account must still authenticate.
3. Sync and async must share ONE predicate definition (no future drift).
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from app.identity.api import workspaces as workspace_api
from app.identity.models.account import Account
from app.identity.models.session import UserSession
from fastapi import HTTPException
from sqlalchemy import create_engine


def _request():
    return SimpleNamespace(cookies={})


class _Credentials:
    def __init__(self, token: str):
        self.credentials = token


class _Result:
    def __init__(self, row):
        self._row = row

    def first(self):
        return self._row


class _CapturingAsyncDb:
    """Executes the REAL statement against SQLite and records it for inspection."""

    def __init__(self, engine):
        self.engine = engine
        self.statement = None

    async def execute(self, statement):
        from sqlalchemy.orm import Session

        self.statement = statement
        with Session(self.engine) as session:
            rows = session.execute(statement).all()
        return _Result(rows[0] if rows else None)


def _sql(statement) -> str:
    return str(statement.compile(compile_kwargs={"literal_binds": True})).lower()


@pytest.fixture()
def sqlite_db():
    """Two active accounts — one locked, one unlocked — with matching sessions."""
    engine = create_engine("sqlite:///:memory:")
    Account.__table__.create(engine)
    UserSession.__table__.create(engine)
    now = datetime.now(UTC)
    with engine.begin() as conn:
        for suffix, locked in (("open", False), ("locked", True)):
            conn.execute(
                Account.__table__.insert().values(
                    id=f"acct-{suffix}",
                    uuid=f"uuid-{suffix}",
                    identity_id=f"ident-{suffix}",
                    account_type="human",
                    status="active",
                    is_active=True,
                    is_locked=locked,
                    email=f"{suffix}@test.invalid",
                )
            )
            conn.execute(
                UserSession.__table__.insert().values(
                    id=f"sess-{suffix}",
                    uuid=f"sessuuid-{suffix}",
                    account_id=f"acct-{suffix}",
                    token_jti=f"jti-{suffix}",
                    session_type="web",
                    is_active=True,
                    started_at=now,
                    last_activity_at=now,
                    expires_at=now + timedelta(days=1),
                )
            )
    return engine


class TestAsyncActorLockEnforcement:
    @pytest.mark.asyncio
    async def test_locked_active_account_is_rejected(self, monkeypatch, sqlite_db):
        """The exact auditor falsification: a locked account must not authenticate."""
        monkeypatch.setattr(
            workspace_api,
            "decode_token",
            lambda token: {"jti": "jti-locked", "account_uuid": "uuid-locked"},
        )
        db = _CapturingAsyncDb(sqlite_db)

        with pytest.raises(HTTPException) as exc:
            await workspace_api.get_current_niam_actor(_request(), _Credentials("t"), db)

        assert exc.value.status_code == 401
        assert "is_locked" in _sql(db.statement), "async query omits the account-lock predicate"

    @pytest.mark.asyncio
    async def test_unlocked_active_account_still_authenticates(self, monkeypatch, sqlite_db):
        """Backward compatibility: the lock check must not reject valid actors."""
        monkeypatch.setattr(
            workspace_api,
            "decode_token",
            lambda token: {"jti": "jti-open", "account_uuid": "uuid-open"},
        )
        db = _CapturingAsyncDb(sqlite_db)
        actor = await workspace_api.get_current_niam_actor(_request(), _Credentials("t"), db)
        assert actor.account.id == "acct-open"
        assert actor.session.id == "sess-open"
        assert "is_locked" in _sql(db.statement)

    def test_sync_and_async_share_one_predicate_definition(self):
        """A single helper must carry the lock predicate for both dependencies."""
        preds = workspace_api._active_niam_actor_predicates("uuid-x", "jti-x")
        compiled = [_sql(p) for p in preds]
        assert any("is_locked" in c for c in compiled), "shared predicate lacks the lock check"
        # The strict form rejects NULL as well as TRUE (IS FALSE == only FALSE matches).
        assert any("is false" in c or "= 0" in c for c in compiled)

    def test_both_dependencies_reference_the_shared_helper(self):
        """Guard against a future re-introduction of duplicated query logic."""
        import inspect

        src_sync = inspect.getsource(workspace_api.get_current_niam_actor_sync)
        src_async = inspect.getsource(workspace_api.get_current_niam_actor)
        assert "_active_niam_actor_predicates" in src_sync
        assert "_active_niam_actor_predicates" in src_async
        assert "is_locked" not in src_sync.replace(" ", "")
        assert "is_locked" not in src_async.replace(" ", "")
