"""Consent layer — the 5 must-pass production tests.

Covers the governing access rules:
  1. no consent → deny
  2. valid consent → allow
  3. expired consent → deny
  4. emergency break-glass (doctor) → allow + audit flag
  5. revoke → immediate block

The tests hit the service layer + the FastAPI dependency directly, not a
full TestClient, because the dependency is the single source of truth for
access control and we want to isolate it from route wiring churn.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from app._compat import UTC

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///test_consent.db")
os.environ.setdefault("SECRET_KEY", "test-secret-consent-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

import pytest
from app.database import Base
from app.models.audit_log import AuditLog
from app.models.consent import Consent
from app.models.lab_user import LabUser
from app.orm_topology import own_tables
from app.security.consent_dep import require_consent
from app.services import consent_service
from app.services.mpi.models import Citizen, IdentityClaim
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── In-memory test DB ─────────────────────────────────────────────────────────

@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:",
                           connect_args={"check_same_thread": False})
    # Create only the tables we need; bulk metadata.create_all may pull in
    # tables with FKs we don't care about — but Consent has an FK to
    # lab_users, so we create all to satisfy it.
    Base.metadata.create_all(engine, tables=own_tables(Base))
    Session = sessionmaker(bind=engine)
    s = Session()
    try:
        yield s
    finally:
        s.close()


def _make_request(user_role: str = "doctor", user_id: int = 42,
                  emergency: bool = False, citizen_ulid: str = "01CITIZEN000000000000000ZZ"):
    """Fabricate a minimal FastAPI Request stand-in for the dependency."""
    headers = {}
    if emergency:
        headers["X-Emergency-Access"] = "true"

    request = MagicMock()
    request.headers = headers
    request.path_params = {"citizen_ulid": citizen_ulid}
    request.client = SimpleNamespace(host="127.0.0.1")
    return request


def _make_user(role: str = "doctor", user_id: int = 42, citizen_ulid=None):
    """LabUser stand-in — the dep only touches .id, .role, .citizen_ulid."""
    u = SimpleNamespace()
    u.id = user_id
    u.role = role
    if citizen_ulid is not None:
        u.citizen_ulid = citizen_ulid
    return u


# ── TEST 1: no consent → 403 ─────────────────────────────────────────────────

def test_no_consent_denies(db):
    dep = require_consent("read:citizen")
    with pytest.raises(HTTPException) as exc:
        dep(request=_make_request(),
            current_user=_make_user(),
            db=db)
    assert exc.value.status_code == 403
    assert exc.value.detail["error"] == "consent_required"


# ── TEST 2: valid consent → allow ────────────────────────────────────────────

def test_valid_consent_allows(db):
    consent_service.grant_consent(
        db,
        gpid="01CITIZEN000000000000000ZZ",
        grantee_id="user:42",
        scope="read:citizen",
        expires_in_hours=24,
        actor_user_id=42,
        actor_role="citizen",
    )
    db.commit()

    dep = require_consent("read:citizen")
    result = dep(request=_make_request(),
                 current_user=_make_user(),
                 db=db)
    assert result.id == 42


# ── TEST 3: expired consent → 403 ────────────────────────────────────────────

def test_expired_consent_denies(db):
    # Insert directly with expires_at in the past (bypasses API 72h cap)
    row = Consent(
        id="01EXPIREDCONSENT000000000A",
        gpid="01CITIZEN000000000000000ZZ",
        grantee_id="user:42",
        scope="read:citizen",
        status="active",
        expires_at=datetime.now(UTC) - timedelta(minutes=5),
        created_at=datetime.now(UTC) - timedelta(hours=2),
    )
    db.add(row)
    db.commit()

    dep = require_consent("read:citizen")
    with pytest.raises(HTTPException) as exc:
        dep(request=_make_request(),
            current_user=_make_user(),
            db=db)
    assert exc.value.status_code == 403

    # The service should have lazily flipped status to 'expired'
    db.refresh(row)
    assert row.status == "expired"


# ── TEST 4: emergency break-glass (doctor) → allow + audit ───────────────────

def test_emergency_break_glass_allows_doctor(db):
    dep = require_consent("read:citizen")
    result = dep(request=_make_request(emergency=True),
                 current_user=_make_user(role="doctor"),
                 db=db)
    assert result.id == 42

    # Audit row must have been written with emergency=True in details
    audits = db.query(AuditLog).filter(
        AuditLog.action == "consent_check_allow",
    ).all()
    assert len(audits) == 1
    assert "emergency=True" in audits[0].details


def test_emergency_break_glass_rejects_non_doctor(db):
    dep = require_consent("read:citizen")
    with pytest.raises(HTTPException) as exc:
        dep(request=_make_request(emergency=True),
            current_user=_make_user(role="staff"),
            db=db)
    assert exc.value.status_code == 403


# ── TEST 5: revoke → immediate block ─────────────────────────────────────────

def test_revoke_immediately_blocks(db):
    consent_service.grant_consent(
        db,
        gpid="01CITIZEN000000000000000ZZ",
        grantee_id="user:42",
        scope="read:citizen",
        expires_in_hours=24,
        actor_user_id=42,
        actor_role="citizen",
    )
    db.commit()

    # First access allowed
    dep = require_consent("read:citizen")
    dep(request=_make_request(), current_user=_make_user(), db=db)

    consent_service.revoke_consent(
        db,
        gpid="01CITIZEN000000000000000ZZ",
        grantee_id="user:42",
        scope="read:citizen",
        actor_user_id=42,
        actor_role="citizen",
    )
    db.commit()

    # Subsequent access denied
    with pytest.raises(HTTPException) as exc:
        dep(request=_make_request(),
            current_user=_make_user(),
            db=db)
    assert exc.value.status_code == 403
    assert exc.value.detail["error"] == "consent_required"


# ── Additional: owner bypass ─────────────────────────────────────────────────

def test_owner_bypasses_consent(db):
    dep = require_consent("read:citizen")
    user = _make_user(role="citizen", user_id=7,
                      citizen_ulid="01CITIZEN000000000000000ZZ")
    result = dep(request=_make_request(), current_user=user, db=db)
    assert result.id == 7


# ── Additional: scope + duration policy ──────────────────────────────────────

def test_grant_rejects_disallowed_scope(db):
    with pytest.raises(consent_service.ConsentError):
        consent_service.grant_consent(
            db,
            gpid="01CITIZEN000000000000000ZZ",
            grantee_id="user:42",
            scope="read:everything",   # wildcard-ish, not in ALLOWED_SCOPES
            expires_in_hours=1,
        )


def test_grant_rejects_over_72h(db):
    with pytest.raises(consent_service.ConsentError):
        consent_service.grant_consent(
            db,
            gpid="01CITIZEN000000000000000ZZ",
            grantee_id="user:42",
            scope="read:citizen",
            expires_in_hours=73,
        )
