"""AUTH-004: the boundaries that must hold between account, identity and patient.

GULA must never treat "I created an account" as "I proved who I am", nor "I
proved who I am" as "I may read this patient's record". Those are four
independent questions — account control, real-world identity, professional
standing, organizational legitimacy — and the platform's own
``VerificationRecordType`` already names them.

These tests pin the boundaries between them. Where a boundary currently holds,
they guard it. Where AUTH-004 found it broken, they pin the *defect* with the
evidence, so it cannot be lost: when the defect is fixed the test fails, and
that is the signal to rewrite it to pin the resolution — not to delete it.
"""

from __future__ import annotations

import inspect
import pathlib

import pytest
from app.identity.models.verification_record import VerificationRecordType
from app.identity.services.verification_record_service import (
    InvalidVerificationTransition,
    VerificationRecordService,
)
from app.identity.services.verification_service import (
    AssuranceEngine,
    AssuranceLevel,
    VerificationMethod,
    VerificationPolicy,
    VerificationPurpose,
    VerificationResult,
    VerificationStatus,
)

APP = pathlib.Path(__file__).resolve().parents[1] / "app"


def verified(method: VerificationMethod) -> VerificationResult:
    return VerificationResult(
        status=VerificationStatus.verified,
        assurance=AssuranceLevel.L3,
        provider="test-provider",
        method=method,
    )


# ── 1. the four purposes are not one scale ───────────────────────────────────


def test_the_purposes_the_record_names_are_the_purposes_the_policy_scores() -> None:
    """One vocabulary, not two.

    ``VerificationRecordType`` (persisted) and ``VerificationPurpose`` (scored)
    must stay the same set, or a record will be filed under a category the
    assurance engine cannot reason about.
    """
    assert {p.value for p in VerificationPurpose} == {t.value for t in VerificationRecordType}


def test_proving_an_organization_never_proves_who_the_account_holder_is() -> None:
    results = [verified(VerificationMethod.organization_registry)]
    assert AssuranceEngine.level_for(results, VerificationPurpose.organization) == AssuranceLevel.L2
    assert AssuranceEngine.level_for(results, VerificationPurpose.identity) == AssuranceLevel.L0
    with pytest.raises(PermissionError):
        AssuranceEngine.require(results, VerificationPurpose.identity, AssuranceLevel.L2)


def test_proving_a_licence_never_proves_who_the_account_holder_is() -> None:
    """A registry says a licence exists, not that this human holds it."""
    results = [verified(VerificationMethod.professional_registry)]
    assert AssuranceEngine.level_for(results, VerificationPurpose.identity) == AssuranceLevel.L0


def test_receiving_a_code_proves_contact_and_nothing_further() -> None:
    """The OTP boundary. This is the whole of what /auth/verification proves."""
    results = [verified(VerificationMethod.email), verified(VerificationMethod.phone)]
    assert AssuranceEngine.level_for(results, VerificationPurpose.contact) == AssuranceLevel.L1
    for purpose in (VerificationPurpose.identity, VerificationPurpose.professional,
                    VerificationPurpose.organization):
        assert AssuranceEngine.level_for(results, purpose) == AssuranceLevel.L0


def test_a_capture_technique_is_not_an_attestation() -> None:
    """OCR reads a document and NFC reads a chip. Neither vouches for it.

    They stay at L0 until an authority validates what was captured, so a
    deployment cannot reach identity assurance by buying a scanner.
    """
    for method in (VerificationMethod.ocr, VerificationMethod.nfc):
        assert VerificationPolicy.purpose_for(method) == VerificationPurpose.identity
        assert VerificationPolicy.assurance_for(verified(method)) == AssuranceLevel.L0


# ── 2. the provider does not grade its own work ──────────────────────────────


def test_a_provider_cannot_declare_its_own_assurance() -> None:
    claim = VerificationResult(
        status=VerificationStatus.verified,
        assurance=AssuranceLevel.L3,
        provider="hostile-provider",
        method=VerificationMethod.email,
    )
    assert VerificationPolicy.assurance_for(claim) == AssuranceLevel.L1


