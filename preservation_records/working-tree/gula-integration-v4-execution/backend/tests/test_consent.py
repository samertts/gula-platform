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
from app.models.authorization import BreakGlassSession
from app.models.consent import Consent
from app.models.lab_user import LabUser
from app.models.patient import Patient
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
    Base.metadata.create_all(engine)
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


_GPID = "01CITIZEN000000000000000ZZ"
_VALID_JUSTIFICATION = "Patient in cardiac arrest; immediate record access required for life-saving care."


def _activate_break_glass(db, *, user_id: int = 42, gpid: str = _GPID,
                          category: str = "patient_critical", patient_id: int | None = None,
                          claim_patient_id: int | None = None,
                          justification: str = _VALID_JUSTIFICATION,
                          expires_in: timedelta = timedelta(minutes=30),
                          status: str = "active",
                          deactivated: bool = False):
    """Create synthetic MPI linkage + a server-side BreakGlassSession.

    ``claim_patient_id`` is the subject's MPI-linked local patient;
    ``patient_id`` is the patient the session is scoped to. They differ only in
    the wrong-patient adversarial test. SQLite FKs are off in this fixture, so
    a placeholder lab_id is sufficient.
    """
    citizen = Citizen(
        citizen_ulid=gpid, name_canonical="Synthetic Citizen",
        name_blocking_key="SYN", status="active", nid_verified=False,
    )
    db.add(citizen)
    db.flush()
    if claim_patient_id is None:
        claim_patient_id = patient_id
    if claim_patient_id is None:
        patient = Patient(lab_id=1, full_name="Synthetic Patient", phone="07900000000")
        db.add(patient)
        db.flush()
        claim_patient_id = patient.id
    if patient_id is None:
        patient_id = claim_patient_id
    db.add(IdentityClaim(
        citizen_id=citizen.id, lab_id=1, local_patient_id=claim_patient_id,
        match_method="nid_exact",
    ))
    now = datetime.now(UTC)
    session = BreakGlassSession(
        user_id=user_id, emergency_category=category, justification=justification,
        patient_id=patient_id, started_at=now, expires_at=now + expires_in,
        status=status,
        deactivated_at=now if deactivated else None,
    )
    db.add(session)
    db.commit()
    return session


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


# ── TEST 4: server-verified break-glass → allow + audit ──────────────────────

def test_verified_break_glass_allows_eligible_clinician(db):
    _activate_break_glass(db, user_id=42)
    dep = require_consent("read:citizen")
    result = dep(request=_make_request(emergency=True),
                 current_user=_make_user(role="doctor"),
                 db=db)
    assert result.id == 42

    audits = db.query(AuditLog).filter(
        AuditLog.action == "consent_check_allow",
    ).all()
    assert len(audits) == 1
    assert "emergency=True" in audits[0].details
    assert "break_glass_verified" in audits[0].details


def test_verified_break_glass_rejects_non_clinical_role(db):
    _activate_break_glass(db, user_id=42)
    dep = require_consent("read:citizen")
    with pytest.raises(HTTPException) as exc:
        dep(request=_make_request(emergency=True),
            current_user=_make_user(role="staff"),
            db=db)
    assert exc.value.status_code == 403
    assert exc.value.detail["error"] == "break_glass_denied"
    assert exc.value.detail["reason"] == "ineligible_role"


def test_forged_emergency_header_without_session_denied(db):
    """The exact prior bypass (header + doctor role) must no longer work."""
    dep = require_consent("read:citizen")
    with pytest.raises(HTTPException) as exc:
        dep(request=_make_request(emergency=True),
            current_user=_make_user(role="doctor"),
            db=db)
    assert exc.value.status_code == 403
    assert exc.value.detail["error"] == "break_glass_denied"
    assert exc.value.detail["reason"] == "no_active_break_glass_session"
    audits = db.query(AuditLog).filter(AuditLog.action == "consent_check_deny").all()
    assert any("break_glass_denied" in a.details for a in audits)


