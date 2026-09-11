"""AUTH-005: identity evidence, not account control, gates health-data linkage.

The boundary these tests defend is the one that matters most in a health
platform: proving you control an account is not proving who you are, and being
authorized to perform an operation is not evidence about the subject of it.

Before AUTH-005, `CitizenRelationshipService.activate` — which links an account
to a citizen and a patient, with a scope — refused unless the source account was
"active and verified", reading the boolean that an emailed six-digit code sets
(NR-039). And `POST /niam/trust/assurance-profiles` accepted the assurance level,
the assessor and the evidence from the caller (NR-038).
"""

from __future__ import annotations

import os
import pathlib
import uuid
from datetime import (
    datetime,
    timedelta,
)
from types import SimpleNamespace

import pytest
from app._compat import UTC
from app.identity.models.account import Account, AccountStatus
from app.identity.models.identity import IdentityRecord
from app.identity.models.legacy_account_link import (
    LegacyAccountLink,
    LegacyAccountLinkSource,
    LegacyAccountLinkStatus,
)
from app.identity.models.person import Person
from app.identity.models.verification_record import VerificationRecordStatus
from app.identity.services.identity_link_policy import (
    IDENTITY_LINK_MINIMUM,
    can_link_health_identity,
    resolve_canonical_account,
)
from app.identity.services.verification_service import (
    AssuranceLevel,
    VerificationMethod,
    VerificationPurpose,
    VerificationResult,
    VerificationStatus,
)
from app.identity.services.verification_workflow import (
    VerificationWorkflow,
    VerificationWorkflowError,
)
from app.models.user import User
from fastapi import HTTPException
from sqlalchemy import String as sqlalchemy_String
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def _now():
    return datetime.now(UTC)


# These tables are migration-backed and are deliberately absent from conftest's
# create_all: TEST-001 established that a green test must never mean "the ORM
# can create this table". The identity platform's tables therefore come from the
# migrated PostgreSQL database CI already builds, or the suite skips.
SCHEMA_DATABASE_URL = (
    os.environ.get("GULA_SCHEMA_DATABASE_URL")
    or os.environ.get("MIGRATION_DATABASE_URL", "")
)
pytestmark = pytest.mark.skipif(
    not SCHEMA_DATABASE_URL,
    reason="GULA_SCHEMA_DATABASE_URL/MIGRATION_DATABASE_URL is not configured",
)


