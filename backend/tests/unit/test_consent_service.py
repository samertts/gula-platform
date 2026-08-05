"""Unit tests for consent_service — grant, revoke, check, access decision audit."""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from unittest.mock import patch

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import pytest
from app._compat import UTC
from app.database import Base
from app.models.consent import Consent
from app.services import consent_service
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ─── _ulid ─────────────────────────────────────────────────────────────────────


def test_ulid_is_26_char_crockford():
    u = consent_service._ulid()
    assert len(u) == 26
    assert all(c in consent_service._CROCKFORD for c in u)


def test_ulid_unique():
    ids = {consent_service._ulid() for _ in range(200)}
    assert len(ids) == 200


# ─── Policy constants ──────────────────────────────────────────────────────────


def test_allowed_scopes_have_no_wildcards():
    for scope in consent_service.ALLOWED_SCOPES:
        assert "*" not in scope
        assert scope.count(":") == 1
        verb, resource = scope.split(":")
        assert verb in {"read", "write"}
        assert resource


def test_max_consent_hours_cap():
    assert consent_service.MAX_CONSENT_HOURS == 72


# ─── grant_consent ─────────────────────────────────────────────────────────────


def test_grant_consent_creates_active_row(db_session):
    with patch("app.services.consent_service.log_action") as log:
        row = consent_service.grant_consent(
            db_session,
            gpid="GPID1",
            grantee_id="GRANTEE1",
            scope="read:patient",
            expires_in_hours=24,
            actor_user_id=1,
            actor_role="admin",
        )

    assert row.status == "active"
    assert row.gpid == "GPID1"
    assert row.grantee_id == "GRANTEE1"
    assert row.scope == "read:patient"
    assert row.expires_at > datetime.now(UTC)
    log.assert_called_once()
    assert log.call_args.kwargs["action"] == "consent_grant"


def test_grant_consent_rejects_disallowed_scope(db_session):
    with pytest.raises(consent_service.ConsentError):
        consent_service.grant_consent(
            db_session, gpid="G", grantee_id="R", scope="delete:everything",
            expires_in_hours=1,
        )


def test_grant_consent_rejects_wildcard_scope(db_session):
    with pytest.raises(consent_service.ConsentError):
        consent_service.grant_consent(
            db_session, gpid="G", grantee_id="R", scope="read:*",
            expires_in_hours=1,
        )


def test_grant_consent_rejects_nonpositive_duration(db_session):
    with pytest.raises(consent_service.ConsentError):
        consent_service.grant_consent(
            db_session, gpid="G", grantee_id="R", scope="read:patient",
            expires_in_hours=0,
        )


def test_grant_consent_rejects_duration_over_cap(db_session):
    with pytest.raises(consent_service.ConsentError):
        consent_service.grant_consent(
            db_session, gpid="G", grantee_id="R", scope="read:patient",
            expires_in_hours=consent_service.MAX_CONSENT_HOURS + 1,
        )


def test_grant_consent_rejects_empty_identifiers(db_session):
    with pytest.raises(consent_service.ConsentError):
        consent_service.grant_consent(
            db_session, gpid="", grantee_id="R", scope="read:patient",
            expires_in_hours=1,
        )


def test_grant_consent_revokes_previous_active(db_session):
    with patch("app.services.consent_service.log_action"):
        first = consent_service.grant_consent(
            db_session, gpid="G", grantee_id="R", scope="read:patient",
            expires_in_hours=24,
        )
        second = consent_service.grant_consent(
            db_session, gpid="G", grantee_id="R", scope="read:patient",
            expires_in_hours=24,
        )

    db_session.flush()
    first_row = db_session.get(Consent, first.id)
    assert first_row.status == "revoked"
    assert first_row.revoked_at is not None
    assert second.id != first.id
    assert second.status == "active"


# ─── check_active_consent ──────────────────────────────────────────────────────


def test_check_active_consent_returns_row(db_session):
    with patch("app.services.consent_service.log_action"):
        consent_service.grant_consent(
            db_session, gpid="G", grantee_id="R", scope="read:patient",
            expires_in_hours=24,
        )

    row = consent_service.check_active_consent(
        db_session, gpid="G", grantee_id="R", scope="read:patient",
    )
    assert row is not None
    assert row.status == "active"