def test_break_glass_never_creates_consent(db):
    """Consent and break-glass are separate: no Consent row is created."""
    _activate_break_glass(db, user_id=42)
    dep = require_consent("read:citizen")
    dep(request=_make_request(emergency=True),
        current_user=_make_user(role="doctor"), db=db)
    assert db.query(Consent).filter(Consent.gpid == _GPID).count() == 0


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    [
        ({"expires_in": timedelta(minutes=-5)}, "break_glass_expired"),
        ({"deactivated": True}, "break_glass_deactivated"),
        ({"status": "deactivated"}, "no_active_break_glass_session"),
        ({"justification": "too short"}, "justification_too_short"),
        ({"category": "arbitrary_client_value"}, "invalid_emergency_category"),
    ],
)
def test_invalid_break_glass_sessions_denied(db, overrides, expected_reason):
    _activate_break_glass(db, user_id=42, **overrides)
    dep = require_consent("read:citizen")
    with pytest.raises(HTTPException) as exc:
        dep(request=_make_request(emergency=True),
            current_user=_make_user(role="doctor"), db=db)
    assert exc.value.status_code == 403
    assert exc.value.detail["reason"] == expected_reason


def test_break_glass_for_wrong_patient_denied(db):
    """A session bound to a different subject cannot access this subject."""
    subject_patient = Patient(lab_id=1, full_name="Subject Patient", phone="07900000002")
    other_patient = Patient(lab_id=1, full_name="Other Patient", phone="07900000001")
    db.add(subject_patient)
    db.add(other_patient)
    db.flush()
    _activate_break_glass(
        db, user_id=42,
        claim_patient_id=subject_patient.id,
        patient_id=other_patient.id,  # session scoped to the wrong subject
    )
    dep = require_consent("read:citizen")
    with pytest.raises(HTTPException) as exc:
        dep(request=_make_request(emergency=True),
            current_user=_make_user(role="doctor"), db=db)
    assert exc.value.detail["reason"] == "subject_not_in_break_glass_scope"


def test_break_glass_session_for_another_actor_denied(db):
    _activate_break_glass(db, user_id=99)  # session belongs to user 99
    dep = require_consent("read:citizen")
    with pytest.raises(HTTPException) as exc:
        dep(request=_make_request(emergency=True),
            current_user=_make_user(role="doctor", user_id=42), db=db)
    assert exc.value.detail["reason"] == "no_active_break_glass_session"


def test_non_read_scope_ineligible_for_break_glass(db):
    _activate_break_glass(db, user_id=42)
    dep = require_consent("export:citizen")
    with pytest.raises(HTTPException) as exc:
        dep(request=_make_request(emergency=True),
            current_user=_make_user(role="doctor"), db=db)
    assert exc.value.detail["reason"] == "scope_ineligible_for_break_glass"


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


# ── B2: activation-time policy validation (defense in depth) ──────────────────

def test_activation_policy_accepts_valid_request():
    from app.security.break_glass_guard import validate_break_glass_activation

    validate_break_glass_activation(
        role="doctor", emergency_category="patient_critical",
        justification=_VALID_JUSTIFICATION, patient_id=1, duration_minutes=60,
    )


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"role": "staff"}, "ineligible_role"),
        ({"emergency_category": "because_i_want_to"}, "invalid_emergency_category"),
        ({"justification": "short"}, "justification_too_short"),
        ({"patient_id": None}, "patient_id_required"),
        ({"duration_minutes": 9999}, "invalid_duration"),
        ({"duration_minutes": 0}, "invalid_duration"),
    ],
)
def test_activation_policy_rejects_invalid_requests(kwargs, reason):
    from app.security.break_glass_guard import validate_break_glass_activation

    values = {
        "role": "doctor", "emergency_category": "patient_critical",
        "justification": _VALID_JUSTIFICATION, "patient_id": 1, "duration_minutes": 60,
    }
    values.update(kwargs)
    with pytest.raises(ValueError, match=reason):
        validate_break_glass_activation(**values)