@pytest.fixture(scope="module")
def engine():
    eng = create_engine(SCHEMA_DATABASE_URL, future=True)
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture()
def db(engine):
    """A session on the migrated schema, rolled back so tests cannot leak."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, future=True)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


def _identity_chain(db, suffix: str) -> str:
    """Person -> Identity, the rows a canonical Account requires.

    Creating these inside a rolled-back test transaction is test data, not a
    backfill: AUTH-F10 forbids asserting a Person for *existing production
    accounts* without proofing, which is a different act entirely.
    """
    db.add(Person(
        id=f"person-{suffix}", uuid=str(uuid.uuid4()),
        given_name="Link", family_name="Subject",
        is_deceased=False, is_active=True,
    ))
    # Flush between the two: the FK is a plain column, so SQLAlchemy cannot
    # infer the insert order from a relationship it does not have.
    db.flush()
    db.add(IdentityRecord(
        id=f"ident-{suffix}", uuid=str(uuid.uuid4()), person_id=f"person-{suffix}",
        identity_type="citizen", status="active", issued_at=_now(), is_active=True,
    ))
    db.flush()
    return f"ident-{suffix}"


def _linked_account(db, *, suffix: str, legacy_id: int) -> Account:
    identity_id = _identity_chain(db, suffix)
    acct = Account(
        id=f"acct-{suffix}", uuid=str(uuid.uuid4()), identity_id=identity_id,
        status=AccountStatus.active.value, is_active=True, is_locked=False,
    )
    db.add(acct)
    db.flush()
    db.add(LegacyAccountLink(
        source_kind=LegacyAccountLinkSource.user.value,
        legacy_account_id=legacy_id,
        canonical_account_id=acct.id,
        source_fingerprint=f"fp-{suffix}",
        status=LegacyAccountLinkStatus.validated.value,
        rollback_token=uuid.uuid4().hex,
    ))
    db.flush()
    return acct


@pytest.fixture()
def account(db):
    """A canonical account with a validated mapping from a legacy `users` row."""
    db.add(User(
        id=880051, full_name="Link Subject", email="link-subject@example.invalid",
        phone="07800510000", password_hash="!x", role="citizen",
        is_active=True, is_verified=True,   # contact verified — the NR-039 input
    ))
    db.flush()
    return _linked_account(db, suffix="auth005-1", legacy_id=880051)


def _verify(db, account_id, method, *, identity_id="ident-auth005-1"):
    """Drive a verification to `verified` through the real state machine."""
    flow = VerificationWorkflow(db)
    record = flow.request(
        account_id=account_id, identity_id=identity_id,
        method=method, provider="auth005-test-provider",
    )
    flow.start(record)
    flow.apply(record, VerificationResult(
        status=VerificationStatus.verified, assurance=AssuranceLevel.L3,
        provider="auth005-test-provider", method=method,
        provider_reference="opaque-ref",
    ))
    db.flush()
    return record


# ── NR-040: the architecture now has a writer ────────────────────────────────


def test_the_workflow_creates_records_through_the_real_state_machine(db, account) -> None:
    record = _verify(db, account.id, VerificationMethod.email)
    assert record.status == VerificationRecordStatus.verified.value
    assert record.record_type == "contact"
    assert record.verification_session_id
    assert record.completed_at is not None


def test_the_provider_does_not_grade_its_own_work(db, account) -> None:
    """The provider claimed L3 for an emailed code. The policy says L1."""
    record = _verify(db, account.id, VerificationMethod.email)
    assert record.assurance_level == AssuranceLevel.L1.value


def test_a_result_cannot_answer_a_record_opened_for_another_method(db, account) -> None:
    """The purpose is fixed when the record opens; the answer cannot move it."""
    flow = VerificationWorkflow(db)
    record = flow.request(
        account_id=account.id, identity_id="ident-auth005-1",
        method=VerificationMethod.official_identity, provider="p",
    )
    flow.start(record)
    with pytest.raises(VerificationWorkflowError, match="cannot answer it"):
        flow.apply(record, VerificationResult(
            status=VerificationStatus.verified, assurance=AssuranceLevel.L2,
            provider="p", method=VerificationMethod.email,
        ))


def test_a_not_connected_provider_still_fails_closed(db, account) -> None:
    """The fail-closed adapter must not become a stub that passes."""
    flow = VerificationWorkflow(db)
    record = flow.request(
        account_id=account.id, identity_id="ident-auth005-1",
        method=VerificationMethod.official_identity, provider="official:not-connected",
    )
    flow.start(record)
    flow.apply(record, VerificationResult(
        status=VerificationStatus.not_connected, assurance=AssuranceLevel.L0,
        provider="official:not-connected", method=VerificationMethod.official_identity,
        reason="Provider integration is not connected in this deployment",
    ))
    assert record.status == VerificationRecordStatus.failed.value
    assert record.assurance_level == AssuranceLevel.L0.value


# ── NR-039: contact is not identity ──────────────────────────────────────────


def test_contact_verification_alone_cannot_link_health_identity(db, account) -> None:
    """The defect, now refused.

    This account's `users.is_verified` is True and it holds a genuine, verified
    contact record. It still may not be linked to a person's health identity,
    because nothing has established who holds it.
    """
    _verify(db, account.id, VerificationMethod.email)
    decision = can_link_health_identity(
        db, legacy_account_id=880051,
        source_kind=LegacyAccountLinkSource.user.value,
        target_citizen_id="citizen-auth005-1",
    )
    assert not decision.allowed
    assert decision.reason_code == "insufficient_identity_assurance"
    assert decision.identity_assurance == AssuranceLevel.L0
    assert "a delivered code is not evidence of who the holder is" in decision.detail


def test_identity_verification_from_an_authority_permits_the_link(db, account) -> None:
    _verify(db, account.id, VerificationMethod.official_identity)
    decision = can_link_health_identity(
        db, legacy_account_id=880051,
        source_kind=LegacyAccountLinkSource.user.value,
        target_citizen_id="citizen-auth005-1",
    )
    assert decision.allowed
    assert decision.identity_assurance == IDENTITY_LINK_MINIMUM
    assert decision.canonical_account_id == "acct-auth005-1"
    assert decision.evidence_ids


def test_a_capture_technique_does_not_reach_the_identity_threshold(db, account) -> None:
    """OCR reads a document; it does not attest to one."""
    _verify(db, account.id, VerificationMethod.ocr)
    decision = can_link_health_identity(
        db, legacy_account_id=880051,
        source_kind=LegacyAccountLinkSource.user.value,
        target_citizen_id="citizen-auth005-1",
    )
    assert not decision.allowed
    assert decision.identity_assurance == AssuranceLevel.L0


def test_a_revoked_identity_verification_stops_permitting_the_link(db, account) -> None:
    record = _verify(db, account.id, VerificationMethod.official_identity)
    VerificationWorkflow(db).revoke(record, reason="security_event")
    decision = can_link_health_identity(
        db, legacy_account_id=880051,
        source_kind=LegacyAccountLinkSource.user.value,
        target_citizen_id="citizen-auth005-1",
    )
    assert not decision.allowed


def test_an_expired_identity_verification_stops_permitting_the_link(db, account) -> None:
    record = _verify(db, account.id, VerificationMethod.official_identity)
    record.expires_at = _now() - timedelta(days=1)
    db.flush()
    decision = can_link_health_identity(
        db, legacy_account_id=880051,
        source_kind=LegacyAccountLinkSource.user.value,
        target_citizen_id="citizen-auth005-1",
    )
    assert not decision.allowed
    assert decision.identity_assurance == AssuranceLevel.L0


def test_the_stored_assurance_column_cannot_raise_itself(db, account) -> None:
    """A row is a cache; the policy is the authority.

    A compromised or buggy writer that stamps L3 on an emailed code must not
    thereby clear the identity threshold.
    """
    record = _verify(db, account.id, VerificationMethod.email)
    record.assurance_level = AssuranceLevel.L3.value
    record.record_type = "identity"
    db.flush()

    decision = can_link_health_identity(
        db, legacy_account_id=880051,
        source_kind=LegacyAccountLinkSource.user.value,
        target_citizen_id="citizen-auth005-1",
    )
    assert not decision.allowed, "a stored level was trusted over the method"
    assert decision.identity_assurance == AssuranceLevel.L0


# ── AUTH-F10: ambiguity blocks, it never guesses ─────────────────────────────


def test_an_account_with_no_canonical_mapping_is_pending_proofing(db) -> None:
    decision = can_link_health_identity(
        db, legacy_account_id=999999,
        source_kind=LegacyAccountLinkSource.user.value,
        target_citizen_id="citizen-x",
    )
    assert not decision.allowed
    assert decision.reason_code == "no_identity_evidence"


def test_an_unvalidated_mapping_is_not_evidence(db) -> None:
    db.add(LegacyAccountLink(
        source_kind=LegacyAccountLinkSource.user.value, legacy_account_id=880052,
        canonical_account_id=None, source_fingerprint="fp-2",
        status=LegacyAccountLinkStatus.pending.value, rollback_token=uuid.uuid4().hex,
    ))
    db.flush()
    decision = resolve_canonical_account(
        db, legacy_account_id=880052, source_kind=LegacyAccountLinkSource.user.value,
    )
    assert not decision.allowed
    assert decision.reason_code == "link_not_validated"


def test_the_schema_makes_a_second_mapping_impossible(db) -> None:
    """Ambiguity is prevented one level below the policy.

    `resolve_canonical_account` refuses when a legacy account maps to more than
    one canonical account. That branch is defence in depth: the migrated schema
    carries a unique constraint on (source_kind, legacy_account_id), so a second
    mapping cannot be written at all. Proving the constraint is stronger than
    proving the Python guard, because the constraint holds against every writer
    including ones that bypass this service.
    """
    import sqlalchemy.exc

    identity_id = _identity_chain(db, "dup-a")
    db.add(Account(
        id="acct-dup-a", uuid=str(uuid.uuid4()), identity_id=identity_id,
        status=AccountStatus.active.value, is_active=True, is_locked=False,
    ))
    db.flush()
    db.add(LegacyAccountLink(
        source_kind=LegacyAccountLinkSource.user.value, legacy_account_id=880053,
        canonical_account_id="acct-dup-a", source_fingerprint="fp-dup-a",
        status=LegacyAccountLinkStatus.validated.value, rollback_token=uuid.uuid4().hex,
    ))
    db.flush()

    db.add(LegacyAccountLink(
        source_kind=LegacyAccountLinkSource.user.value, legacy_account_id=880053,
        canonical_account_id="acct-dup-a", source_fingerprint="fp-dup-b",
        status=LegacyAccountLinkStatus.validated.value, rollback_token=uuid.uuid4().hex,
    ))
    with pytest.raises(sqlalchemy.exc.IntegrityError, match="uq_niam_legacy_account_link_source"):
        db.flush()


def test_an_unknown_account_kind_fails_closed(db) -> None:
    decision = resolve_canonical_account(
        db, legacy_account_id=880051, source_kind="ministry",
    )
    assert not decision.allowed
    assert decision.reason_code == "unknown_account_kind"


def test_a_link_without_a_target_identity_is_refused(db, account) -> None:
    _verify(db, account.id, VerificationMethod.official_identity)
    decision = can_link_health_identity(
        db, legacy_account_id=880051,
        source_kind=LegacyAccountLinkSource.user.value,
        target_citizen_id=None,
    )
    assert not decision.allowed
    assert decision.reason_code == "no_target_identity"


# ── cross-account isolation ──────────────────────────────────────────────────


def test_one_account_cannot_borrow_another_accounts_evidence(db, account) -> None:
    """Evidence is scoped to the account it was gathered for."""
    _linked_account(db, suffix="auth005-2", legacy_id=880054)

    # The first account is identity-verified; the second is not.
    _verify(db, account.id, VerificationMethod.official_identity)

    decision = can_link_health_identity(
        db, legacy_account_id=880054,
        source_kind=LegacyAccountLinkSource.user.value,
        target_citizen_id="citizen-auth005-2",
    )
    assert not decision.allowed
    assert decision.identity_assurance == AssuranceLevel.L0


# ── purposes stay separate under persistence too ─────────────────────────────


def test_a_professional_record_does_not_satisfy_the_identity_threshold(db, account) -> None:
    _verify(db, account.id, VerificationMethod.professional_registry)
    flow = VerificationWorkflow(db)
    profile = flow.profile(account.id)
    assert profile.level_for(VerificationPurpose.professional) == AssuranceLevel.L2
    assert profile.level_for(VerificationPurpose.identity) == AssuranceLevel.L0

    decision = can_link_health_identity(
        db, legacy_account_id=880051,
        source_kind=LegacyAccountLinkSource.user.value,
        target_citizen_id="citizen-auth005-1",
    )
    assert not decision.allowed


# ── Phase 8: the lifecycle, end to end, on the migrated schema ───────────────


def test_the_whole_lifecycle_from_registration_to_activation(db) -> None:
    """Registration → contact → identity evidence → assurance → VERIFIED → link.

    One test walking the path a real citizen takes, against migrated
    PostgreSQL with its real foreign keys, so each step is proven to follow
    from the previous one rather than from a fixture shortcut.
    """
    from app.identity.models.verification_record import VerificationRecord

    # 1. an account exists, and a legacy registration is mapped to it
    account = _linked_account(db, suffix="e2e", legacy_id=880060)
    db.add(User(
        id=880060, full_name="End To End", email="e2e@example.invalid",
        phone="07800600000", password_hash="!x", role="citizen",
        is_active=True, is_verified=False,
    ))
    db.flush()

    # 2. contact verification — what /auth/verification/confirm establishes
    _verify(db, account.id, VerificationMethod.email, identity_id=account.identity_id)
    profile = VerificationWorkflow(db).profile(account.id)
    assert profile.level_for(VerificationPurpose.contact) == AssuranceLevel.L1
    assert profile.level_for(VerificationPurpose.identity) == AssuranceLevel.L0

    # 3. contact alone cannot link a health identity
    blocked = can_link_health_identity(
        db, legacy_account_id=880060,
        source_kind=LegacyAccountLinkSource.user.value,
        target_citizen_id="citizen-e2e",
    )
    assert not blocked.allowed
    assert blocked.reason_code == "insufficient_identity_assurance"

    # 4. identity evidence, created only through the workflow's state machine
    record = _verify(
        db, account.id, VerificationMethod.official_identity,
        identity_id=account.identity_id,
    )
    assert record.status == VerificationRecordStatus.verified.value

    # 5. the record is persisted and readable — this is the row that was missing
    persisted = (
        db.query(VerificationRecord)
        .filter(VerificationRecord.id == record.id)
        .one()
    )
    assert persisted.record_type == "identity"
    assert persisted.assurance_level == AssuranceLevel.L2.value
    assert persisted.account_id == account.id

    # 6. assurance is now sufficient, and says so per purpose
    allowed = can_link_health_identity(
        db, legacy_account_id=880060,
        source_kind=LegacyAccountLinkSource.user.value,
        target_citizen_id="citizen-e2e",
    )
    assert allowed.allowed
    assert allowed.identity_assurance == IDENTITY_LINK_MINIMUM
    assert str(record.id) in allowed.evidence_ids

    # 7. the legacy boolean was never touched and never consulted
    legacy = db.query(User).filter(User.id == 880060).one()
    assert legacy.is_verified is False, (
        "identity verification must not write the legacy contact boolean"
    )


# ── Phase 9: security-sensitive transitions are auditable ────────────────────


def test_every_verification_transition_writes_the_canonical_audit(db, account) -> None:
    """One audit architecture, not a second one.

    The workflow writes through `app.services.audit_service.log_action`, the
    same hash-chained log the rest of the platform uses.
    """
    from sqlalchemy import text

    before = db.execute(text("SELECT count(*) FROM audit_logs")).scalar_one()
    record = _verify(db, account.id, VerificationMethod.official_identity)
    VerificationWorkflow(db).revoke(record, reason="security_event")
    db.flush()

    rows = db.execute(text(
        "SELECT action, details FROM audit_logs ORDER BY id DESC LIMIT 8"
    )).all()
    actions = {row[0] for row in rows}
    assert db.execute(text("SELECT count(*) FROM audit_logs")).scalar_one() > before
    for expected in ("verification_requested", "verification_started",
                     "verification_verified", "verification_revoked"):
        assert expected in actions, f"{expected} was not audited; saw {sorted(actions)}"

    # The record and account are identifiable from the entry.
    detail = next(row[1] for row in rows if row[0] == "verification_verified")
    assert f"account_id={account.id}" in detail
    assert "assurance=L2" in detail


def test_a_refused_linkage_is_audited_with_its_reason(db, account) -> None:
    """A denial is a security event and must leave a trace."""
    from types import SimpleNamespace

    from app.identity.services.citizen_relationship_service import (
        CitizenRelationshipConflict,
        CitizenRelationshipWorkflow,
    )
    from sqlalchemy import text

    _verify(db, account.id, VerificationMethod.email)   # contact only

    relationship = SimpleNamespace(
        id="REL-AUDIT-0001", status="pending", legacy_user_id=880051,
        citizen_id="citizen-auth005-1", version=1, metadata_={},
    )
    workflow = CitizenRelationshipWorkflow.__new__(CitizenRelationshipWorkflow)
    workflow.db = db
    workflow.actor = SimpleNamespace(id=9001, role="ministry_admin")
    workflow.request_ip = "127.0.0.1"
    workflow._for_update = lambda _id: relationship

    with pytest.raises(CitizenRelationshipConflict, match="Identity evidence is insufficient"):
        workflow.activate(relationship.id, verification_reference="review-audit-1")

    row = db.execute(text(
        "SELECT action, details FROM audit_logs "
        "WHERE action = 'citizen_relationship_link_denied' ORDER BY id DESC LIMIT 1"
    )).first()
    assert row is not None, "a refused health-identity linkage was not audited"
    assert "reason=insufficient_identity_assurance" in row[1]
    assert "identity_assurance=L0" in row[1]
    assert relationship.status == "pending", "a refused activation changed state"


# ── NR-044.1: the NIAM gate now reaches PostgreSQL ───────────────────────────


def _mint_niam_token(account_uuid: str) -> tuple[object, str]:
    """Mint a NIAM access token and report the jti the platform assigned.

    `create_token` generates its own `jti` and ignores any supplied one, so the
    session row has to be built from the minted token rather than the reverse.
    """
    from types import SimpleNamespace

    from app.security.auth import create_token, decode_token

    token = create_token({
        "account_uuid": account_uuid, "user_id": 1,
        "lab_id": None, "role": "citizen", "perm_ver": 1,
    })
    jti = decode_token(token)["jti"]
    return SimpleNamespace(cookies={"access_token": token}, headers={}), jti


@pytest.fixture()
def niam_session(db):
    """An active account with a live session, on the migrated schema."""
    from app.identity.models.session import UserSession

    identity_id = _identity_chain(db, "niam-gate")
    account = Account(
        id="acct-niam-gate", uuid=str(uuid.uuid4()), identity_id=identity_id,
        status=AccountStatus.active.value, is_active=True, is_locked=False,
    )
    db.add(account)
    db.flush()

    request, jti = _mint_niam_token(account.uuid)
    session_row = UserSession(
        id="sess-niam-gate", uuid=str(uuid.uuid4()), account_id=account.id,
        token_jti=jti, session_type="web", is_active=True,
        started_at=_now(), last_activity_at=_now(),
        expires_at=_now() + timedelta(hours=1),
    )
    db.add(session_row)
    db.flush()
    return account, session_row, request


def test_the_niam_actor_dependency_now_authenticates_against_postgresql(db, niam_session) -> None:
    """NR-044.1. The gate on every `/niam/*` route used to raise before it
    could query. It now executes and returns the actor."""
    from app.identity.api.workspaces import get_current_niam_actor

    account, session_row, request = niam_session
    actor = get_current_niam_actor(request, None, db)
    assert actor.account.id == account.id
    assert actor.session.id == session_row.id


def test_the_actor_dependency_is_no_longer_a_coroutine(db) -> None:
    """One dependency, synchronous, and the old name is an alias for it."""
    import inspect as _inspect

    from app.identity.api import workspaces

    assert not _inspect.iscoroutinefunction(workspaces.get_current_niam_actor)
    assert workspaces.get_current_niam_actor_sync is workspaces.get_current_niam_actor


def test_a_locked_account_is_refused(db, niam_session) -> None:
    """The check the async version omitted.

    `get_current_niam_actor_sync` filtered on `Account.is_locked`; the async
    twin did not. Converting adopted the stricter of the two, so the gate is
    tightened by this change rather than merely relocated.
    """
    from app.identity.api.workspaces import get_current_niam_actor
    from fastapi import HTTPException

    account, _session_row, request = niam_session
    account.is_locked = True
    db.flush()

    with pytest.raises(HTTPException) as exc:
        get_current_niam_actor(request, None, db)
    assert exc.value.status_code == 401


def test_a_revoked_session_is_refused(db, niam_session) -> None:
    from app.identity.api.workspaces import get_current_niam_actor
    from fastapi import HTTPException

    _account, session_row, request = niam_session
    session_row.is_active = False
    db.flush()

    with pytest.raises(HTTPException) as exc:
        get_current_niam_actor(request, None, db)
    assert exc.value.status_code == 401


def test_a_token_naming_another_session_is_refused(db, niam_session) -> None:
    """The jti must match the stored session, not merely exist."""
    from app.identity.api.workspaces import get_current_niam_actor
    from fastapi import HTTPException

    account, _session_row, _request = niam_session
    other_request, _jti = _mint_niam_token(account.uuid)   # a different jti
    with pytest.raises(HTTPException) as exc:
        get_current_niam_actor(other_request, None, db)
    assert exc.value.status_code == 401


def test_a_suspended_account_is_refused(db, niam_session) -> None:
    from app.identity.api.workspaces import get_current_niam_actor
    from fastapi import HTTPException

    account, _session_row, request = niam_session
    account.status = AccountStatus.suspended.value
    db.flush()

    with pytest.raises(HTTPException) as exc:
        get_current_niam_actor(request, None, db)
    assert exc.value.status_code == 401


def test_the_repository_layer_reaches_postgresql(db, niam_session) -> None:
    """The leaves of the conversion, against real tables.

    `count()` is included deliberately: it imported `sqlalchemy.func` as a
    module, which does not exist. The bug was unreachable while this layer
    could not execute and surfaced the moment it could.
    """
    from app.identity.repositories.account_repository import AccountRepository

    account, _session_row, _request = niam_session
    repo = AccountRepository(db)

    assert repo.get_by_id(account.id) is not None
    assert repo.get_by_uuid(account.uuid) is not None
    assert repo.find_by_email("nobody-at-all@example.invalid") is None
    assert repo.count() >= 1
    assert any(row.id == account.id for row in repo.list_all())


# ── NR-044.1 closeout: the runtime chain, end to end, on the migrated schema ──
#
# Everything below runs against real PostgreSQL through the real FastAPI
# dependency graph. `GET /clinical/patients` is used deliberately: it is the
# narrowest *read-only* route that depends on the converted actor dependency, so
# exercising it proves the chain without performing a clinical mutation.


class _ContainedSession:
    """The real Session, with `commit` downgraded to `flush`.

    The gateway audits before it denies and then commits, by design: a denial
    that cannot be recorded returns 503 rather than a silent 403. That is
    correct, and it is also incompatible with a fixture whose whole purpose is
    that nothing escapes — a real `commit` would end the outer transaction and
    leak the rows.

    Downgrading commit to flush keeps every property that matters for this
    proof: the statements execute against PostgreSQL, foreign keys and
    constraints are enforced, and the audit row is really written. Only the
    outer transaction boundary is withheld, so the test rolls back as designed.
    Every other attribute is the session itself.
    """

    def __init__(self, session):
        self._session = session

    def commit(self):
        self._session.flush()

    def __getattr__(self, name):
        return getattr(self._session, name)


def _gateway_app(db):
    """The real gateway router, with get_db bound to this contained session."""
    from app.clinical_gateway.routes import router
    from app.database import get_db
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    contained = _ContainedSession(db)
    app.dependency_overrides[get_db] = lambda: contained
    return app


def _client(db):
    from fastapi.testclient import TestClient

    return TestClient(_gateway_app(db), raise_server_exceptions=False)


def test_an_unauthenticated_clinical_request_is_rejected(db) -> None:
    """Phase 3.1 — no credential, no entry, over real HTTP."""
    response = _client(db).get("/api/v1/clinical/patients")
    assert response.status_code == 401


def test_a_malformed_token_is_rejected(db) -> None:
    """Phase 3.2 — a bearer token that is not a JWT at all."""
    response = _client(db).get(
        "/api/v1/clinical/patients", headers={"Authorization": "Bearer not-a-jwt"}
    )
    assert response.status_code == 401


def test_a_token_signed_with_another_secret_is_rejected(db) -> None:
    """Phase 3.2 — a well-formed JWT the platform did not sign.

    This is the one that matters: the actor dependency reads `account_uuid` and
    `jti` from the payload, so a token whose signature is not checked would let
    an attacker name any account. `decode_token` returns None on a bad
    signature and the dependency fails closed.
    """
    from app.identity.api.workspaces import get_current_niam_actor
    from joserfc import jwt as _jwt
    from joserfc.jwk import OctKey

    forged = _jwt.encode(
        {"alg": "HS256"},
        {
            "sub": "attacker", "type": "access", "jti": "forged-jti",
            "account_uuid": "any-account-at-all", "user_id": 1,
            "exp": int((_now() + timedelta(hours=1)).timestamp()),
        },
        OctKey.import_key("a-different-secret-entirely-not-the-platforms"),
    )

    from app.security.auth import decode_token
    assert decode_token(forged) is None, "a foreign-signed token decoded successfully"

    request = SimpleNamespace(cookies={"access_token": forged}, headers={})
    with pytest.raises(HTTPException) as exc:
        get_current_niam_actor(request, None, db)
    assert exc.value.status_code == 401

    assert _client(db).get(
        "/api/v1/clinical/patients", headers={"Authorization": f"Bearer {forged}"}
    ).status_code == 401


def test_an_expired_token_is_rejected(db, niam_session) -> None:
    """Phase 3.3 / Phase 4 — expiry is enforced at the token layer.

    The session row is live and active; only the token's `exp` is in the past.
    The request must still be refused, which proves the rejection comes from
    claim validation rather than from the session lookup happening to miss.
    """
    from app.config import SECRET_KEY
    from app.identity.api.workspaces import get_current_niam_actor
    from app.security.auth import decode_token
    from joserfc import jwt as _jwt
    from joserfc.jwk import OctKey

    account, session_row, _request = niam_session
    expired = _jwt.encode(
        {"alg": "HS256"},
        {
            "sub": str(account.id), "type": "access", "jti": session_row.token_jti,
            "account_uuid": account.uuid, "user_id": 1,
            "exp": int((_now() - timedelta(minutes=5)).timestamp()),
            "iat": int((_now() - timedelta(hours=2)).timestamp()),
        },
        OctKey.import_key(SECRET_KEY),
    )

    assert session_row.is_active is True, "the session row must stay live for this proof"
    assert decode_token(expired) is None, "an expired token decoded successfully"

    request = SimpleNamespace(cookies={"access_token": expired}, headers={})
    with pytest.raises(HTTPException) as exc:
        get_current_niam_actor(request, None, db)
    assert exc.value.status_code == 401


def test_a_valid_actor_passes_the_gate_and_the_denial_is_audited(db) -> None:
    """The gate, and the deny path that NR-045 used to break, end to end.

    Three states have been true for this request in sequence, and the
    difference between them is the whole point of NR-044.1 and NR-045:

      * before NR-044.1 — 500: the async actor raised TypeError before a
        statement reached PostgreSQL;
      * after NR-044.1, before NR-045 — 503: authentication succeeded and the
        gateway tried to audit the denial, and the audit insert was refused;
      * now — 403, with the denial recorded in `niam_audit_entries`.

    A 403 here therefore proves authentication passed, authorization ran, and
    the audit write succeeded. The audit row is the evidence for all three.
    """
    import os as _os

    from app.identity.models.session import UserSession
    from sqlalchemy import text

    identity_id = _identity_chain(db, "gate-deny")
    account = Account(
        id="acct-gate-deny", uuid=str(uuid.uuid4()), identity_id=identity_id,
        status=AccountStatus.active.value, is_active=True, is_locked=False,
    )
    db.add(account)
    db.flush()
    request, jti = _mint_niam_token(account.uuid)
    db.add(UserSession(
        id="sess-gate-deny", uuid=str(uuid.uuid4()), account_id=account.id,
        token_jti=jti, session_type="web", is_active=True,
        started_at=_now(), last_activity_at=_now(),
        expires_at=_now() + timedelta(hours=1),
    ))
    db.flush()

    _os.environ["GULA_CLINICAL_GATEWAY_MODE"] = "ON"
    try:
        response = _client(db).get(
            "/api/v1/clinical/patients",
            headers={"Authorization": f"Bearer {request.cookies['access_token']}"},
        )
    finally:
        _os.environ.pop("GULA_CLINICAL_GATEWAY_MODE", None)

    assert response.status_code != 500, "the NR-044 TypeError is back"
    assert response.status_code != 401, "the gate rejected a valid actor"
    assert response.status_code != 503, "NR-045 has regressed — the audit write failed again"
    assert response.status_code == 403, response.text

    row = db.execute(
        text("SELECT uuid, entry_hash, decision, reason_code, actor_id, session_id, source "
             "FROM niam_audit_entries WHERE actor_id = :a"),
        {"a": account.id},
    ).one()
    assert row.uuid and row.entry_hash, "the denial was audited without canonical fields"
    assert row.decision == "deny"
    assert row.reason_code == "missing_workspace"
    assert row.session_id == "sess-gate-deny"
    assert row.source == "clinical_gateway"


def test_the_canonical_audit_writer_satisfies_the_schema_contract_nr045(db) -> None:
    """NR-045, repaired and pinned where it was found.

    This test previously asserted the defect: `CanonicalAuditService.record()`
    omitted the NOT NULL `uuid`, the insert raised IntegrityError, and the
    clinical gateway answered 503 to every request because it audits before it
    allows *and* before it denies.

    `IdentityAuditEntry.uuid` now carries the canonical default, so the writer
    satisfies the contract `AuditService` was already meeting. The assertion is
    inverted rather than deleted: the row must now be written.
    """
    from sqlalchemy import text

    marker = f"nr045-{uuid.uuid4()}"
    entry = (_canonical_audit(db).record(_audit_event(
        actor_id="acct-nr045", request_id=marker, decision="deny",
        reason_code="missing_workspace", outcome="denied",
    )))
    db.flush()

    stored = db.execute(
        text("SELECT uuid, entry_hash, action, decision, outcome "
             "FROM niam_audit_entries WHERE request_id = :m"),
        {"m": marker},
    ).one()
    assert stored.uuid == entry.uuid
    assert uuid.UUID(stored.uuid)
    assert stored.entry_hash
    assert stored.action == "patients.read"
    assert stored.decision == "deny"
    assert stored.outcome == "denied"


# ── NR-044.1 closeout: authorization, against real rows, no mocks ────────────
#
# `ClinicalGatewayContextResolver.resolve()` is the authorization decision for
# the reachable clinical path. It is fully synchronous and queries PostgreSQL
# directly, so it can be exercised without the audit writer NR-045 has broken.
# Each step below plants exactly the state the previous denial named, and the
# resolver's reason advances — which is only possible if every query really ran
# against the migrated schema and read the rows just written.


def _resolve(db, actor):
    from app.clinical_gateway.context import ClinicalGatewayContextResolver

    return ClinicalGatewayContextResolver(db).resolve(actor)


def _blocked_reason(db, actor) -> str:
    from app.clinical_gateway.context import ClinicalGatewayBlocked

    with pytest.raises(ClinicalGatewayBlocked) as exc:
        _resolve(db, actor)
    return exc.value.reason_code


def _niam_organization(db, *, org_key: str, status: str = "active",
                       is_active: bool = True, flush: bool = True):
    """A NIAM organization on the migrated schema."""
    from app.identity.models.niam_organization import NIAMOrganization

    organization = NIAMOrganization(
        id=org_key, uuid=str(uuid.uuid4()), org_id=f"{org_key}-{uuid.uuid4().hex[:8]}",
        name_en="Verification Org", name_ar="\u0645\u0646\u0638\u0645\u0629",
        org_type="hospital", status=status, is_active=is_active,
    )
    db.add(organization)
    db.flush()
    return organization


def _admin_facility(db, *, organization_id: str, suffix: str = "nr0441"):
    """A portal, a branch and an active facility under that organization.

    `niam_admin_portals` has no ORM model in `app/identity/models/`, so the row
    is inserted with Core SQL. `niam_admin_branches.portal_id` is NOT NULL with
    a foreign key to it, although the ORM column permits None — ORM/migration
    drift, noted here rather than fixed, since schema changes are out of scope
    for NR-044.1.
    """
    from app.identity.models.administrative_structure import (
        NIAMAdminBranch,
        NIAMAdminFacility,
    )
    from sqlalchemy import text as _text

    portal_id = f"prt-{suffix}"
    db.execute(
        _text(
            "INSERT INTO niam_admin_portals "
            "(id, uuid, portal_id, organization_id, name, portal_type, status, "
            " is_active, created_at, updated_at) "
            "VALUES (:id, :uuid, :portal_id, :org, :name, 'organization', 'active', "
            " true, now(), now())"
        ),
        {
            "id": portal_id, "uuid": str(uuid.uuid4()),
            "portal_id": f"portal-{uuid.uuid4().hex[:8]}",
            "org": organization_id, "name": "Verification Portal",
        },
    )
    branch = NIAMAdminBranch(
        id=f"brn-{suffix}", uuid=str(uuid.uuid4()),
        branch_id=f"brn-{uuid.uuid4().hex[:8]}", organization_id=organization_id,
        portal_id=portal_id,
        name_en="Verification Branch", name_ar="\u0641\u0631\u0639",
        status="active", is_active=True,
    )
    db.add(branch)
    db.flush()
    facility = NIAMAdminFacility(
        id=f"fac-{suffix}", uuid=str(uuid.uuid4()),
        facility_id=f"fac-{uuid.uuid4().hex[:8]}", branch_id=branch.id,
        organization_id=organization_id, name_en="Verification Facility",
        name_ar="\u0645\u0646\u0634\u0623\u0629", facility_type="hospital",
        status="active", is_active=True,
    )
    db.add(facility)
    db.flush()
    return facility


def test_authorization_walks_its_denial_ladder_on_real_postgresql(db, niam_session) -> None:
    """Phase 3.7/3.9 — authorization denial is preserved and is data-driven.

    Six distinct refusals, each provoked by a real row (or its absence) on the
    migrated schema, each naming a different boundary. A resolver that had
    stopped executing — the NR-044 failure mode — could not produce this
    sequence; it would raise the same error every time.
    """
    from app.identity.api.workspaces import get_current_niam_actor
    from app.identity.models.membership import Membership, MembershipStatus
    from app.identity.models.workspace import (
        Workspace,
        WorkspaceSessionContext,
        WorkspaceStatus,
    )

    account, session_row, request = niam_session
    actor = get_current_niam_actor(request, None, db)

    # 1. No workspace bound to the session at all.
    assert _blocked_reason(db, actor) == "missing_workspace"

    # 2. A context exists, but it points at a workspace with no org/facility.
    workspace = Workspace(
        id="ws-nr0441", uuid=str(uuid.uuid4()), workspace_key=f"ws-key-{uuid.uuid4()}",
        workspace_type="professional", name="Verification Workspace",
        status=WorkspaceStatus.active.value, is_personal=False, version=1,
    )
    db.add(workspace)
    db.flush()
    db.add(WorkspaceSessionContext(
        id="wsc-nr0441", session_id=session_row.id,
        account_id=account.id, identity_id=account.identity_id,
        workspace_id=workspace.id, version=1, is_active=True,
    ))
    db.flush()
    assert _blocked_reason(db, actor) == "workspace_inactive"

    # 3. Real organization and facility rows exist, but the organization's own
    #    standing is suspended. Pointing the workspace at them is refused — the
    #    tenant's standing is part of the conjunction, not just its existence.
    #    (The organization must exist first: niam_workspaces.organization_id is
    #    a real foreign key, so "points at a missing org" is not expressible.)
    organization = _niam_organization(
        db, org_key="org-nr0441", status="suspended", is_active=False,
    )
    facility = _admin_facility(db, organization_id=organization.id)
    workspace.organization_id = organization.id
    workspace.facility_id = facility.id
    db.flush()
    assert _blocked_reason(db, actor) == "invalid_context"

    # 4. Organization active, facility suspended — the facility's standing is
    #    checked independently of the organization's.
    organization.status = "active"
    organization.is_active = True
    facility.status = "suspended"
    facility.is_active = False
    db.flush()
    assert _blocked_reason(db, actor) == "invalid_context"

    # 5. Both active: the refusal moves on to membership, which proves steps 3
    #    and 4 were the organization and facility checks rather than one blanket
    #    failure that happened to fire every time.
    facility.status = "active"
    facility.is_active = True
    db.flush()
    assert _blocked_reason(db, actor) == "membership_missing"

    # 6. A membership in a *different* organization does not count — tenant
    #    isolation holds at the authorization boundary.
    other_org = _niam_organization(db, org_key="org-nr0441-other")
    db.add(Membership(
        id="mem-nr0441-foreign", uuid=str(uuid.uuid4()),
        membership_key=f"mk-{uuid.uuid4()}", account_id=account.id,
        organization_id=other_org.id, relationship_type="staff",
        scope_type="organization", status=MembershipStatus.active.value,
        source="test", version=1, is_active=True,
    ))
    db.flush()
    assert _blocked_reason(db, actor) == "membership_missing", (
        "a membership in another organization satisfied this organization's check"
    )

    # 8. The correct membership advances the refusal to legacy identity, which
    #    is the last boundary before clinical scope is built.
    db.add(Membership(
        id="mem-nr0441", uuid=str(uuid.uuid4()), membership_key=f"mk-{uuid.uuid4()}",
        account_id=account.id, organization_id=organization.id,
        relationship_type="staff", scope_type="organization",
        status=MembershipStatus.active.value, source="test", version=1, is_active=True,
    ))
    db.flush()
    assert _blocked_reason(db, actor) == "legacy_identity_unresolved"


def test_authorization_will_not_accept_a_user_link_where_a_lab_user_is_required(
    db, niam_session,
) -> None:
    """Phase 4 / NR-035 — the discriminator holds on the reachable path.

    The historical ambiguity was that `LegacyAccountLink.legacy_account_id` is a
    bare integer that could mean `User.id` or `LabUser.id`. The resolver filters
    on `source_kind == lab_user`, so a `user` link with the same integer cannot
    be mistaken for a clinical principal. This plants exactly that collision and
    asserts the resolver still refuses.
    """
    from app.identity.api.workspaces import get_current_niam_actor
    from app.identity.models.membership import Membership, MembershipStatus
    from app.identity.models.workspace import (
        Workspace,
        WorkspaceSessionContext,
        WorkspaceStatus,
    )

    account, session_row, request = niam_session
    actor = get_current_niam_actor(request, None, db)

    organization = _niam_organization(db, org_key="org-nr035")
    facility = _admin_facility(db, organization_id=organization.id, suffix="nr035")
    workspace = Workspace(
        id="ws-nr035", uuid=str(uuid.uuid4()), workspace_key=f"ws-key-{uuid.uuid4()}",
        workspace_type="professional", name="NR-035 Workspace",
        status=WorkspaceStatus.active.value, is_personal=False, version=1,
        organization_id=organization.id, facility_id=facility.id,
    )
    db.add(workspace)
    db.flush()
    db.add(WorkspaceSessionContext(
        id="wsc-nr035", session_id=session_row.id,
        account_id=account.id, identity_id=account.identity_id,
        workspace_id=workspace.id, version=1, is_active=True,
    ))
    db.add(Membership(
        id="mem-nr035", uuid=str(uuid.uuid4()), membership_key=f"mk-{uuid.uuid4()}",
        account_id=account.id, organization_id=organization.id,
        relationship_type="staff", scope_type="organization",
        status=MembershipStatus.active.value, source="test", version=1, is_active=True,
    ))
    db.flush()

    # A *user*-kind link for this account. Same shape, same integer space,
    # wrong principal type.
    db.add(LegacyAccountLink(
        source_kind=LegacyAccountLinkSource.user.value,
        legacy_account_id=770035,
        canonical_account_id=account.id,
        source_fingerprint=f"fp-nr035-{uuid.uuid4()}",
        status=LegacyAccountLinkStatus.migrated.value,
        rollback_token=uuid.uuid4().hex,
    ))
    db.flush()

    assert _blocked_reason(db, actor) == "legacy_identity_unresolved", (
        "a user-kind legacy link was accepted where a lab_user link is required — "
        "NR-035's discriminator is not holding on the clinical path"
    )


# ── NR-044.1 closeout: token and session integrity ───────────────────────────


def test_the_token_and_the_session_row_are_bound_by_the_platforms_own_jti(db, niam_session) -> None:
    """Phase 4 — claims, jti, and the session linkage.

    `create_token` mints its own `jti` and ignores any supplied one, so the
    session row must be built from the minted token. Anything else produces a
    session that no token can ever match — a failure mode that looks like
    "authentication is broken" and is really a fixture bug.
    """
    from app.security.auth import create_token, decode_token

    account, session_row, request = niam_session

    supplied = "a-jti-the-caller-chose"
    token = create_token({
        "account_uuid": account.uuid, "user_id": 1, "lab_id": None,
        "role": "citizen", "perm_ver": 1, "jti": supplied,
    })
    claims = decode_token(token)

    assert claims["jti"] != supplied, "create_token now honours a caller-supplied jti"
    assert claims["type"] == "access"
    assert claims["account_uuid"] == account.uuid
    assert "exp" in claims

    # The live session in the fixture carries the jti of its own token, and that
    # is what the gate matches on.
    live = decode_token(request.cookies["access_token"])
    assert live["jti"] == session_row.token_jti


def test_the_gate_does_not_consult_the_session_row_expiry(db, niam_session) -> None:
    """Phase 4 — an honest negative result, recorded as NR-046.

    `UserSession.expires_at` is NOT NULL and is set at login, but the actor
    dependency filters only on `UserSession.is_active`. A session row whose
    `expires_at` is in the past still authenticates, provided the bearer token
    itself has not expired.

    This is NOT a NR-044.1 regression: the converted query is byte-for-byte the
    pre-existing `get_current_niam_actor_sync`, and the async twin did not check
    `expires_at` either. The practical exposure is bounded by the access token's
    own `exp` (JWT_EXPIRE_MINUTES, default 15), which IS enforced — so this
    matters only where a session is meant to expire sooner than its tokens.

    The test asserts today's behaviour so that adding the check fails here and
    this test is rewritten to pin the fix.
    """
    from app.identity.api.workspaces import get_current_niam_actor

    account, session_row, request = niam_session
    session_row.expires_at = _now() - timedelta(days=1)
    db.flush()

    actor = get_current_niam_actor(request, None, db)
    assert actor.account.id == account.id, "unexpected: the gate now rejects on expiry"
    assert session_row.is_active is True
    assert session_row.expires_at < _now()


def test_a_token_for_one_account_cannot_use_another_accounts_session(db, niam_session) -> None:
    """Phase 4 — account and session must belong together.

    The gate joins `UserSession.account_id == Account.id` and matches the jti,
    so a token naming account A with a jti belonging to account B's session
    satisfies neither half of the conjunction.
    """
    from app.identity.api.workspaces import get_current_niam_actor
    from app.identity.models.session import UserSession

    account, session_row, _request = niam_session

    intruder_identity = _identity_chain(db, "niam-intruder")
    intruder = Account(
        id="acct-niam-intruder", uuid=str(uuid.uuid4()), identity_id=intruder_identity,
        status=AccountStatus.active.value, is_active=True, is_locked=False,
    )
    db.add(intruder)
    db.flush()
    intruder_request, intruder_jti = _mint_niam_token(intruder.uuid)
    db.add(UserSession(
        id="sess-niam-intruder", uuid=str(uuid.uuid4()), account_id=intruder.id,
        token_jti=intruder_jti, session_type="web", is_active=True,
        started_at=_now(), last_activity_at=_now(),
        expires_at=_now() + timedelta(hours=1),
    ))
    db.flush()

    # The intruder's own token resolves to the intruder, never to the victim.
    resolved = get_current_niam_actor(intruder_request, None, db)
    assert resolved.account.id == intruder.id
    assert resolved.account.id != account.id
    assert resolved.session.id != session_row.id


# ── NR-044.1 closeout: one Session, one transaction ──────────────────────────


def test_the_actor_and_the_repositories_share_one_session_and_transaction(db, niam_session) -> None:
    """Phase 5 — no parallel database path was created by the conversion.

    The gate, the repository layer and the authorization resolver all receive
    the *same* Session object and therefore the same connection and the same
    transaction. The proof is visibility: a row flushed but not committed inside
    this transaction is seen by all three. A second engine, pool or transaction
    boundary could not see it.
    """
    from app.clinical_gateway.context import ClinicalGatewayContextResolver
    from app.identity.api.workspaces import get_current_niam_actor
    from app.identity.repositories.account_repository import AccountRepository
    from app.identity.repositories.session_repository import SessionRepository

    account, _session_row, request = niam_session

    actor = get_current_niam_actor(request, None, db)
    account_repo = AccountRepository(db)
    session_repo = SessionRepository(db)
    resolver = ClinicalGatewayContextResolver(db)

    # One connection behind all of them.
    assert db.connection() is db.connection()
    assert resolver.db is db
    assert account_repo.session is db
    assert session_repo.session is db

    # Uncommitted state written through one is visible through the others,
    # which is only true inside a single transaction.
    account.is_locked = True
    db.flush()
    assert account_repo.get_by_id(account.id).is_locked is True
    with pytest.raises(HTTPException):
        get_current_niam_actor(request, None, db)

    account.is_locked = False
    db.flush()
    assert get_current_niam_actor(request, None, db).account.id == actor.account.id

    # And the transaction is still open — nothing the gate or the repositories
    # did committed on its own.
    assert db.in_transaction(), "something committed the caller's transaction"


# ── NR-045: the canonical audit write, and the allow path it was blocking ────
#
# NR-044.1 could prove every authorization DENIAL but not a single ALLOW,
# because the gateway audits before it allows *and* before it denies and
# `CanonicalAuditService.record()` could not insert a row. Everything below
# runs against the migrated PostgreSQL schema through the real services.


def _canonical_audit(db):
    from app.identity.services.canonical_audit import CanonicalAuditService

    # NR-044.2: the canonical audit writer takes the session the application
    # actually has. It used to be handed `SyncSessionAsyncFacade`, a shim that
    # made a synchronous Session look awaitable; the writer is synchronous now
    # and the shim is deleted.
    return CanonicalAuditService(db)


def _audit_event(**overrides):
    from app.identity.services.canonical_audit import AuditEventInput

    fields = {
        "event_type": "clinical_gateway_access", "category": "clinical_access",
        "action": "patients.read", "actor_id": "acct-nr045",
        "actor_identity_id": "ident-nr045", "target_type": "clinical_patient",
        "decision": "allow", "reason_code": "permission_granted",
        "request_id": str(uuid.uuid4()), "correlation_id": str(uuid.uuid4()),
        "session_id": "sess-nr045", "source": "clinical_gateway",
        "data_classification": "CLINICAL_SENSITIVE", "outcome": "success",
    }
    fields.update(overrides)
    return AuditEventInput(**fields)


def test_the_canonical_audit_writer_produces_a_schema_valid_row(db) -> None:
    """NR-045 repaired. The row the constraint used to refuse.

    `uuid` is NOT NULL with no server default and `IdentityBaseEntity` does not
    supply it; the column default added by this repair does. `uuid` is
    deliberately absent from v2's `_canonical_payload`, so populating it cannot
    change any entry hash — past entries verify exactly as before.
    """
    entry = (_canonical_audit(db).record(_audit_event(organization_id="org-nr045")))
    db.flush()

    assert entry.uuid, "uuid is still unpopulated — NR-045 has regressed"
    assert uuid.UUID(entry.uuid)           # canonical uuid4, not an arbitrary string
    assert entry.id and len(entry.id) == 26
    assert entry.event_version == "2"
    assert entry.occurred_at is not None
    assert entry.actor_id == "acct-nr045"
    assert entry.decision == "allow"
    assert entry.data_classification == "CLINICAL_SENSITIVE"


def test_the_canonical_audit_entry_carries_a_valid_hash_chain(db) -> None:
    """Hash-chain fields populated, and the chain verifies as the service defines it."""
    from app.identity.services.canonical_audit import CanonicalAuditService, IntegrityStatus

    service = _canonical_audit(db)
    first = (service.record(_audit_event(organization_id="org-chain")))
    second = (service.record(_audit_event(organization_id="org-chain", decision="deny", reason_code="permission_denied", outcome="denied")))
    db.flush()

    assert first.entry_hash and second.entry_hash
    assert first.entry_hash == CanonicalAuditService._hash(first)
    assert second.entry_hash == CanonicalAuditService._hash(second)
    assert second.previous_hash == first.entry_hash, "the second entry does not chain to the first"

    report = (service.verify(organization_id="org-chain"))
    assert report["status"] == IntegrityStatus.valid.value, report["violations"]
    assert report["entries_checked"] == 2
    assert report["violations"] == []


def test_the_audit_service_never_commits_on_its_own(db) -> None:
    """Phase 4.8 — the audit write joins the caller's transaction, it does not end it.

    An audit service that committed would make the protected operation
    un-rollbackable: the audit row would survive a failure it was recording.
    """
    from sqlalchemy import text

    db.execute(text("SELECT 1"))            # a Session begins lazily; make it real first
    assert db.in_transaction()
    (_canonical_audit(db).record(_audit_event(organization_id="org-tx")))
    assert db.in_transaction(), "the audit service committed the caller's transaction"

    source = (
        pathlib.Path(__file__).resolve().parents[1]
        / "app" / "identity" / "services" / "canonical_audit.py"
    ).read_text(encoding="utf-8")
    # NR-044.2: `record` is a plain def now — it was `async def` and could not run.
    record_body = source[source.index("def record("):source.index("def search(")]
    assert "commit" not in record_body, "CanonicalAuditService.record() now commits"


def test_a_rolled_back_operation_leaves_no_committed_audit_row(db, engine) -> None:
    """Phase 4.3 — atomicity, proved by a real rollback against PostgreSQL.

    The audit row is written and flushed inside a transaction that is then
    rolled back. A separate connection must not see it. This is the property
    that makes "audit before deny" meaningful rather than decorative.
    """
    from sqlalchemy import text

    marker = f"rollback-probe-{uuid.uuid4()}"
    connection = engine.connect()
    transaction = connection.begin()
    scratch = Session(bind=connection, future=True)
    try:
        (_canonical_audit(scratch).record(_audit_event(request_id=marker)))
        scratch.flush()
        # Visible inside its own transaction ...
        assert scratch.execute(
            text("SELECT count(*) FROM niam_audit_entries WHERE request_id = :m"), {"m": marker}
        ).scalar() == 1
    finally:
        scratch.close()
        transaction.rollback()
        connection.close()

    # ... and gone once that transaction rolls back.
    assert db.execute(
        text("SELECT count(*) FROM niam_audit_entries WHERE request_id = :m"), {"m": marker}
    ).scalar() == 0, "a rolled-back operation left a committed audit row"


def _authorized_clinical_context(db, *, suffix="allow"):
    """Every row a genuinely authorized clinical read requires, and nothing more.

    Assembled from the actual predicates in ClinicalGatewayContextResolver,
    ClinicalAuthorizationContextService and AuthorizationDecisionService. No
    mock, no monkeypatch, no fake decision: if any row is wrong the real
    services refuse, which is what the denial ladder above already demonstrates.
    """
    from datetime import date

    from app.identity.models.administrative_structure import (
        NIAMAdminBranch,
        NIAMAdminFacility,
    )
    from app.identity.models.authorization import (
        Permission,
        Role,
        RoleAssignment,
        RolePermission,
    )
    from app.identity.models.membership import Membership, MembershipStatus
    from app.identity.models.session import UserSession
    from app.identity.models.workspace import (
        Workspace,
        WorkspaceSessionContext,
        WorkspaceStatus,
    )
    from app.models.clinical_scope import ClinicalLabFacilityBinding
    from app.models.lab_user import LabUser
    from app.models.organization import Facility, Organization
    from app.models.tenant import Tenant
    from sqlalchemy import text as _text

    tag = f"{suffix}-{uuid.uuid4().hex[:6]}"
    # The operational tables (tenants/organizations/facilities/lab_users) are the
    # legacy integer-keyed side of the bridge; the NIAM tables are string-keyed.
    # That divergence is precisely why ClinicalLabFacilityBinding exists.
    nonce = uuid.uuid4().int % 900000
    legacy_lab_id = 9100000 + nonce
    legacy_lab_user_id = 9200000 + nonce

    # ── operational scope: tenant -> organization -> facility ────────────────
    tenant = Tenant(id=9300000 + nonce, tenant_id=f"tid-{tag}", name_en="T", name_ar="ت", is_active=True)
    db.add(tenant)
    db.flush()
    # NR-047 repaired: the ORM now maps onto the real columns, so the fixture
    # builds this row the way the application does rather than around it.
    op_org = Organization(
        id=9400000 + nonce, org_id=f"oid-{tag}", name_en="O", name_ar="م",
        org_type="hospital", tenant_id=tenant.id, is_active=True,
    )
    db.add(op_org)
    db.flush()
    op_org_id = op_org.id
    op_facility = Facility(
        id=9500000 + nonce, facility_id=f"ofid-{tag}", name_en="F", name_ar="ف",
        facility_type="hospital", organization_id=op_org_id, is_active=True,
    )
    db.add(op_facility)
    db.flush()

    # ── NIAM scope: organization -> portal -> branch -> facility -> workspace ─
    niam_org = _niam_organization(db, org_key=f"norg-{tag}")
    niam_facility = _admin_facility(db, organization_id=niam_org.id, suffix=tag)
    assert isinstance(niam_facility, NIAMAdminFacility)
    assert db.query(NIAMAdminBranch).filter_by(organization_id=niam_org.id).count() == 1

    workspace = Workspace(
        id=f"ws-{tag}", uuid=str(uuid.uuid4()), workspace_key=f"wk-{uuid.uuid4()}",
        workspace_type="professional", name="Allow Workspace",
        status=WorkspaceStatus.active.value, is_personal=False, version=1,
        organization_id=niam_org.id, facility_id=niam_facility.id,
    )
    db.add(workspace)
    db.flush()

    # ── the account, its identity chain, and a live session ──────────────────
    identity_id = _identity_chain(db, tag)
    account = Account(
        id=f"acct-{tag}", uuid=str(uuid.uuid4()), identity_id=identity_id,
        status=AccountStatus.active.value, is_active=True, is_locked=False,
    )
    db.add(account)
    db.flush()
    request, jti = _mint_niam_token(account.uuid)
    session_row = UserSession(
        id=f"sess-{tag}", uuid=str(uuid.uuid4()), account_id=account.id,
        token_jti=jti, session_type="web", is_active=True,
        started_at=_now(), last_activity_at=_now(),
        expires_at=_now() + timedelta(hours=1),
    )
    db.add(session_row)
    db.add(WorkspaceSessionContext(
        id=f"wsc-{tag}", session_id=session_row.id, account_id=account.id,
        identity_id=account.identity_id, workspace_id=workspace.id,
        version=1, is_active=True,
    ))
    membership = Membership(
        id=f"mem-{tag}", uuid=str(uuid.uuid4()), membership_key=f"mk-{uuid.uuid4()}",
        account_id=account.id, organization_id=niam_org.id,
        facility_id=niam_facility.id, workspace_id=workspace.id,
        relationship_type="staff", scope_type="organization",
        status=MembershipStatus.active.value, source="test", version=1, is_active=True,
    )
    db.add(membership)
    db.flush()

    # ── the legacy bridge: lab -> lab user -> migrated link -> binding ──────
    db.execute(
        _text(
            "INSERT INTO labs (id, name, is_active, created_at) "
            "VALUES (:id, :name, true, now())"
        ),
        {"id": legacy_lab_id, "name": f"Lab {tag}"},
    )
    db.add(LabUser(
        id=legacy_lab_user_id, lab_id=legacy_lab_id, name="Clinician",
        email=f"clinician-{tag}@example.invalid", password_hash="x", is_active=True,
        role="lab_technician",
    ))
    db.add(LegacyAccountLink(
        source_kind=LegacyAccountLinkSource.lab_user.value,
        legacy_account_id=legacy_lab_user_id, canonical_account_id=account.id,
        source_fingerprint=f"fp-{tag}", status=LegacyAccountLinkStatus.migrated.value,
        rollback_token=uuid.uuid4().hex,
    ))
    db.add(ClinicalLabFacilityBinding(
        legacy_lab_id=legacy_lab_id, facility_resource_id=op_facility.id,
        niam_organization_id=niam_org.id, niam_facility_id=niam_facility.id,
        status="active", mapping_version=1,
    ))
    db.flush()

    # ── the reviewed person->assignment proof chain ──────────────────────────
    person_id = db.execute(
        _text("SELECT person_id FROM niam_identities WHERE id = :i"), {"i": identity_id}
    ).scalar_one()
    employment_id = f"emp-{tag}"
    db.execute(
        _text(
            "INSERT INTO niam_employments (id, uuid, person_id, organization_id, "
            " employment_type, status, position, start_date, is_active, "
            " created_at, updated_at) "
            "VALUES (:id, :uuid, :person, :org, 'full_time', 'active', 'Clinician', "
            " :start, true, now(), now())"
        ),
        {"id": employment_id, "uuid": str(uuid.uuid4()), "person": person_id,
         "org": niam_org.id, "start": date.today() - timedelta(days=30)},
    )
    clinical_role = Role(
        id=f"role-{tag}", uuid=str(uuid.uuid4()), role_key=f"clinician-{tag}",
        name="Clinician", scope_type="organization", status="active",
    )
    db.add(clinical_role)
    db.flush()
    # Core SQL: niam_assignments carries foreign keys into `organizations` and
    # `facilities`, which live in a different declarative base, so the ORM
    # mapper cannot be configured from this side (the 16-base problem NR-018
    # and NR-019 already track). The row itself is ordinary.
    db.execute(
        _text(
            "INSERT INTO niam_assignments (id, uuid, employment_id, person_id, "
            " role_id, assignment_type, organization_id, facility_id, "
            " clinical_organization_resource_id, clinical_facility_resource_id, "
            " status, is_active, start_date, assigned_at, created_at, updated_at) "
            "VALUES (:id, :uuid, :emp, :person, :role, 'clinical', :org, :fac, "
            " :corg, :cfac, 'active', true, :start, now(), now(), now())"
        ),
        {"id": f"asg-{tag}", "uuid": str(uuid.uuid4()), "emp": employment_id,
         "person": person_id, "role": clinical_role.id, "org": niam_org.id,
         "fac": niam_facility.id, "corg": op_org_id, "cfac": op_facility.id,
         "start": date.today() - timedelta(days=30)},
    )

    # ── the permission the gateway asks for, granted in this exact scope ─────
    # `patients.read` is seeded platform catalog data. Use the real row rather
    # than a duplicate — the catalog is the thing the gateway consults.
    permission = db.query(Permission).filter_by(permission_key="patients.read").one_or_none()
    if permission is None:
        permission = Permission(
            id=f"perm-{tag}", uuid=str(uuid.uuid4()), permission_key="patients.read",
            name="Read patients", resource="clinical_patient", action="read", status="active",
        )
        db.add(permission)
        db.flush()
    assert permission.status == "active", "the seeded patients.read permission is not active"
    db.add(RolePermission(
        id=f"rp-{tag}", role_id=clinical_role.id, permission_id=permission.id, status="active",
    ))
    db.add(RoleAssignment(
        id=f"ra-{tag}", uuid=str(uuid.uuid4()),
        assignment_key=f"{account.id}:{membership.id}:{clinical_role.id}:{niam_org.id}:-:-:-:-",
        account_id=account.id, membership_id=membership.id, role_id=clinical_role.id,
        organization_id=niam_org.id, scope_type="organization", status="active",
    ))
    db.flush()

    return SimpleNamespace(
        account=account, session=session_row, request=request, workspace=workspace,
        niam_org=niam_org, niam_facility=niam_facility, op_facility=op_facility,
        legacy_lab_id=legacy_lab_id, legacy_lab_user_id=legacy_lab_user_id, tag=tag,
    )


def test_a_fully_authorized_actor_is_allowed_and_the_read_executes(db) -> None:
    """The ALLOW proof NR-044.1 could not produce, now produced (NR-047).

    Every precondition is a real row: active account, live NIAM session, active
    workspace bound to that session, active organization and facility, an active
    membership in that organization, a migrated `lab_user` link, an active
    lab-to-facility binding, an active employment and clinical assignment, and
    the *seeded* `patients.read` permission granted through a role assignment in
    exactly this scope. Nothing is mocked and no decision is supplied — the
    denial ladder above proves each of those checks is really evaluated, so
    getting past them means they were satisfied.

    Three states have been true for this request in sequence:

      * before NR-044.1 — 500, the async actor raised before reaching PostgreSQL;
      * after NR-044.1, before NR-045 — 503, the deny audit could not be written;
      * after NR-045, before NR-047 — 403 `invalid_context`, because the
        Organization ORM named columns the table does not have;
      * now — **200**, with the workspace context echoed back.
    """
    import os as _os

    ctx = _authorized_clinical_context(db)

    _os.environ["GULA_CLINICAL_GATEWAY_MODE"] = "ON"
    try:
        response = _client(db).get(
            "/api/v1/clinical/patients",
            headers={"Authorization": f"Bearer {ctx.request.cookies['access_token']}"},
        )
    finally:
        _os.environ.pop("GULA_CLINICAL_GATEWAY_MODE", None)

    assert response.status_code != 401, "authentication failed for a valid actor"
    assert response.status_code != 403, f"authorization denied a fully authorized actor: {response.text}"
    assert response.status_code != 503, f"NR-045 regressed — the audit write failed: {response.text}"
    assert response.status_code == 200, response.text

    payload = response.json()
    assert payload["workspace_context"]["workspace_id"] == ctx.workspace.id
    assert payload["workspace_context"]["organization_id"] == ctx.niam_org.id
    assert payload["workspace_context"]["facility_id"] == ctx.niam_facility.id
    assert "items" in payload


def test_the_allow_path_resolves_the_full_operational_scope(db) -> None:
    """The resolver reaches operational scope — the step NR-047 used to break.

    Asserting the scope, not just the status code: a 200 with the wrong tenant
    or facility would be worse than a 403.
    """
    from app.clinical_gateway.context import ClinicalGatewayContextResolver
    from app.identity.api.workspaces import get_current_niam_actor

    ctx = _authorized_clinical_context(db)
    actor = get_current_niam_actor(ctx.request, None, db)
    resolved = ClinicalGatewayContextResolver(db).resolve(actor)

    assert resolved.scope.legacy_lab_id == ctx.legacy_lab_id
    assert resolved.scope.operational_facility_id == ctx.op_facility.id
    assert resolved.scope.niam_organization_id == ctx.niam_org.id
    assert resolved.scope.niam_facility_id == ctx.niam_facility.id
    assert resolved.scope.niam_workspace_id == ctx.workspace.id
    assert resolved.scope.tenant_id is not None
    assert resolved.legacy_user.lab_id == ctx.legacy_lab_id


def test_the_operational_organization_orm_matches_its_table_nr047(db) -> None:
    """NR-047 repaired, pinned where the defect was found.

    This test previously asserted the drift: the ORM declared `org_id`,
    `org_type`, `parent_org_id` and `updated_at`, none of which the table had.
    The assertion is inverted rather than deleted — declared and physical
    columns must now agree exactly, in both directions.

    Note what the repair did *not* do. `org_id` and `org_type` are mapped onto
    the existing `organization_id` and `organization_type`; no column was
    renamed to suit the model. `updated_at` was removed from the ORM instead of
    added to the table, because nothing reads, writes or serialises it. Only
    `parent_org_id` was added, because the bootstrap genuinely seeds a
    ministry-to-directorate hierarchy through it.
    """
    from app.models.organization import Organization
    from sqlalchemy import text

    physical = {
        row[0]
        for row in db.execute(
            text("SELECT column_name FROM information_schema.columns "
                 "WHERE table_name = 'organizations'")
        )
    }
    declared = {column.name for column in Organization.__table__.columns}

    assert declared - physical == set(), (
        f"the ORM declares columns the table lacks: {sorted(declared - physical)}"
    )
    assert physical - declared == set(), (
        f"the table has columns the ORM does not map: {sorted(physical - declared)}"
    )

    # The Python attributes kept their names; only the mapping moved.
    assert Organization.org_id.property.columns[0].name == "organization_id"
    assert Organization.org_type.property.columns[0].name == "organization_type"
    assert not hasattr(Organization, "updated_at"), (
        "updated_at came back — it is read by nothing and belongs to NIAMOrganization"
    )

    # parent_org_id is a public-identifier string, not NIAM's integer self-FK.
    parent = Organization.__table__.c.parent_org_id
    assert isinstance(parent.type, sqlalchemy_String), parent.type
    assert parent.type.length == 100
    assert parent.nullable is True
    assert not parent.foreign_keys, (
        "a foreign key appeared on parent_org_id; NR-047 deliberately declared none"
    )


def test_the_exact_operational_scope_query_executes(db) -> None:
    """The query that raised UndefinedColumn, run verbatim against PostgreSQL."""
    from app.models.organization import Facility, Organization
    from app.models.tenant import Tenant
    from sqlalchemy import select

    db.execute(
        select(Facility, Organization, Tenant)
        .join(Organization, Organization.id == Facility.organization_id)
        .join(Tenant, Tenant.id == Organization.tenant_id)
        .where(
            Facility.is_active.is_(True),
            Organization.is_active.is_(True),
            Tenant.is_active.is_(True),
        ),
    ).first()


def test_the_national_bootstrap_completes_and_is_idempotent_for_organizations(db) -> None:
    """NR-047's other half: the bootstrap has never run until now.

    `run_bootstrap` is called from the startup guard inside a `try/except`
    logged "non-fatal", so its failure on `organizations.org_id` was invisible:
    the platform reported ready while the ministry, directorates, organizations
    and facilities were never seeded. `organizations` being empty was the
    symptom, not evidence of disuse.

    Idempotency is asserted only for the tables this finding owns.
    `lims_departments` gains rows on a second pass and then stabilises — a
    pre-existing seeder behaviour, recorded rather than folded in here.
    """
    from app.core.bootstrap.bootstrap import run_bootstrap
    from app.models.organization import Facility, Organization
    from sqlalchemy import func, select

    first = run_bootstrap(db=db)
    assert first["ministry"] == 1, first
    assert first["directorates"] >= 1, first

    organizations = db.scalar(select(func.count()).select_from(Organization))
    facilities = db.scalar(select(func.count()).select_from(Facility))
    assert organizations >= 2

    ministry = db.query(Organization).filter(Organization.org_id == "org-iraq-moh").one()
    assert ministry.parent_org_id is None, "the ministry must sit at the root"

    children = db.query(Organization).filter(Organization.parent_org_id.isnot(None)).all()
    assert children, "no directorate was given a parent"
    known = {row.org_id for row in db.query(Organization)}
    assert {child.parent_org_id for child in children} <= known, (
        "a directorate points at an organization_id that does not exist"
    )
    assert db.query(Facility).filter(Facility.organization_id.is_(None)).count() == 0

    # Second pass adds no organization or facility, and no duplicate key.
    run_bootstrap(db=db)
    assert db.scalar(select(func.count()).select_from(Organization)) == organizations
    assert db.scalar(select(func.count()).select_from(Facility)) == facilities
    duplicates = db.execute(
        select(Organization.org_id, func.count())
        .group_by(Organization.org_id)
        .having(func.count() > 1),
    ).all()
    assert duplicates == [], duplicates


def test_every_denial_boundary_still_holds_from_an_otherwise_valid_context(db) -> None:
    """Phase 8 — the denial ladder, re-run from a context that would otherwise ALLOW.

    This is the version that matters now. The earlier ladder built the context
    up from nothing, so each refusal could in principle have come from something
    still missing. Here the starting point is a context proven to return 200, and
    exactly one fact is broken at a time. A universal 403 caused by a hidden
    database failure cannot produce this: each break must yield *its own* reason
    and the context must recover when the fact is restored.
    """
    from app.clinical_gateway.context import ClinicalGatewayContextResolver
    from app.identity.api.workspaces import get_current_niam_actor
    from app.identity.models.membership import Membership, MembershipStatus
    from app.identity.models.workspace import WorkspaceSessionContext, WorkspaceStatus

    ctx = _authorized_clinical_context(db, suffix="deny")
    actor = get_current_niam_actor(ctx.request, None, db)

    def resolves() -> bool:
        ClinicalGatewayContextResolver(db).resolve(actor)
        return True

    assert resolves(), "the baseline context must allow before anything is broken"

    context_row = db.query(WorkspaceSessionContext).filter_by(session_id=ctx.session.id).one()
    membership = db.query(Membership).filter_by(account_id=ctx.account.id).one()
    link = db.query(LegacyAccountLink).filter_by(canonical_account_id=ctx.account.id).one()

    # 1. no workspace bound to the session
    context_row.is_active = False
    db.flush()
    assert _blocked_reason(db, actor) == "missing_workspace"
    context_row.is_active = True
    db.flush()
    assert resolves()

    # 2. the workspace itself is not active
    ctx.workspace.status = WorkspaceStatus.suspended.value
    db.flush()
    assert _blocked_reason(db, actor) == "workspace_inactive"
    ctx.workspace.status = WorkspaceStatus.active.value
    db.flush()
    assert resolves()

    # 3. the organization's own standing
    ctx.niam_org.is_active = False
    db.flush()
    assert _blocked_reason(db, actor) == "invalid_context"
    ctx.niam_org.is_active = True
    db.flush()
    assert resolves()

    # 4. the facility's own standing, checked independently
    ctx.niam_facility.status = "suspended"
    ctx.niam_facility.is_active = False
    db.flush()
    assert _blocked_reason(db, actor) == "invalid_context"
    ctx.niam_facility.status = "active"
    ctx.niam_facility.is_active = True
    db.flush()
    assert resolves()

    # 5. membership revoked
    membership.status = MembershipStatus.revoked.value
    membership.is_active = False
    db.flush()
    assert _blocked_reason(db, actor) == "membership_missing"
    membership.status = MembershipStatus.active.value
    membership.is_active = True
    db.flush()
    assert resolves()

    # 6. membership moved to another organization — tenant isolation
    other = _niam_organization(db, org_key=f"norg-other-{ctx.tag}")
    membership.organization_id = other.id
    db.flush()
    assert _blocked_reason(db, actor) == "membership_missing", (
        "a membership in another organization satisfied this organization's check"
    )
    membership.organization_id = ctx.niam_org.id
    db.flush()
    assert resolves()

    # 7. the legacy identity no longer resolves
    link.status = LegacyAccountLinkStatus.validated.value   # not `migrated`
    db.flush()
    assert _blocked_reason(db, actor) == "legacy_identity_unresolved"
    link.status = LegacyAccountLinkStatus.migrated.value
    db.flush()
    assert resolves()

    # 8. the operational tenant is deactivated — the far end of the bridge
    from sqlalchemy import text as _t

    db.execute(_t("UPDATE tenants SET is_active = false WHERE id = "
                  "(SELECT tenant_id FROM organizations WHERE id = :o)"),
               {"o": ctx.op_facility.organization_id})
    db.flush()
    assert _blocked_reason(db, actor) == "invalid_context"


def test_an_allowed_read_is_audited_with_a_valid_chain(db) -> None:
    """Phase 6/9 — the ALLOW side of the audit, which NR-045 also unblocked.

    The gateway audits before it serves. A 200 therefore implies a canonical
    audit row exists, and this reads it back rather than trusting the status.
    """
    import os as _os

    from app.identity.services.canonical_audit import CanonicalAuditService
    from sqlalchemy import text

    ctx = _authorized_clinical_context(db, suffix="audit")

    _os.environ["GULA_CLINICAL_GATEWAY_MODE"] = "ON"
    try:
        response = _client(db).get(
            "/api/v1/clinical/patients",
            headers={"Authorization": f"Bearer {ctx.request.cookies['access_token']}"},
        )
    finally:
        _os.environ.pop("GULA_CLINICAL_GATEWAY_MODE", None)
    assert response.status_code == 200, response.text

    rows = db.execute(
        text("SELECT uuid, entry_hash, previous_hash, decision, action, actor_id, "
             "session_id, organization_id, source, data_classification, occurred_at "
             "FROM niam_audit_entries WHERE actor_id = :a ORDER BY occurred_at"),
        {"a": ctx.account.id},
    ).all()
    # Two writers audit one allowed read, and both are intentional:
    # AuthorizationDecisionService records the decision it made, and
    # ClinicalGatewayService records the gateway access. They are distinguished
    # by `source`. This asserts exactly one of each rather than a bare count, so
    # a genuine duplicate from either writer would still fail.
    by_source = {}
    for row in rows:
        by_source.setdefault(row.source, []).append(row)
    gateway = by_source.get("clinical_gateway", [])
    assert len(gateway) == 1, f"clinical_gateway wrote {len(gateway)} entries for one read"
    for source, group in by_source.items():
        assert len(group) == 1, f"{source} wrote {len(group)} entries for one read"
    entry = gateway[0]

    assert entry.uuid and uuid.UUID(entry.uuid)
    assert entry.entry_hash
    assert entry.decision == "allow", entry.decision
    assert entry.action == "patients.read"
    assert entry.session_id == ctx.session.id
    assert entry.source == "clinical_gateway"
    assert entry.data_classification == "CLINICAL_SENSITIVE"
    assert entry.occurred_at is not None

    report = verify_chain(db, organization_id=entry.organization_id)
    assert report["status"] == "VALID", report["violations"]
    assert report["entries_checked"] >= 1
    assert CanonicalAuditService  # imported for the reader's benefit


def verify_chain(db, *, organization_id):
    from app.identity.services.canonical_audit import CanonicalAuditService

    return CanonicalAuditService(db).verify(organization_id=organization_id)


def test_a_valid_context_never_reaches_the_broad_exception_path(db) -> None:
    """Phase 9 — a schema fault no longer masquerades as a policy decision.

    `clinical_gateway/context.py` converts any unexpected exception into
    `invalid_context`, which is indistinguishable from a genuine denial. That
    wrapper is deliberately left alone in this batch; what is asserted here is
    that the repaired path no longer *needs* it — the resolver completes without
    raising, so `invalid_context` is once again reserved for real context
    failures (proved by the denial ladder, which still produces it for a
    suspended organization and a suspended facility).
    """
    from app.clinical_gateway.context import ClinicalGatewayContextResolver
    from app.identity.api.workspaces import get_current_niam_actor

    ctx = _authorized_clinical_context(db, suffix="nowrap")
    actor = get_current_niam_actor(ctx.request, None, db)

    resolver = ClinicalGatewayContextResolver(db)
    raised: list[BaseException] = []
    original = resolver.resolve

    resolved = original(actor)
    assert resolved is not None
    assert not raised
    assert resolved.scope.niam_organization_id == ctx.niam_org.id


# ── NR-044.2: the service layer, executed against migrated PostgreSQL ─────────
#
# Until this batch, every test below would have failed with
# `TypeError: object ChunkedIteratorResult can't be used in 'await' expression`
# before a statement reached the database. None of them uses a fake session, a
# monkeypatched service or a mocked decision: a fake proves the shape of a call,
# and the shape was never what was broken.


def _password_account(db, *, suffix: str, password: str, **overrides) -> Account:
    """A real account with a real Argon2/bcrypt hash, on the migrated schema."""
    from app.security.auth import hash_password

    identity_id = _identity_chain(db, f"authn-{suffix}")
    fields = {
        "id": f"acct-authn-{suffix}",
        "uuid": str(uuid.uuid4()),
        "identity_id": identity_id,
        "email": f"authn-{suffix}@example.iq",
        "status": AccountStatus.active.value,
        "is_active": True,
        "is_locked": False,
        "failed_login_attempts": 0,
        "password_hash": hash_password(password),
    }
    fields.update(overrides)
    account = Account(**fields)
    db.add(account)
    db.flush()
    return account


def test_the_authentication_service_now_logs_in_against_postgresql(db) -> None:
    """NR-044.2 — the NIAM login path reaches the database and mints a session.

    `AuthenticationService.login` walks `AccountService.authenticate` (a SELECT
    and a flush), `SessionRepository.create` (an INSERT) and
    `WorkspaceService.ensure_citizen_workspace` (another SELECT and INSERT).
    Every one of those was an `await` on a synchronous Session, so the whole
    flow raised on its first statement. It runs now, and the session row it
    claims to have created is read back from PostgreSQL rather than trusted.
    """
    from app.identity.models.session import UserSession
    from app.identity.services.authentication_service import AuthenticationService

    account = _password_account(db, suffix="ok", password="correct horse battery staple")

    result = AuthenticationService(db).login(
        login="authn-ok@example.iq", password="correct horse battery staple",
    )

    assert result is not None, "login returned None on a valid credential"
    assert result["account_uuid"] == account.uuid
    assert result["access_token"] and result["refresh_token"]

    stored = (
        db.query(UserSession)
        .filter(UserSession.uuid == result["session_uuid"])
        .one()
    )
    assert stored.account_id == account.id
    assert stored.is_active is True
    assert stored.token_jti and stored.refresh_token_jti
    assert stored.expires_at is not None

    db.refresh(account)
    assert account.last_login is not None, "the successful login was not recorded"
    assert account.failed_login_attempts == 0


def test_a_wrong_password_is_denied_and_creates_no_session(db) -> None:
    """The denial half, and the counter that makes lockout possible.

    Reading the failure counter back from PostgreSQL is the point: an
    unreachable service incremented nothing, so the lockout policy that depends
    on it could not have worked either.
    """
    from app.identity.models.session import UserSession
    from app.identity.services.authentication_service import AuthenticationService

    account = _password_account(db, suffix="wrong", password="correct horse battery staple")
    before = db.query(UserSession).filter(UserSession.account_id == account.id).count()

    result = AuthenticationService(db).login(
        login="authn-wrong@example.iq", password="not the password",
    )

    assert result is None
    after = db.query(UserSession).filter(UserSession.account_id == account.id).count()
    assert after == before, "a denied login created a session row"
    db.refresh(account)
    assert account.failed_login_attempts == 1


def test_an_unknown_login_is_denied_without_a_session(db) -> None:
    from app.identity.services.authentication_service import AuthenticationService

    assert AuthenticationService(db).login(
        login="nobody-at-all@example.iq", password="anything",
    ) is None


def test_a_suspended_account_cannot_authenticate_even_with_the_right_password(db) -> None:
    """Status is checked before the password is believed, against real rows."""
    from app.identity.services.authentication_service import AuthenticationService

    _password_account(
        db, suffix="susp", password="correct horse battery staple",
        status=AccountStatus.suspended.value,
    )

    assert AuthenticationService(db).login(
        login="authn-susp@example.iq", password="correct horse battery staple",
    ) is None


def test_a_locked_account_within_its_lockout_window_cannot_authenticate(db) -> None:
    """The lock is honoured while `locked_until` is in the future.

    After it expires the account is released — asserted here too, so the test
    pins the policy rather than only its denial half.
    """
    from app.identity.services.authentication_service import AuthenticationService

    account = _password_account(
        db, suffix="locked", password="correct horse battery staple",
        is_locked=True, status=AccountStatus.locked.value,
        locked_until=_now() + timedelta(minutes=30),
    )

    assert AuthenticationService(db).login(
        login="authn-locked@example.iq", password="correct horse battery staple",
    ) is None

    account.locked_until = _now() - timedelta(minutes=1)
    db.flush()
    released = AuthenticationService(db).login(
        login="authn-locked@example.iq", password="correct horse battery staple",
    )
    assert released is not None, "an expired lockout still refused a valid credential"


def test_logout_terminates_the_real_session_row(db) -> None:
    """Session lifecycle, read back from PostgreSQL rather than asserted."""
    from app.identity.models.session import UserSession
    from app.identity.services.authentication_service import AuthenticationService

    _password_account(db, suffix="logout", password="correct horse battery staple")
    service = AuthenticationService(db)
    result = service.login(
        login="authn-logout@example.iq", password="correct horse battery staple",
    )
    assert result is not None

    service.logout(result["session_uuid"])
    db.flush()

    stored = db.query(UserSession).filter(UserSession.uuid == result["session_uuid"]).one()
    assert stored.is_active is False
    assert stored.termination_reason == "user_logout"


def test_the_workspace_service_reads_eligibility_from_postgresql(db) -> None:
    """`WorkspaceService` was the headline unreachable service; it executes now.

    The citizen workspace is the one every account gets, so creating it twice
    must be idempotent — a property that could not previously be tested because
    the first call never completed.
    """
    from app.identity.services.workspace_service import WorkspaceService

    account = _password_account(db, suffix="ws", password="correct horse battery staple")
    service = WorkspaceService(db)

    first = service.ensure_citizen_workspace(account)
    db.flush()
    second = service.ensure_citizen_workspace(account)
    db.flush()

    assert first is not None
    assert second is not None
    assert first.id == second.id, "a second call created a duplicate citizen workspace"
    assert any(w.id == first.id for w in service.list_eligible(account))


def test_a_database_fault_is_no_longer_reported_as_a_policy_denial(db) -> None:
    """NR-048 — the gateway used to translate *any* exception into a 403.

    That is how NR-047 presented: `column organizations.org_id does not exist`
    reached the client as `invalid_context`, indistinguishable from a genuine
    authorization denial both in the response and in the audit row. NR-044's
    `TypeError` was swallowed by the same handler.

    Here a real `SQLAlchemyError` is raised from inside the context service. It
    must propagate — the read is still refused, but as a fault rather than as a
    decision. The denial ladder above proves the other half: real denials still
    produce `invalid_context`.
    """
    from app.clinical_gateway.context import ClinicalGatewayContextResolver
    from app.identity.api.workspaces import get_current_niam_actor
    from app.identity.services.clinical_authorization_context_service import (
        ClinicalAuthorizationContextService,
    )
    from sqlalchemy.exc import OperationalError

    ctx = _authorized_clinical_context(db, suffix="nr048")
    actor = get_current_niam_actor(ctx.request, None, db)

    original = ClinicalAuthorizationContextService.resolve_for_legacy_lab_user

    def _explode(self, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("connection reset"))

    ClinicalAuthorizationContextService.resolve_for_legacy_lab_user = _explode
    try:
        with pytest.raises(OperationalError):
            ClinicalGatewayContextResolver(db).resolve(actor)
    finally:
        ClinicalAuthorizationContextService.resolve_for_legacy_lab_user = original

    # And the same resolver, unperturbed, still completes.
    assert ClinicalGatewayContextResolver(db).resolve(actor) is not None


def test_a_genuine_context_denial_is_still_translated_to_invalid_context(db) -> None:
    """The other side of NR-048: the service's own vocabulary keeps its meaning."""
    from app.clinical_gateway.context import (
        ClinicalGatewayBlocked,
        ClinicalGatewayContextResolver,
    )
    from app.identity.api.workspaces import get_current_niam_actor
    from app.identity.services.clinical_authorization_context_service import (
        ClinicalActiveAssignmentUnavailable,
        ClinicalAuthorizationContextService,
    )

    ctx = _authorized_clinical_context(db, suffix="nr048b")
    actor = get_current_niam_actor(ctx.request, None, db)

    original = ClinicalAuthorizationContextService.resolve_for_legacy_lab_user

    def _deny(self, **kwargs):
        raise ClinicalActiveAssignmentUnavailable("no active clinical assignment")

    ClinicalAuthorizationContextService.resolve_for_legacy_lab_user = _deny
    try:
        with pytest.raises(ClinicalGatewayBlocked) as blocked:
            ClinicalGatewayContextResolver(db).resolve(actor)
    finally:
        ClinicalAuthorizationContextService.resolve_for_legacy_lab_user = original

    assert blocked.value.reason_code == "invalid_context"


