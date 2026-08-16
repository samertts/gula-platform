"""Read-only legacy/NIAM parity proofs used before any migration decision."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from app.identity.models.account import Account, AccountStatus
from app.identity.models.legacy_account_link import LegacyAccountLink, LegacyAccountLinkStatus


@dataclass(frozen=True, slots=True)
class IdentityParityResult:
    """Minimal, non-PII parity result; it is not an authorization decision."""

    source_kind: str
    legacy_account_id: int
    canonical_account_id: str | None
    mapping_version: int
    link_status: str
    legacy_active: bool
    canonical_active: bool
    canonical_status: str
    role_match: bool | None
    ready_for_review: bool
    reasons: tuple[str, ...]


def evaluate_identity_parity(
    link: LegacyAccountLink,
    legacy_account: object,
    canonical_account: Account,
    *,
    role_mapping: Mapping[str, set[str]] | None = None,
    canonical_roles: set[str] | None = None,
) -> IdentityParityResult:
    """Compare only the fields required for a reviewed, read-only parity proof.

    The function never writes either account, copies credentials, or grants access.
    ``ready_for_review`` means that an operator may review the result; it does not
    mean that a migration or single-write cutover is approved.
    """
    reasons: list[str] = []
    canonical_ids = {
        str(value)
        for value in (
            getattr(canonical_account, "id", None),
            getattr(canonical_account, "uuid", None),
        )
        if value is not None
    }
    linked_canonical_id = str(getattr(link, "canonical_account_id", ""))
    legacy_active = bool(getattr(legacy_account, "is_active", False))
    canonical_active = bool(getattr(canonical_account, "is_active", False))
    canonical_status = str(getattr(canonical_account, "status", ""))

    if getattr(link, "status", None) != LegacyAccountLinkStatus.migrated.value:
        reasons.append("link_not_migrated")
    if not linked_canonical_id or linked_canonical_id not in canonical_ids:
        reasons.append("canonical_account_mismatch")
    if not legacy_active:
        reasons.append("legacy_account_inactive")
    if not canonical_active or canonical_status != AccountStatus.active.value:
        reasons.append("canonical_account_not_active")

    role_match: bool | None = None
    legacy_role = getattr(legacy_account, "role", None)
    if role_mapping is not None:
        role_match = bool(
            legacy_role
            and canonical_roles
            and set(role_mapping.get(str(legacy_role), set())).intersection(canonical_roles),
        )
        if not role_match:
            reasons.append("role_parity_missing")

    return IdentityParityResult(
        source_kind=str(getattr(link, "source_kind", "")),
        legacy_account_id=int(getattr(link, "legacy_account_id", 0)),
        canonical_account_id=linked_canonical_id or None,
        mapping_version=int(getattr(link, "mapping_version", 1) or 1),
        link_status=str(getattr(link, "status", "")),
        legacy_active=legacy_active,
        canonical_active=canonical_active,
        canonical_status=canonical_status,
        role_match=role_match,
        ready_for_review=not reasons,
        reasons=tuple(reasons),
    )


class IdentityParityService:
    """Read-only facade over a reviewed ``LegacyAccountLink`` record."""

    def evaluate(
        self,
        link: LegacyAccountLink,
        legacy_account: object,
        canonical_account: Account,
        *,
        role_mapping: Mapping[str, set[str]] | None = None,
        canonical_roles: set[str] | None = None,
    ) -> IdentityParityResult:
        return evaluate_identity_parity(
            link,
            legacy_account,
            canonical_account,
            role_mapping=role_mapping,
            canonical_roles=canonical_roles,
        )
