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