# ── NR-044.3 Part H: the two findings whose proof was blocked on reachability ─
#
# NR-038 and AUTH-F5/NR-043 have been PARTIALLY VERIFIED since AUTH-005 for the
# same reason: the code was correct and could not run, so no behavioural proof
# existed. NR-044.3 made both paths executable. These are the proofs that were
# owed — and they are behavioural, because "it no longer raises" is not the same
# as "the control works".


def test_an_account_with_no_identity_evidence_gets_the_floor_assurance_nr038(db) -> None:
    """NR-038 — the level is derived from evidence, and absent evidence is low.

    The route used to accept `ial`, `aal`, `fal`, `assessed_by` and `evidence`
    from the caller and write them through with `status="active"`. The static
    half of that (the parameters are gone) has been pinned since AUTH-005. This
    is the half that needed a database: with no verification record at all, the
    derived profile must sit at the floor rather than anywhere a caller might
    have preferred.
    """
    from app.identity.trust.services import AssuranceService

    identity_id = _identity_chain(db, "nr038-floor")
    account = Account(
        id="acct-nr038-floor", uuid=str(uuid.uuid4()), identity_id=identity_id,
        status=AccountStatus.active.value, is_active=True, is_locked=False,
    )
    db.add(account)
    db.flush()

    profile = AssuranceService(db).derive_profile(
        account_id=account.id, person_id="person-nr038-floor",
        identity_id=identity_id, assessed_by=account.id,
    )
    db.flush()

    assert profile.ial == "IAL1", f"no evidence produced {profile.ial}"
    assert profile.aal == "AAL1"
    assert profile.fal == "FAL1"
    assert profile.overall_assurance == "IAL1"
    assert profile.evidence["derived_from"] == "niam_verification_records"
    assert profile.assessed_by == account.id


