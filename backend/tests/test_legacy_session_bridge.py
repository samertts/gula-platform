"""NR-135 — a legacy login produces a canonical NIAM session, or nothing.

The runtime proof drives this over real HTTP against PostgreSQL. These tests
pin the decision logic itself, including the cases the happy path never
exercises: an account that exists but may not hold a session, and a legacy row
that is not linked at all.
"""
from __future__ import annotations

import uuid as _uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app._compat import UTC
from app.identity.base import IdentityBase, _ulid
from app.identity.models.account import Account, AccountStatus
from app.identity.models.identity import IdentityRecord
from app.identity.models.legacy_account_link import (
    LegacyAccountLink,
    LegacyAccountLinkSource,
    LegacyAccountLinkStatus,
)
from app.identity.models.person import Person
from app.identity.models.session import UserSession
from app.identity.services.legacy_session_bridge import (
    establish_canonical_session,
    resolve_canonical_account,
    session_expiry,
    terminate_canonical_session,
)

LEGACY_LAB_USER_ID = 41


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    # Only the tables this module touches. Creating the whole IdentityBase
    # metadata fails here: niam_assignments carries a foreign key to
    # `organizations`, which belongs to a different declarative base, so the
    # sort cannot resolve it on a standalone engine.
    IdentityBase.metadata.create_all(
        engine,
        tables=[
            Person.__table__,
            IdentityRecord.__table__,
            Account.__table__,
            LegacyAccountLink.__table__,
            UserSession.__table__,
        ],
    )
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _account(db, *, status=AccountStatus.active.value, is_active=True, is_locked=False):
    person = Person(id=_ulid(), uuid=str(_uuid.uuid4()), given_name="A", family_name="B",
                    is_active=True)
    db.add(person)
    ident = IdentityRecord(id=_ulid(), uuid=str(_uuid.uuid4()), person_id=person.id,
                           identity_type="national_id", status="active",
                           issued_at=datetime.now(UTC), is_active=True)
    db.add(ident)
    account = Account(id=_ulid(), uuid=str(_uuid.uuid4()), identity_id=ident.id,
                      account_type="human", status=status,
                      email=f"{_uuid.uuid4().hex[:8]}@gula.test",
                      is_active=is_active, is_locked=is_locked, failed_login_attempts=0,
                      email_verified=True, phone_verified=False, identity_verified=True)
    db.add(account)
    db.flush()
    return account


def _link(db, account, *, source=LegacyAccountLinkSource.lab_user,
          legacy_id=LEGACY_LAB_USER_ID):
    link = LegacyAccountLink(
        id=_ulid(), source_kind=source.value, legacy_account_id=legacy_id,
        canonical_account_id=account.id if account else None,
        source_fingerprint=_uuid.uuid4().hex,
        status=LegacyAccountLinkStatus.migrated.value, mapping_version=1,
        rollback_token=_uuid.uuid4().hex,
    )
    db.add(link)
    db.flush()
    return link


def test_a_linked_active_account_is_resolved(db):
    account = _account(db)
    _link(db, account)
    resolved = resolve_canonical_account(
        db, legacy_account_id=LEGACY_LAB_USER_ID, account_kind="lab"
    )
    assert resolved is not None, "the positive control must resolve, or the rest proves nothing"
    assert resolved.id == account.id


def test_an_unlinked_legacy_row_resolves_to_nothing(db):
    _account(db)  # exists, but no link points at it
    assert resolve_canonical_account(
        db, legacy_account_id=LEGACY_LAB_USER_ID, account_kind="lab"
    ) is None


def test_a_link_with_no_canonical_account_resolves_to_nothing(db):
    _link(db, None)
    assert resolve_canonical_account(
        db, legacy_account_id=LEGACY_LAB_USER_ID, account_kind="lab"
    ) is None