def test_check_active_consent_none_when_missing(db_session):
    row = consent_service.check_active_consent(
        db_session, gpid="G", grantee_id="R", scope="read:patient",
    )
    assert row is None


def test_check_active_consent_none_for_revoked(db_session):
    with patch("app.services.consent_service.log_action"):
        consent_service.grant_consent(
            db_session, gpid="G", grantee_id="R", scope="read:patient",
            expires_in_hours=24,
        )
        consent_service.revoke_consent(
            db_session, gpid="G", grantee_id="R", scope="read:patient",
        )

    assert (
        consent_service.check_active_consent(
            db_session, gpid="G", grantee_id="R", scope="read:patient",
        )
        is None
    )


def test_check_active_consent_expired_row_lazily_marked(db_session):
    past = datetime.now(UTC) - timedelta(hours=2)
    row = Consent(
        id=consent_service._ulid(),
        gpid="G",
        grantee_id="R",
        scope="read:patient",
        status="active",
        expires_at=past,
        created_at=past - timedelta(hours=1),
    )
    db_session.add(row)
    db_session.flush()

    result = consent_service.check_active_consent(
        db_session, gpid="G", grantee_id="R", scope="read:patient",
    )
    assert result is None
    db_session.flush()
    db_session.refresh(row)
    assert row.status == "expired"


def test_check_active_consent_different_scope(db_session):
    with patch("app.services.consent_service.log_action"):
        consent_service.grant_consent(
            db_session, gpid="G", grantee_id="R", scope="read:patient",
            expires_in_hours=24,
        )

    assert (
        consent_service.check_active_consent(
            db_session, gpid="G", grantee_id="R", scope="read:orders",
        )
        is None
    )


# ─── revoke_consent ────────────────────────────────────────────────────────────


def test_revoke_consent_returns_true(db_session):
    with patch("app.services.consent_service.log_action"):
        consent_service.grant_consent(
            db_session, gpid="G", grantee_id="R", scope="read:patient",
            expires_in_hours=24,
        )

    with patch("app.services.consent_service.log_action") as log:
        result = consent_service.revoke_consent(
            db_session, gpid="G", grantee_id="R", scope="read:patient",
        )

    assert result is True
    log.assert_called_once()
    assert log.call_args.kwargs["action"] == "consent_revoke"


def test_revoke_consent_idempotent(db_session):
    with patch("app.services.consent_service.log_action"):
        consent_service.grant_consent(
            db_session, gpid="G", grantee_id="R", scope="read:patient",
            expires_in_hours=24,
        )
        assert consent_service.revoke_consent(
            db_session, gpid="G", grantee_id="R", scope="read:patient",
        ) is True
        assert consent_service.revoke_consent(
            db_session, gpid="G", grantee_id="R", scope="read:patient",
        ) is False


def test_revoke_consent_no_active_row_returns_false(db_session):
    result = consent_service.revoke_consent(
        db_session, gpid="G", grantee_id="R", scope="read:patient",
    )
    assert result is False


# ─── log_access_decision ───────────────────────────────────────────────────────


def test_log_access_decision_allow():
    with patch("app.services.consent_service.log_action") as log:
        consent_service.log_access_decision(
            None,  # db unused — mocked audit
            actor_user_id=1,
            actor_role="doctor",
            gpid="G",
            scope="read:patient",
            result="allow",
            reason="active_consent",
            emergency=False,
            ip_address="10.0.0.1",
        )

    log.assert_called_once()
    assert log.call_args.kwargs["action"] == "consent_check_allow"
    assert log.call_args.kwargs["user_id"] == 1
    assert log.call_args.kwargs["user_role"] == "doctor"
    assert "result=allow" in log.call_args.kwargs["details"]


def test_log_access_decision_deny():
    with patch("app.services.consent_service.log_action") as log:
        consent_service.log_access_decision(
            None,
            actor_user_id=2,
            actor_role="nurse",
            gpid="G",
            scope="read:orders",
            result="deny",
            reason="no_consent",
        )

    assert log.call_args.kwargs["action"] == "consent_check_deny"
    assert log.call_args.kwargs["details"].startswith("gpid=G scope=read:orders")