def test_only_a_real_verification_record_raises_the_level_nr038(db) -> None:
    """NR-038 — and the only thing that raises it is evidence a verifier wrote.

    The record is created through `VerificationWorkflow`, the real state
    machine, not by inserting a row that says the right thing. The profile then
    has to move on its own.
    """
    from app.identity.trust.services import AssuranceService

    identity_id = _identity_chain(db, "nr038-raise")
    account = Account(
        id="acct-nr038-raise", uuid=str(uuid.uuid4()), identity_id=identity_id,
        status=AccountStatus.active.value, is_active=True, is_locked=False,
    )
    db.add(account)
    db.flush()

    before = AssuranceService(db).derive_profile(
        account_id=account.id, person_id="person-nr038-raise",
        identity_id=identity_id, assessed_by=account.id,
    )
    db.flush()

    _verify(db, account.id, VerificationMethod.official_identity, identity_id=identity_id)

    after = AssuranceService(db).derive_profile(
        account_id=account.id, person_id="person-nr038-raise",
        identity_id=identity_id, assessed_by=account.id,
    )
    db.flush()

    assert before.ial == "IAL1"
    assert after.ial != before.ial, "a verified identity record did not raise the level"
    assert after.evidence["identity_assurance"] != "none"


def test_the_overall_assurance_is_the_weakest_axis_not_the_average_nr038(db) -> None:
    """NR-038 — averaging let authentication strength lift an unproofed identity.

    With AAL and FAL pinned at the floor, a raised IAL must not drag the overall
    up with it: the overall is the weakest axis. Asserted from a real derived
    profile rather than by reading `_calculate_overall`.
    """
    from app.identity.trust.services import AssuranceService

    identity_id = _identity_chain(db, "nr038-weakest")
    account = Account(
        id="acct-nr038-weakest", uuid=str(uuid.uuid4()), identity_id=identity_id,
        status=AccountStatus.active.value, is_active=True, is_locked=False,
    )
    db.add(account)
    db.flush()
    _verify(db, account.id, VerificationMethod.official_identity, identity_id=identity_id)

    profile = AssuranceService(db).derive_profile(
        account_id=account.id, person_id="person-nr038-weakest",
        identity_id=identity_id, assessed_by=account.id,
    )
    db.flush()

    assert profile.aal == "AAL1" and profile.fal == "FAL1"
    assert profile.overall_assurance == "IAL1", (
        f"a raised IAL lifted the overall to {profile.overall_assurance} while AAL "
        "and FAL are at the floor; the overall must be the weakest axis"
    )


