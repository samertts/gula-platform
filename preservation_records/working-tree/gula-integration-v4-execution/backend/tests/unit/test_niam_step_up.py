"""Adversarial regression tests for functional NIAM step-up authentication.

All principals, sessions and evidence are created with disposable synthetic
data in an in-memory SQLite database. No operational DB, Redis, HTTP or real
identity data is used.
"""

from __future__ import annotations

import asyncio
import importlib.util
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import app.identity.services.step_up_service as step_up_module
import pyotp
import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from app._compat import UTC
from app.config import (
    NIAM_STEP_UP_FRESHNESS_SECONDS_DEFAULT,
    load_niam_step_up_freshness_seconds,
)
from app.database import AsyncCompatSession
from app.identity.base import IdentityBase
from app.identity.models.account import Account
from app.identity.models.audit import IdentityAuditEntry
from app.identity.models.session import UserSession
from app.identity.models.step_up import NiamStepUpEvent
from app.identity.services.step_up_service import (
    StepUpConfigurationError,
    StepUpDenied,
    StepUpService,
)
from sqlalchemy import MetaData, create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from shared.auth.mfa import generate_totp_secret

_FRESHNESS = NIAM_STEP_UP_FRESHNESS_SECONDS_DEFAULT


def _identity_metadata_subset() -> MetaData:
    """Only the tables step-up needs, plus their FK closure."""
    from app.database import Base

    combined = MetaData()
    for metadata in (Base.metadata, IdentityBase.metadata):
        for table in metadata.tables.values():
            if table.name not in combined.tables:
                table.to_metadata(combined)
    roots = (
        "niam_step_up_events",
        "niam_audit_entries",
        "niam_sessions",
        "niam_accounts",
    )
    needed: set[str] = set()

    def visit(name: str) -> None:
        if name in needed or name not in combined.tables:
            return
        needed.add(name)
        for fk in combined.tables[name].foreign_keys:
            visit(fk.target_fullname.split(".", 1)[0])

    for root in roots:
        visit(root)
    subset = MetaData()
    for name in sorted(needed):
        combined.tables[name].to_metadata(subset)
    return subset


@pytest.fixture()
def step_db():
    engine = create_engine("sqlite://")
    _identity_metadata_subset().create_all(engine)
    sync = Session(engine)
    try:
        yield AsyncCompatSession(sync)
    finally:
        sync.close()
        engine.dispose()


def _make_actor(
    db,
    *,
    secret: str | None = None,
    mfa_enabled: bool = True,
    methods: str = "totp",
    account_id: str = "ACCOUNT-0000000000000000000001",
    session_id: str = "SESSION-0000000000000000000001",
    jti: str = "jti-admin-1",
):
    account = Account(
        id=account_id,
        uuid=f"uuid-{account_id}",
        identity_id="IDENTITY-0000000000001",
        account_type="human",
        status="active",
        is_active=True,
        mfa_enabled=mfa_enabled,
        mfa_methods=methods,
        mfa_secret=secret or generate_totp_secret(),
    )
    now = datetime.now(UTC)
    session = UserSession(
        id=session_id,
        uuid=f"uuid-{session_id}",
        account_id=account_id,
        token_jti=jti,
        session_type="web",
        is_active=True,
        started_at=now,
        last_activity_at=now,
        expires_at=now + timedelta(days=1),
        mfa_used=False,
    )
    db.add(account)
    db.add(session)
    db.flush()
    actor = SimpleNamespace(
        account=SimpleNamespace(id=account.id),
        session=SimpleNamespace(id=session.id, token_jti=session.token_jti),
    )
    return actor, account, session


async def _verify(step_db, actor, secret: str):
    return await StepUpService(step_db, freshness_seconds=_FRESHNESS).verify(
        actor, pyotp.TOTP(secret).now(), "totp"
    )


# ── legitimate workflow ───────────────────────────────────────────────────────

