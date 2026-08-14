from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.identity.models.legacy_account_link import (
    LegacyAccountLink,
    LegacyAccountLinkSource,
    LegacyAccountLinkStatus,
)
from app.identity.services.legacy_mapping_service import (
    LegacyMappingRollbackDenied,
    LegacyMappingService,
    make_source_fingerprint,
)


@pytest.fixture
def pending_link() -> LegacyAccountLink:
    return LegacyAccountLink(
        id="01WAVE3LINK0000000000000001",
        source_kind=LegacyAccountLinkSource.user.value,
        legacy_account_id=42,
        source_fingerprint="a" * 64,
        status=LegacyAccountLinkStatus.pending.value,
        mapping_version=1,
        rollback_token="rollback-secret",
    )


def test_mapping_state_machine_allows_reviewed_forward_path(pending_link: LegacyAccountLink):
    pending_link.transition(LegacyAccountLinkStatus.validated, reason="dry-run passed")
    assert pending_link.status == LegacyAccountLinkStatus.validated.value
    assert pending_link.mapping_version == 2
    assert pending_link.validated_at is not None

    pending_link.transition(LegacyAccountLinkStatus.migrated, reason="approved cohort")
    assert pending_link.status == LegacyAccountLinkStatus.migrated.value
    assert pending_link.migrated_at is not None

    pending_link.transition(LegacyAccountLinkStatus.rolled_back, reason="authorization mismatch")
    assert pending_link.status == LegacyAccountLinkStatus.rolled_back.value
    assert pending_link.rolled_back_at is not None


def test_mapping_state_machine_rejects_skips_and_reasonless_safety_states(
    pending_link: LegacyAccountLink,
):
    with pytest.raises(ValueError, match="Invalid legacy account mapping transition"):
        pending_link.transition(LegacyAccountLinkStatus.migrated, reason="skip validation")

    with pytest.raises(ValueError, match="reason is required"):
        pending_link.transition(LegacyAccountLinkStatus.collision)

    pending_link.transition(LegacyAccountLinkStatus.collision, reason="email collision")
    with pytest.raises(ValueError, match="Invalid legacy account mapping transition"):
        pending_link.transition(LegacyAccountLinkStatus.migrated, reason="unsafe merge")


def test_source_fingerprint_is_stable_and_does_not_store_raw_identifier():
    first = make_source_fingerprint(LegacyAccountLinkSource.user, 42, "k" * 64)
    second = make_source_fingerprint("user", 42, "k" * 64)
    assert first == second
    assert len(first) == 64
    assert "42" not in first
    with pytest.raises(ValueError, match="at least 32"):
        make_source_fingerprint("user", 42, "short")


@pytest.mark.asyncio
async def test_service_rejects_invalid_rollback_token(pending_link: LegacyAccountLink):
    session = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = pending_link
    session.execute = AsyncMock(return_value=result)
    service = LegacyMappingService(session, "k" * 64)
    service.audit.record_event = AsyncMock()

    with pytest.raises(LegacyMappingRollbackDenied, match="Invalid rollback token"):
        await service.rollback(
            pending_link.id,
            "wrong-token",
            actor_id="operator-1",
            reason="test rollback",
        )
    assert pending_link.status == LegacyAccountLinkStatus.pending.value


def test_frontend_cookie_only_auth_regression():
    """The production frontend must use HttpOnly cookies for live sessions.

    Demo state is intentionally limited to sessionStorage markers and synthetic
    persona selection; it must not introduce bearer-token persistence.
    """
    from pathlib import Path

    root = Path(__file__).parents[2]
    client = (root / "frontend-v3/src/api/client.ts").read_text()
    auth_context = (root / "frontend-v3/src/contexts/AuthContext.tsx").read_text()

    assert "withCredentials: true" in client
    assert "localStorage.setItem('gula_access_token'" not in client
    assert "localStorage.setItem('gula_refresh_token'" not in client
    assert "Authorization: `Bearer ${token}`" not in client
    assert "localStorage.setItem(USER_KEY" not in auth_context
    assert "localStorage.getItem(USER_KEY" not in auth_context
    assert "sessionStorage.setItem(DEMO_SESSION_KEY" in auth_context
    assert "sessionStorage.setItem(DEMO_PERSONA_KEY" in auth_context
    assert "DEMO_API_BASE_URL = \"/demo-api\"" in client


def test_wave3_migration_is_additive_and_has_rollback_metadata():
    from pathlib import Path

    migration = (
        Path(__file__).parents[1]
        / "migrations/versions/20260811_0001_wave3_identity_mapping.py"
    ).read_text()
    assert 'down_revision = "20260723_0002"' in migration
    assert "niam_legacy_account_links" in migration
    assert "ondelete=\"SET NULL\"" in migration
    assert "niam_legacy_account_links_source" not in migration
    assert "users" not in migration.replace("legacy_account_links", "")
    assert "lab_users" not in migration.replace("legacy_account_links", "")
    assert "def downgrade" in migration