def test_asserting_for_another_account_needs_an_administrative_assignment_nr038(db) -> None:
    """NR-038 — the route's own gate, executed.

    `create_assurance_profile` recomputes the caller's own profile freely, and
    requires an active administrative assignment to name a different subject.
    The gate is called here directly with a real session and a real actor.
    """
    from app.identity.trust.routes import _require_assurance_administrator
    from fastapi import HTTPException

    identity_id = _identity_chain(db, "nr038-admin")
    account = Account(
        id="acct-nr038-admin", uuid=str(uuid.uuid4()), identity_id=identity_id,
        status=AccountStatus.active.value, is_active=True, is_locked=False,
    )
    db.add(account)
    db.flush()

    from app.identity.models.session import UserSession

    _request, jti = _mint_niam_token(account.uuid)
    session_row = UserSession(
        id="sess-nr038-admin", uuid=str(uuid.uuid4()), account_id=account.id,
        token_jti=jti, session_type="web", is_active=True,
        started_at=_now(), last_activity_at=_now(), expires_at=_now() + timedelta(hours=1),
    )
    db.add(session_row)
    db.flush()

    from app.identity.api.workspaces import NiamActor

    actor = NiamActor(account=account, session=session_row)
    with pytest.raises(HTTPException) as denied:
        _require_assurance_administrator(db, actor)
    assert denied.value.status_code == 403