async def test_self_mfa_creates_fresh_evidence_and_assert_passes(step_db):
    secret = generate_totp_secret()
    actor, _, _ = _make_actor(step_db, secret=secret)
    event = await _verify(step_db, actor, secret)
    assert event.mfa_method == "totp"
    assert event.verified_at <= datetime.now(UTC)
    checked = await StepUpService(step_db, freshness_seconds=_FRESHNESS).assert_fresh(
        actor, purpose="synthetic_cross_account_read"
    )
    assert checked.id == event.id


async def test_success_is_written_to_immutable_audit_log(step_db):
    secret = generate_totp_secret()
    actor, _, _ = _make_actor(step_db, secret=secret)
    await _verify(step_db, actor, secret)
    entries = step_db.query(IdentityAuditEntry).all()
    assert any(entry.action == "mfa_verified" and entry.outcome == "success" for entry in entries)


# ── freshness boundary (owner-approved 300s) ─────────────────────────────────

class _FrozenClock:
    """Deterministic clock for exact freshness-boundary assertions."""

    def __init__(self, value: datetime) -> None:
        self.value = value

    def now(self, tz=None):
        return self.value


@pytest.mark.parametrize(
    ("elapsed", "accepted"),
    [(299, True), (_FRESHNESS, True), (_FRESHNESS + 1, False)],
)
async def test_freshness_boundary_299_300_301(step_db, monkeypatch, elapsed, accepted):
    fixed = datetime.now(UTC).replace(microsecond=0)
    monkeypatch.setattr(step_up_module, "datetime", _FrozenClock(fixed))
    secret = generate_totp_secret()
    actor, _, _ = _make_actor(step_db, secret=secret)
    event = await _verify(step_db, actor, secret)
    event.verified_at = fixed - timedelta(seconds=elapsed)
    event.expires_at = fixed + timedelta(seconds=_FRESHNESS) - timedelta(seconds=elapsed)
    step_db.flush()
    service = StepUpService(step_db, freshness_seconds=_FRESHNESS)
    if accepted:
        assert (await service.assert_fresh(actor, purpose="boundary")).id == event.id
    else:
        with pytest.raises(StepUpDenied, match="stale_step_up_evidence"):
            await service.assert_fresh(actor, purpose="boundary")


async def test_future_timestamp_clock_skew_fails_closed(step_db):
    secret = generate_totp_secret()
    actor, _, _ = _make_actor(step_db, secret=secret)
    event = await _verify(step_db, actor, secret)
    event.verified_at = datetime.now(UTC) + timedelta(seconds=30)
    step_db.flush()
    with pytest.raises(StepUpDenied, match="clock_skew_rejected"):
        await StepUpService(step_db, freshness_seconds=_FRESHNESS).assert_fresh(actor, purpose="skew")


# ── replay / substitution / revocation ───────────────────────────────────────

async def test_replay_of_same_factor_code_is_rejected(step_db):
    secret = generate_totp_secret()
    actor, _, _ = _make_actor(step_db, secret=secret)
    code = pyotp.TOTP(secret).now()
    await StepUpService(step_db, freshness_seconds=_FRESHNESS).verify(actor, code, "totp")
    with pytest.raises(StepUpDenied, match="replay_detected"):
        await StepUpService(step_db, freshness_seconds=_FRESHNESS).verify(actor, code, "totp")


async def test_session_substitution_invalidates_evidence(step_db):
    secret = generate_totp_secret()
    actor, _, _ = _make_actor(step_db, secret=secret)
    await _verify(step_db, actor, secret)
    substituted = SimpleNamespace(
        account=SimpleNamespace(id=actor.account.id),
        session=SimpleNamespace(id="SESSION-0000000000000000000099", token_jti="jti-other"),
    )
    with pytest.raises(StepUpDenied):
        await StepUpService(step_db, freshness_seconds=_FRESHNESS).assert_fresh(
            substituted, purpose="substitution"
        )


async def test_token_jti_substitution_on_same_session_invalidates(step_db):
    secret = generate_totp_secret()
    actor, _, _ = _make_actor(step_db, secret=secret)
    await _verify(step_db, actor, secret)
    tampered = SimpleNamespace(
        account=SimpleNamespace(id=actor.account.id),
        session=SimpleNamespace(id=actor.session.id, token_jti="jti-refreshed"),
    )
    with pytest.raises(StepUpDenied, match="session_substitution"):
        await StepUpService(step_db, freshness_seconds=_FRESHNESS).assert_fresh(
            tampered, purpose="substitution"
        )