@pytest.mark.parametrize(
    ("kwargs", "why"),
    [
        ({"status": AccountStatus.suspended.value}, "suspended"),
        ({"status": AccountStatus.disabled.value}, "disabled"),
        ({"status": AccountStatus.pending_verification.value}, "never activated"),
        ({"is_active": False}, "deactivated"),
        ({"is_locked": True}, "locked"),
    ],
)
def test_an_account_that_may_not_hold_a_session_is_refused(db, kwargs, why):
    """Every state the gateway itself rejects is rejected here too.

    If the bridge bound a session for one of these, the token would carry an
    account_uuid the gateway then refuses -- a login that looks canonical and
    is not.
    """
    account = _account(db, **kwargs)
    _link(db, account)
    assert resolve_canonical_account(
        db, legacy_account_id=LEGACY_LAB_USER_ID, account_kind="lab"
    ) is None, f"an account that is {why} must not be resolved"


def test_the_account_kind_selects_the_source_table(db):
    """`lab`/`user` are the token's vocabulary; the link records lab_user/user."""
    account = _account(db)
    _link(db, account, source=LegacyAccountLinkSource.lab_user)
    assert resolve_canonical_account(
        db, legacy_account_id=LEGACY_LAB_USER_ID, account_kind="user"
    ) is None, "a citizen id must not resolve through a lab_user link"
    assert resolve_canonical_account(
        db, legacy_account_id=LEGACY_LAB_USER_ID, account_kind="lab"
    ) is not None


@pytest.mark.parametrize("kind", ["", "admin", "LAB", None, "organization"])
def test_an_unknown_account_kind_resolves_to_nothing(db, kind):
    account = _account(db)
    _link(db, account)
    assert resolve_canonical_account(
        db, legacy_account_id=LEGACY_LAB_USER_ID, account_kind=kind
    ) is None


@pytest.mark.parametrize("legacy_id", [0, -1, None, "1"])
def test_a_non_positive_legacy_id_resolves_to_nothing(db, legacy_id):
    account = _account(db)
    _link(db, account)
    assert resolve_canonical_account(
        db, legacy_account_id=legacy_id, account_kind="lab"
    ) is None


def test_the_session_binds_the_tokens_own_jti(db):
    account = _account(db)
    session = establish_canonical_session(
        db, account=account, access_jti="access-jti-1", refresh_jti="refresh-jti-1",
        expires_at=session_expiry(7), ip_address="203.0.113.9", user_agent="probe",
    )
    assert session.token_jti == "access-jti-1"
    assert session.refresh_token_jti == "refresh-jti-1"
    assert session.account_id == account.id
    assert session.is_active is True
    assert session.expires_at > datetime.now(UTC) + timedelta(days=6)


def test_termination_closes_the_session_for_that_token_only(db):
    account = _account(db)
    keep = establish_canonical_session(
        db, account=account, access_jti="keep", refresh_jti=None,
        expires_at=session_expiry(7),
    )
    drop = establish_canonical_session(
        db, account=account, access_jti="drop", refresh_jti=None,
        expires_at=session_expiry(7),
    )
    assert terminate_canonical_session(db, access_jti="drop", reason="logout") == 1

    assert db.get(UserSession, drop.id).is_active is False
    assert db.get(UserSession, drop.id).termination_reason == "logout"
    assert db.get(UserSession, keep.id).is_active is True, (
        "logging one session out must not close the account's other sessions"
    )


def test_terminating_an_unknown_token_is_a_no_op(db):
    assert terminate_canonical_session(db, access_jti="never-existed", reason="logout") == 0


def test_a_missing_identity_schema_withholds_authority_without_breaking_login():
    """A database error must cost the caller authority, never authentication.

    Measured regression: wiring this lookup into /login made every request
    query niam_legacy_account_links. Against a database that does not have the
    NIAM tables -- a deployment mid-migration, or a test fixture that builds
    only the legacy schema -- the OperationalError propagated and login itself
    failed. 30 passing tests in test_auth_infrastructure.py became 6 passing
    and 24 errors.

    The right outcome is the one that already applies when no link exists: no
    canonical account, so no account_uuid, so the NIAM-protected surface
    refuses the token. An error can withhold authority; it must not grant any,
    and it must not turn a missing table into an outage.
    """
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    # Deliberately create NOTHING: this is the schema-absent case.
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        assert resolve_canonical_account(
            session, legacy_account_id=LEGACY_LAB_USER_ID, account_kind="lab"
        ) is None
    finally:
        session.close()
        engine.dispose()