def test_an_unverified_status_carries_no_assurance_whatever_it_claims() -> None:
    for status in VerificationStatus:
        if status == VerificationStatus.verified:
            continue
        claim = VerificationResult(
            status=status, assurance=AssuranceLevel.L3,
            provider="p", method=VerificationMethod.official_identity,
        )
        assert VerificationPolicy.assurance_for(claim) == AssuranceLevel.L0, status


# ── 3. the state machine is the only way to become verified ──────────────────


def test_a_failed_verification_cannot_be_promoted_straight_to_verified() -> None:
    from app.identity.models.verification_record import VerificationRecord, VerificationRecordStatus

    item = VerificationRecord(status=VerificationRecordStatus.failed.value)
    with pytest.raises(InvalidVerificationTransition):
        VerificationRecordService.transition(item, VerificationRecordStatus.verified)


def test_revocation_drops_assurance_rather_than_leaving_it_standing() -> None:
    """Recovery and revocation must not leave privileges attached to a
    withdrawn proof."""
    from app.identity.models.verification_record import VerificationRecord, VerificationRecordStatus

    item = VerificationRecord(status=VerificationRecordStatus.verified.value)
    item.assurance_level = AssuranceLevel.L2.value
    VerificationRecordService.revoke(item)
    assert item.assurance_level == AssuranceLevel.L0.value
    assert item.is_active is False


# ── 4. registration creates a claim, never a proven person or a patient ──────


def test_citizen_self_registration_asserts_nothing_it_has_not_proven() -> None:
    """Account != Person != Patient, read from the only path that creates one.

    ``/register/citizen`` writes a ``users`` row and an MPI ``Citizen``. Both
    are marked unproven, and neither a Patient nor a ``niam_persons`` row is
    created. A bridge backfill that asserted a Person would convert every one
    of these unproven claims into a proven identity — which is why AUTH-F10
    blocks rather than proceeds.
    """
    source = (APP / "routes" / "register.py").read_text(encoding="utf-8")
    assert "nid_verified=False" in source, "self-registration claims a proven national ID"
    assert "is_verified=False" in source, "self-registration claims a verified account"
    assert "Patient(" not in source, "registration creates a clinical record"
    assert "niam_persons" not in source and "IdentityRecord(" not in source, (
        "registration asserts a canonical Person"
    )


# ── 5. defects AUTH-004 found, pinned with their evidence ────────────────────


def test_defect_one_boolean_serves_two_different_verification_purposes() -> None:
    """AUTH-V3 — ``users.is_verified`` means two incompatible things.

    ``POST /auth/verification/confirm`` sets it from a six-digit code sent to
    an email address or phone — that is *contact* assurance, L1. ``PUT
    /admin/citizens/{id}/verify`` sets the same column and calls it identity
    confirmation. Nothing records which one happened, so a downstream reader
    cannot tell an OTP from a ministry identity check.

    When the column is split by purpose, or replaced by verification records,
    this test fails. Rewrite it to pin the resolution.
    """
    otp = (APP / "routes" / "verification.py").read_text(encoding="utf-8")
    admin = (APP / "routes" / "admin.py").read_text(encoding="utf-8")

    assert "user.is_verified = True" in otp, "the OTP path no longer writes the shared boolean"
    assert "citizen.is_verified = True" in admin, "the admin path no longer writes it"
    assert "identity confirmed" in admin or "identity verified" in admin, (
        "the admin path no longer describes itself as identity verification"
    )
    # And neither path records what was actually proven:
    for name, source in (("otp", otp), ("admin", admin)):
        assert "VerificationRecord" not in source, (
            f"the {name} path now writes a verification record — AUTH-V3 has moved"
        )