async def test_account_substitution_invalidates_evidence(step_db):
    secret = generate_totp_secret()
    actor, _, _ = _make_actor(step_db, secret=secret)
    await _verify(step_db, actor, secret)
    substituted = SimpleNamespace(
        account=SimpleNamespace(id="ACCOUNT-0000000000000000000099"),
        session=SimpleNamespace(id=actor.session.id, token_jti=actor.session.token_jti),
    )
    with pytest.raises(StepUpDenied):
        await StepUpService(step_db, freshness_seconds=_FRESHNESS).assert_fresh(
            substituted, purpose="substitution"
        )


async def test_revoked_session_invalidates_evidence(step_db):
    secret = generate_totp_secret()
    actor, _, session = _make_actor(step_db, secret=secret)
    await _verify(step_db, actor, secret)
    session.is_active = False
    session.terminated_at = datetime.now(UTC)
    step_db.flush()
    with pytest.raises(StepUpDenied, match="session_revoked"):
        await StepUpService(step_db, freshness_seconds=_FRESHNESS).assert_fresh(
            actor, purpose="revocation"
        )


async def test_expired_session_invalidates_evidence(step_db):
    secret = generate_totp_secret()
    actor, _, session = _make_actor(step_db, secret=secret)
    await _verify(step_db, actor, secret)
    session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    step_db.flush()
    with pytest.raises(StepUpDenied, match="session_expired"):
        await StepUpService(step_db, freshness_seconds=_FRESHNESS).assert_fresh(
            actor, purpose="expiry"
        )


# ── factor revocation / bypass / cross-account ───────────────────────────────

@pytest.mark.parametrize(
    "revocation",
    ["disabled", "secret_rotated", "method_removed"],
)
async def test_factor_revocation_invalidates_evidence(step_db, revocation):
    secret = generate_totp_secret()
    actor, account, _ = _make_actor(step_db, secret=secret)
    await _verify(step_db, actor, secret)
    if revocation == "disabled":
        account.mfa_enabled = False
    elif revocation == "secret_rotated":
        account.mfa_secret = generate_totp_secret()
    else:
        account.mfa_methods = "webauthn"
    step_db.flush()
    with pytest.raises(StepUpDenied):
        await StepUpService(step_db, freshness_seconds=_FRESHNESS).assert_fresh(
            actor, purpose="factor_revocation"
        )


async def test_missing_evidence_fails_closed(step_db):
    secret = generate_totp_secret()
    actor, _, _ = _make_actor(step_db, secret=secret)
    with pytest.raises(StepUpDenied, match="no_step_up_evidence"):
        await StepUpService(step_db, freshness_seconds=_FRESHNESS).assert_fresh(
            actor, purpose="bypass"
        )


async def test_cross_account_factor_code_cannot_establish_step_up(step_db):
    admin_secret = generate_totp_secret()
    other_secret = generate_totp_secret()
    admin, _, _ = _make_actor(
        step_db,
        secret=admin_secret,
        account_id="ACCOUNT-0000000000000000000001",
        session_id="SESSION-0000000000000000000001",
        jti="jti-admin-1",
    )
    _make_actor(
        step_db,
        secret=other_secret,
        account_id="ACCOUNT-0000000000000000000002",
        session_id="SESSION-0000000000000000000002",
        jti="jti-other-2",
    )
    with pytest.raises(StepUpDenied, match="factor_verification_failed"):
        await StepUpService(step_db, freshness_seconds=_FRESHNESS).verify(
            admin, pyotp.TOTP(other_secret).now(), "totp"
        )