def test_a_deactivated_organization_loses_its_workspaces_nr043(db) -> None:
    """AUTH-F5 / NR-043 — the narrowing, executed against PostgreSQL.

    `list_eligible` returned an organization's workspaces to an account with an
    active representative record without checking that the organization itself
    was still live, so a representative of a deactivated organization kept
    access. The fix has been correct-but-unrunnable since AUTH-005.

    One fact changes between the two assertions — the organization's standing —
    so what is proved is the predicate, not merely that the function returns a
    list.
    """
    from app.identity.models.administrative_structure import (
        OrganizationRepresentative,
        RepresentativeStatus,
    )
    from app.identity.models.workspace import Workspace, WorkspaceStatus
    from app.identity.services.workspace_service import WorkspaceService

    identity_id = _identity_chain(db, "nr043")
    account = Account(
        id="acct-nr043", uuid=str(uuid.uuid4()), identity_id=identity_id,
        status=AccountStatus.active.value, is_active=True, is_locked=False,
    )
    db.add(account)
    db.flush()

    organization = _niam_organization(db, org_key=f"org-nr043-{uuid.uuid4().hex[:6]}")
    workspace = Workspace(
        id=f"ws-nr043-{uuid.uuid4().hex[:6]}", uuid=str(uuid.uuid4()),
        workspace_key=f"wsk-nr043-{uuid.uuid4().hex[:8]}",
        workspace_type="organization", name="NR-043 Org Workspace", name_ar="مساحة",
        status=WorkspaceStatus.active.value, organization_id=organization.id,
        is_personal=False,
    )
    db.add(workspace)
    db.add(OrganizationRepresentative(
        uuid=str(uuid.uuid4()), organization_id=organization.id,
        account_id=account.id, status=RepresentativeStatus.active.value,
    ))
    db.flush()

    service = WorkspaceService(db)
    eligible_before = {w.id for w in service.list_eligible(account)}
    assert workspace.id in eligible_before, "an active organization's workspace was not offered"

    organization.is_active = False
    db.flush()

    eligible_after = {w.id for w in service.list_eligible(account)}
    assert workspace.id not in eligible_after, (
        "a representative of a deactivated organization kept its workspace"
    )

    organization.is_active = True
    organization.status = "suspended"
    db.flush()
    assert workspace.id not in {w.id for w in service.list_eligible(account)}, (
        "a suspended organization still offered its workspace"
    )