def test_defect_a_health_data_linkage_gate_reads_the_ambiguous_boolean() -> None:
    """AUTH-V3, downstream. Where the conflation actually bites.

    ``CitizenRelationshipService.activate`` links a legacy account to a citizen
    and a patient, with a scope — it grants sight of a person's health data. It
    refuses unless the source account is "active and verified". That gate reads
    the boolean an OTP sets, while its message means identity.

    The activation is ministry-authorized, so this is a misinformed human
    decision rather than a self-service escalation. That is why it is recorded
    and tested rather than silently re-gated: what assurance a ministry actor
    must have before linking health data is a policy decision, not a patch.
    """
    source = (APP / "identity" / "services" / "citizen_relationship_service.py").read_text(
        encoding="utf-8"
    )
    assert "not source.is_verified" in source, "the gate changed; re-derive AUTH-V3"
    assert "AssuranceEngine" not in source, (
        "the linkage now consults the assurance engine — AUTH-V3 is resolved, rewrite this test"
    )


def test_defect_the_client_supplies_its_own_identity_assurance_level() -> None:
    """AUTH-V1 — ``POST /niam/trust/assurance-profiles`` takes the answer.

    ``ial``, ``aal``, ``fal``, ``assessed_by`` and ``evidence`` all arrive from
    the caller and are written with ``status="active"``. No verification record
    is consulted, and the caller names its own assessor. The route is behind
    NIAM authentication, which the application cannot currently reach with a
    legacy token — so this is latent in exactly the way NR-035 was, and goes
    live with the bridge.
    """
    from app.identity.trust import routes as trust_routes

    params = inspect.signature(trust_routes.create_assurance_profile).parameters
    for client_supplied in ("ial", "aal", "fal", "assessed_by", "evidence"):
        assert client_supplied in params, (
            f"{client_supplied} is no longer a request parameter — AUTH-V1 may be resolved"
        )

    source = (APP / "identity" / "trust" / "services.py").read_text(encoding="utf-8")
    assert "VerificationRecord" not in source and "AssuranceEngine" not in source, (
        "the trust service now derives assurance from verification evidence; "
        "AUTH-V1 is resolved and this test must be rewritten to pin that"
    )


def test_defect_authentication_strength_raises_identity_assurance() -> None:
    """AUTH-V2, second vocabulary. ``_calculate_overall`` averages three axes.

    IAL (who you are), AAL (how you signed in) and FAL (how you federated) are
    independent. Averaging them lets a hardware key and a strong federation
    lift an identity that was never proofed beyond IAL1 to an overall IAL2 —
    the same substitution the L0-L5 ladder allowed, in different notation.
    """
    from app.identity.trust.models import AAL1, AAL3, FAL1, FAL3, IAL1
    from app.identity.trust.services import AssuranceService

    calculate = AssuranceService.__dict__["_calculate_overall"]

    class _Unbound:
        pass

    weak = calculate(_Unbound(), IAL1, AAL1, FAL1)
    strong_auth_only = calculate(_Unbound(), IAL1, AAL3, FAL3)
    assert weak == IAL1
    assert strong_auth_only != IAL1, (
        "the averaging was removed — AUTH-V2's second half is resolved, rewrite this test"
    )


def test_defect_the_canonical_verification_domain_is_wired_to_nothing() -> None:
    """AUTH-V4 — built, migrated, unit-tested, and called by no route.

    ``niam_verification_records`` exists and is migration-backed; the record
    service, the provider protocol and the assurance engine are all present.
    No production module constructs a record or calls the service, so every
    verification the platform actually performs happens outside the model
    designed to hold it.
    """
    callers = sorted(
        path.relative_to(APP).as_posix()
        for path in APP.rglob("*.py")
        if "__pycache__" not in path.parts
        and "VerificationRecordService" in path.read_text(encoding="utf-8", errors="ignore")
    )
    assert callers == ["identity/services/verification_record_service.py"], (
        f"the verification domain gained callers: {callers}. AUTH-V4 is moving — "
        "check each caller records method, purpose and assurance, then rewrite this test."
    )