async def test_invalid_code_format_and_unsupported_method_fail_closed(step_db):
    secret = generate_totp_secret()
    actor, _, _ = _make_actor(step_db, secret=secret)
    service = StepUpService(step_db, freshness_seconds=_FRESHNESS)
    with pytest.raises(StepUpDenied, match="invalid_factor_code"):
        await service.verify(actor, "12345", "totp")
    with pytest.raises(StepUpDenied, match="unsupported_factor"):
        await service.verify(actor, "123456", "sms")


async def test_ambiguous_evidence_fails_closed(step_db):
    secret = generate_totp_secret()
    actor, account, session = _make_actor(step_db, secret=secret)
    event = await _verify(step_db, actor, secret)
    twin_id = "STEP-0000000000000000000099"
    step_db.add(
        type(event)(
            id=twin_id,
            uuid=f"uuid-{twin_id}",
            event_id=f"EVENT-{twin_id}",
            account_id=account.id,
            session_id=session.id,
            session_jti=session.token_jti,
            mfa_method="totp",
            code_fingerprint="f" * 64,
            factor_fingerprint="a" * 64,
            verified_at=event.verified_at,
            expires_at=event.expires_at,
            is_active=True,
        )
    )
    step_db.flush()
    with pytest.raises(StepUpDenied, match="ambiguous_step_up_evidence"):
        await StepUpService(step_db, freshness_seconds=_FRESHNESS).assert_fresh(
            actor, purpose="ambiguity"
        )


# ── configuration fail-closed ────────────────────────────────────────────────

@pytest.mark.parametrize("bad_value", ["abc", "0", "-1", "29", "3601", ""])
def test_invalid_configuration_fails_closed(step_db, monkeypatch, bad_value):
    secret = generate_totp_secret()
    actor, _, _ = _make_actor(step_db, secret=secret)
    monkeypatch.setenv("NIAM_STEP_UP_FRESHNESS_SECONDS", bad_value)
    service = StepUpService(step_db)
    with pytest.raises(StepUpConfigurationError):
        asyncio.run(service.verify(actor, pyotp.TOTP(secret).now(), "totp"))


def test_config_loader_default_and_valid_override(monkeypatch):
    monkeypatch.delenv("NIAM_STEP_UP_FRESHNESS_SECONDS", raising=False)
    assert load_niam_step_up_freshness_seconds() == 300
    monkeypatch.setenv("NIAM_STEP_UP_FRESHNESS_SECONDS", "45")
    assert load_niam_step_up_freshness_seconds() == 45


def test_step_up_endpoint_accepts_no_client_identity_claims():
    """Cross-account MFA completion is structurally impossible on this route."""
    from app.main import app

    schema = app.openapi()
    operation = schema["paths"]["/niam/auth/step-up/verify"]["post"]
    body_schema = operation["requestBody"]["content"]["application/json"]["schema"]
    model_name = body_schema["$ref"].rsplit("/", 1)[-1]
    properties = schema["components"]["schemas"][model_name]["properties"]
    assert set(properties) == {"code", "method"}


# ── suspended / locked accounts (directive: item 13) ─────────────────────────

@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda account: setattr(account, "status", "suspended"), "account_inactive"),
        (lambda account: setattr(account, "status", "locked"), "account_inactive"),
        (lambda account: setattr(account, "status", "disabled"), "account_inactive"),
        (lambda account: setattr(account, "status", "deactivated"), "account_inactive"),
        (lambda account: setattr(account, "is_active", False), "account_inactive"),
        (lambda account: setattr(account, "is_locked", True), "account_inactive"),
    ],
)
async def test_suspended_or_locked_account_invalidates_evidence(step_db, mutate, reason):
    secret = generate_totp_secret()
    actor, account, _ = _make_actor(step_db, secret=secret)
    await _verify(step_db, actor, secret)
    mutate(account)
    step_db.flush()
    with pytest.raises(StepUpDenied, match=reason):
        await StepUpService(step_db, freshness_seconds=_FRESHNESS).assert_fresh(
            actor, purpose="account_state"
        )


