"""Command 06 read-only legacy/NIAM identity parity proofs."""

from types import SimpleNamespace

from app.identity.models.account import AccountStatus
from app.identity.models.legacy_account_link import LegacyAccountLinkStatus
from app.identity.services.identity_parity_service import evaluate_identity_parity


def _link(*, status: str = LegacyAccountLinkStatus.migrated.value, canonical_id: str = "canonical-1"):
    return SimpleNamespace(
        source_kind="user",
        legacy_account_id=42,
        canonical_account_id=canonical_id,
        mapping_version=3,
        status=status,
    )


def _legacy(*, active: bool = True, role: str = "doctor"):
    return SimpleNamespace(is_active=active, role=role)


def _canonical(*, account_id: str = "canonical-1", active: bool = True, status: str = AccountStatus.active.value):
    return SimpleNamespace(id=account_id, uuid="canonical-uuid", is_active=active, status=status)


def test_migrated_mapping_produces_reviewable_non_authoritative_parity():
    result = evaluate_identity_parity(
        _link(),
        _legacy(),
        _canonical(),
        role_mapping={"doctor": {"clinical.doctor"}},
        canonical_roles={"clinical.doctor"},
    )

    assert result.ready_for_review is True
    assert result.reasons == ()
    assert result.role_match is True
    assert result.canonical_account_id == "canonical-1"


def test_pending_mapping_is_blocked_before_any_cutover():
    result = evaluate_identity_parity(_link(status=LegacyAccountLinkStatus.pending.value), _legacy(), _canonical())

    assert result.ready_for_review is False
    assert result.reasons == ("link_not_migrated",)


def test_mismatch_and_inactive_accounts_are_blocked_without_raw_identity_values():
    result = evaluate_identity_parity(
        _link(canonical_id="other-canonical"),
        _legacy(active=False, role="nurse"),
        _canonical(active=False, status=AccountStatus.suspended.value),
        role_mapping={"doctor": {"clinical.doctor"}},
        canonical_roles={"clinical.nurse"},
    )

    assert result.ready_for_review is False
    assert set(result.reasons) == {
        "canonical_account_mismatch",
        "legacy_account_inactive",
        "canonical_account_not_active",
        "role_parity_missing",
    }
    assert not hasattr(result, "email")
    assert not hasattr(result, "phone")
    assert not hasattr(result, "password_hash")
