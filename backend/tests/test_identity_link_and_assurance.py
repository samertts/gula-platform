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


def test_a_valid_actor_passes_the_gate_and_execution_continues_past_it(db, niam_session) -> None:
    """Phase 3.4/3.6 — the point of NR-044.1, proved over real HTTP.

    Before the conversion this request died in the dependency: the async actor
    raised `TypeError` before a statement reached PostgreSQL, so the response
    was a 500 and no gateway code ran at all.

    It now authenticates against PostgreSQL and execution carries on into the
    gateway. The response is 503, not 403, and that is *not* an authentication
    failure — it is NR-045: `CanonicalAuditService.record()` cannot insert into
    `niam_audit_entries` because it never sets the NOT NULL `uuid`, and the
    gateway audits before it denies. So the 503 is proof that we reached the
    audit-before-deny path, which is downstream of the gate.

    What this test pins, therefore, is: not 401 (the gate passed) and 503 with
    the gateway's own error envelope (execution reached the gateway's audit).
    When NR-045 is fixed this becomes 403 and this test must be updated to
    assert that — the failure is the signal, not a regression.
    """
    import os as _os

    account, _session_row, request = niam_session
    token = request.cookies["access_token"]

    _os.environ["GULA_CLINICAL_GATEWAY_MODE"] = "ON"
    try:
        response = _client(db).get(
            "/api/v1/clinical/patients", headers={"Authorization": f"Bearer {token}"}
        )
    finally:
        _os.environ.pop("GULA_CLINICAL_GATEWAY_MODE", None)

    assert response.status_code != 401, (
        "the gate rejected a valid actor — NR-044.1 has regressed"
    )
    assert response.status_code != 500, (
        "the request raised before reaching the gateway — the NR-044 TypeError is back"
    )
    assert response.status_code == 503, response.text
    assert response.json()["detail"]["error"]["code"] == "UNAVAILABLE", response.text
    assert account.id  # resolved out of PostgreSQL to get this far


def test_the_canonical_audit_writer_cannot_insert_a_row_nr045(db) -> None:
    """NR-045, pinned where it was found. Not caused by NR-044.1.

    `IdentityAuditEntry.uuid` is NOT NULL with no default.
    `AuditService` sets id/uuid/entry_hash/previous_hash explicitly;
    `CanonicalAuditService.record()` — the writer the clinical gateway uses for
    every allow and every deny — sets none of them. So the insert violates the
    constraint, `ClinicalGatewayAuditFailure` is raised, and every
    `/api/v1/clinical/*` request answers 503.

    It fails closed, so no clinical data escapes, but the gateway is inert and
    its audit trail is empty. This test asserts the defect so that fixing it
    fails here and this test is rewritten to pin the fix.
    """
    import asyncio

    from app.clinical_gateway.session_facade import SyncSessionAsyncFacade
    from app.identity.services.canonical_audit import AuditEventInput, CanonicalAuditService
    from sqlalchemy.exc import IntegrityError

    service = CanonicalAuditService(SyncSessionAsyncFacade(db))
    with pytest.raises(IntegrityError) as exc:
        asyncio.run(
            service.record(
                AuditEventInput(
                    event_type="clinical_gateway_access", category="clinical_access",
                    action="patients.read", actor_id="acct-nr045",
                    actor_identity_id="ident-nr045", target_type="clinical_patient",
                    decision="deny", reason_code="missing_workspace",
                    request_id=str(uuid.uuid4()), correlation_id=str(uuid.uuid4()),
                    session_id="sess-nr045", source="clinical_gateway",
                    data_classification="CLINICAL_SENSITIVE", outcome="denied",
                ),
            ),
        )
    assert "niam_audit_entries" in str(exc.value)
    assert "uuid" in str(exc.value)


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