async def test_suspended_account_cannot_stage_new_evidence(step_db):
    secret = generate_totp_secret()
    actor, account, _ = _make_actor(step_db, secret=secret)
    account.status = "suspended"
    step_db.flush()
    with pytest.raises(StepUpDenied, match="account_inactive"):
        await StepUpService(step_db, freshness_seconds=_FRESHNESS).verify(
            actor, pyotp.TOTP(secret).now(), "totp"
        )


# ── concurrent verification attempts (directive: item 14) ───────────────────

async def test_concurrent_same_code_verification_yields_single_event(step_db):
    secret = generate_totp_secret()
    actor, _, _ = _make_actor(step_db, secret=secret)
    code = pyotp.TOTP(secret).now()
    results = await asyncio.gather(
        StepUpService(step_db, freshness_seconds=_FRESHNESS).verify(actor, code, "totp"),
        StepUpService(step_db, freshness_seconds=_FRESHNESS).verify(actor, code, "totp"),
        return_exceptions=True,
    )
    successes = [r for r in results if not isinstance(r, BaseException)]
    denials = [r for r in results if isinstance(r, StepUpDenied)]
    assert len(successes) == 1
    assert len(denials) == 1
    events = step_db.query(NiamStepUpEvent).all()
    assert len(events) == 1


def test_duplicate_code_fingerprint_rejected_at_database_level(step_db):
    """A concurrent racing insert cannot persist a second evidence row."""
    from app.identity.models.step_up import NiamStepUpEvent

    secret = generate_totp_secret()
    _, account, session = _make_actor(step_db, secret=secret)
    from app.identity.services.step_up_service import _CODE_DOMAIN, _fingerprint

    fp = _fingerprint(_CODE_DOMAIN, account.id, pyotp.TOTP(secret).now())
    now = datetime.now(UTC)
    step_db.add(
        NiamStepUpEvent(
            uuid="uuid-a",
            event_id="EVENT-A",
            account_id=account.id,
            session_id=session.id,
            session_jti=session.token_jti,
            mfa_method="totp",
            code_fingerprint=fp,
            factor_fingerprint="f" * 64,
            verified_at=now,
            expires_at=now + timedelta(seconds=_FRESHNESS),
            is_active=True,
        )
    )
    step_db.flush()
    step_db.add(
        NiamStepUpEvent(
            uuid="uuid-b",
            event_id="EVENT-B",
            account_id=account.id,
            session_id=session.id,
            session_jti=session.token_jti,
            mfa_method="totp",
            code_fingerprint=fp,
            factor_fingerprint="f" * 64,
            verified_at=now,
            expires_at=now + timedelta(seconds=_FRESHNESS),
            is_active=True,
        )
    )
    with pytest.raises(IntegrityError):
        step_db.flush()
    step_db.rollback()


# ── migration upgrade/downgrade on disposable DB (directive: item 18) ────────

def test_step_up_migration_upgrade_and_downgrade(tmp_path):
    """The migration creates and cleanly removes its table on a throwaway DB."""
    import sqlalchemy as sa

    migration_path = (
        Path(__file__).resolve().parents[2]
        / "migrations/versions/20261119_0001_niam_step_up_events.py"
    )
    spec = importlib.util.spec_from_file_location("step_up_migration", migration_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    engine = create_engine(f"sqlite:///{tmp_path / 'migration.db'}")
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE niam_accounts (id VARCHAR(26) PRIMARY KEY)"))
        conn.execute(sa.text("CREATE TABLE niam_sessions (id VARCHAR(26) PRIMARY KEY)"))

    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        module.op = Operations(ctx)
        module.upgrade()
        inspector = inspect(conn)
        assert "niam_step_up_events" in inspector.get_table_names()
        columns = {c["name"] for c in inspector.get_columns("niam_step_up_events")}
        assert {
            "account_id", "session_id", "session_jti", "mfa_method",
            "code_fingerprint", "factor_fingerprint", "verified_at", "expires_at",
        }.issubset(columns)
        uniques = {
            c["name"] for c in inspector.get_unique_constraints("niam_step_up_events")
        }
        assert "uq_niam_step_up_account_code" in uniques

        module.downgrade()
        assert "niam_step_up_events" not in inspect(conn).get_table_names()
    engine.dispose()
