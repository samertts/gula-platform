"""Whether an account may be linked to a health identity, and on what evidence.

GULA must never treat "I created an account" as "I proved who I am". The two
facts live in different places: an account is a row in ``users`` or
``niam_accounts``; a proof of identity is a ``VerificationRecord`` whose purpose
is ``identity``. Before AUTH-005 the linkage gate read ``users.is_verified`` —
a boolean an emailed six-digit code sets — and called it identity confirmation
(NR-039).

The chain this module walks, and refuses at the first gap:

    legacy account id + account kind        (NR-035: the kind is not optional)
      -> LegacyAccountLink, validated or migrated, exactly one
      -> canonical Account
      -> VerificationRecord, purpose=identity, state=verified, live
      -> AssuranceEngine, which recomputes the level from the method
      -> identity assurance >= L2

Two properties are deliberate.

**The stored assurance level is not trusted.** ``VerificationRecord`` carries an
``assurance_level`` column, but this module recomputes it from the record's
method through ``VerificationPolicy``. A column is a cache; the policy is the
authority. A row whose level was written by a compromised or buggy writer
cannot raise its own assurance (NR-038 applied to persisted data).

**Ambiguity fails closed, always.** No link, two links, a link in ``collision``,
an unknown method, an expired or revoked record — each returns a refusal with a
reason code, never a guess.

Authorization is a separate question and is not answered here. A ministry actor
authorizes the *operation*; a verification record establishes the *person*.
Both are required; neither substitutes for the other.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app._compat import UTC
from app.identity.models.legacy_account_link import (
    LegacyAccountLink,
    LegacyAccountLinkSource,
    LegacyAccountLinkStatus,
)
from app.identity.models.verification_record import (
    VerificationRecord,
    VerificationRecordStatus,
    VerificationRecordType,
)
from app.identity.services.verification_service import (
    AssuranceEngine,
    AssuranceLevel,
    AssuranceProfile,
    VerificationMethod,
    VerificationPurpose,
    VerificationResult,
    VerificationStatus,
)

# Linking an account to a person's health identity requires that an
# authoritative source established who that person is. L1 — a code arrived at
# an address they control — is not that.
IDENTITY_LINK_MINIMUM = AssuranceLevel.L2

# The link statuses that mean "this legacy account is the same account".
# `pending` is not evidence, `collision` is the opposite of evidence, and
# `blocked` and `rolled_back` are explicit refusals.
_USABLE_LINK_STATUSES = frozenset({
    LegacyAccountLinkStatus.validated.value,
    LegacyAccountLinkStatus.migrated.value,
})


@dataclass(frozen=True)
class LinkDecision:
    """Why the answer is what it is, in a form the audit log can carry."""

    allowed: bool
    reason_code: str
    detail: str
    identity_assurance: AssuranceLevel = AssuranceLevel.L0
    canonical_account_id: str | None = None
    evidence_ids: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return self.allowed


def _deny(code: str, detail: str, **extra) -> LinkDecision:
    return LinkDecision(allowed=False, reason_code=code, detail=detail, **extra)


def result_from_record(record: VerificationRecord, *, now: datetime | None = None) -> VerificationResult:
    """Read a persisted record as a verification result the engine can score.

    The record's own ``assurance_level`` is ignored. The method decides the
    level, through the same policy that scores a live provider response, so a
    stored row and a fresh result are graded identically.
    """
    now = now or datetime.now(UTC)

    status = VerificationStatus.failed
    if str(record.status) == VerificationRecordStatus.verified.value:
        expired = record.expires_at is not None and record.expires_at <= now
        if record.revoked_at is not None:
            status = VerificationStatus.revoked
        elif expired:
            status = VerificationStatus.expired
        elif record.is_active is False:
            status = VerificationStatus.revoked
        else:
            status = VerificationStatus.verified
    else:
        try:
            status = VerificationStatus(str(record.status))
        except ValueError:
            status = VerificationStatus.failed

    try:
        method = VerificationMethod(str(record.method))
    except ValueError:
        # An unmapped method proves nothing. `VerificationPolicy` returns L0 for
        # it, and naming it here keeps the reason legible in the decision.
        method = VerificationMethod.ocr

    return VerificationResult(
        status=status,
        assurance=AssuranceLevel.L0,
        provider=str(record.provider or "unknown"),
        method=method,
        provider_reference=record.provider_reference,
    )


def resolve_canonical_account(
    db: Session, *, legacy_account_id: int, source_kind: str,
) -> LinkDecision:
    """Find the one canonical account this legacy account is, or refuse.

    Mirrors NR-035 one level up: an integer id plus a kind, resolved to exactly
    one canonical identity, and refused when the evidence is absent or points
    two ways. These refusals are the AUTH-F10 dispositions expressed in code —
    nothing here guesses a mapping.
    """
    if source_kind not in {kind.value for kind in LegacyAccountLinkSource}:
        return _deny("unknown_account_kind", f"Unknown legacy account kind {source_kind!r}")

    links = (
        db.query(LegacyAccountLink)
        .filter(
            LegacyAccountLink.legacy_account_id == legacy_account_id,
            LegacyAccountLink.source_kind == source_kind,
        )
        .all()
    )
    if not links:
        return _deny(
            "no_identity_evidence",
            "This legacy account has no canonical identity mapping; it is PENDING_PROOFING",
        )

    usable = [link for link in links if str(link.status) in _USABLE_LINK_STATUSES]
    if not usable:
        statuses = sorted({str(link.status) for link in links})
        return _deny(
            "link_not_validated",
            f"No validated mapping for this account; statuses present: {statuses}",
        )
    if len({link.canonical_account_id for link in usable}) > 1:
        return _deny(
            "ambiguous_identity",
            "This legacy account maps to more than one canonical account; refusing rather than choosing",
        )

    canonical = usable[0].canonical_account_id
    if not canonical:
        return _deny("link_incomplete", "The validated mapping names no canonical account")
    return LinkDecision(
        allowed=True,
        reason_code="account_resolved",
        detail="Exactly one validated canonical account",
        canonical_account_id=canonical,
    )


def assurance_profile_for_account(
    db: Session, canonical_account_id: str, *, now: datetime | None = None,
) -> tuple[AssuranceProfile, tuple[str, ...]]:
    """What this account has actually proven, per purpose, with the evidence."""
    records = (
        db.query(VerificationRecord)
        .filter(VerificationRecord.account_id == canonical_account_id)
        .all()
    )
    results = [result_from_record(record, now=now) for record in records]
    profile = AssuranceEngine.profile_for(results)

    contributing = tuple(
        str(record.id)
        for record, result in zip(records, results, strict=True)
        if result.status == VerificationStatus.verified
    )
    return profile, contributing


def can_link_health_identity(
    db: Session,
    *,
    legacy_account_id: int,
    source_kind: str,
    target_citizen_id: str | None,
    now: datetime | None = None,
) -> LinkDecision:
    """May this account be linked to this person's health identity?

    Answers only the identity question. The caller must separately establish
    that the actor is authorized to perform the linkage — a ministry role
    authorizes the operation, it does not establish who the subject is.
    """
    if not target_citizen_id:
        return _deny("no_target_identity", "A deterministic target health identity is required")

    resolved = resolve_canonical_account(
        db, legacy_account_id=legacy_account_id, source_kind=source_kind,
    )
    if not resolved.allowed:
        return resolved

    account_id = resolved.canonical_account_id
    assert account_id is not None  # resolve_canonical_account guarantees it when allowed
    profile, evidence = assurance_profile_for_account(db, account_id, now=now)
    identity_level = profile.level_for(VerificationPurpose.identity)

    if not profile.meets(VerificationPurpose.identity, IDENTITY_LINK_MINIMUM):
        contact = profile.level_for(VerificationPurpose.contact)
        detail = (
            f"Identity assurance {identity_level.value} is below the required "
            f"{IDENTITY_LINK_MINIMUM.value}"
        )
        if contact != AssuranceLevel.L0 and identity_level == AssuranceLevel.L0:
            # The NR-039 case, named explicitly so the audit trail says why.
            detail += (
                "; this account has proven contact only — a delivered code is not "
                "evidence of who the holder is"
            )
        return _deny(
            "insufficient_identity_assurance", detail,
            identity_assurance=identity_level,
            canonical_account_id=account_id,
            evidence_ids=evidence,
        )

    return LinkDecision(
        allowed=True,
        reason_code="identity_assurance_satisfied",
        detail=f"Identity assurance {identity_level.value} meets {IDENTITY_LINK_MINIMUM.value}",
        identity_assurance=identity_level,
        canonical_account_id=account_id,
        evidence_ids=evidence,
    )


def identity_record_query(db: Session, canonical_account_id: str):
    """Identity-purpose records for an account, for callers that need the rows."""
    return db.query(VerificationRecord).filter(
        VerificationRecord.account_id == canonical_account_id,
        VerificationRecord.record_type == VerificationRecordType.identity.value,
    )
