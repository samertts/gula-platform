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


def test_the_health_data_linkage_gate_now_reads_identity_evidence() -> None:
    """NR-039 — RESOLVED by AUTH-005.

    `CitizenRelationshipService.activate` links an account to a citizen and a
    patient, with a scope. It used to refuse unless the source account was
    "active and verified", reading the boolean an emailed six-digit code sets.
    It now consults `can_link_health_identity`, which requires identity-purpose
    assurance at L2 from a record only a trusted server-side verifier can write.

    The ministry authorization that guards the endpoint is unchanged and still
    required. It authorizes the *operation*; the verification record establishes
    the *person*. Neither substitutes for the other.
    """
    source = (APP / "identity" / "services" / "citizen_relationship_service.py").read_text(
        encoding="utf-8"
    )
    assert "can_link_health_identity" in source, "the identity gate was removed"
    assert "not source.is_verified" not in source, (
        "activation reads the ambiguous boolean again; NR-039 has regressed"
    )
    assert "identity_assurance" in source, "the activation record no longer states what was proven"


def test_the_assurance_endpoint_no_longer_accepts_an_answer() -> None:
    """NR-038 — RESOLVED by AUTH-005.

    `POST /niam/trust/assurance-profiles` used to take `ial`, `aal`, `fal`,
    `assessed_by` and `evidence` from the caller and write them with
    `status="active"`. The route now names a subject and nothing else: the
    profile is derived from `niam_verification_records` and the assessor is the
    authenticated actor.
    """
    from app.identity.trust import routes as trust_routes

    params = set(inspect.signature(trust_routes.create_assurance_profile).parameters)
    for client_authored in ("ial", "aal", "fal", "assessed_by", "evidence"):
        assert client_authored not in params, (
            f"{client_authored} is a request parameter again; NR-038 has regressed"
        )
    assert "account_id" in params, "the route no longer names the subject account"

    service = (APP / "identity" / "trust" / "services.py").read_text(encoding="utf-8")
    assert "AssuranceEngine" in service, (
        "the trust service no longer derives assurance from verification evidence"
    )


def test_authentication_strength_no_longer_raises_identity_assurance() -> None:
    """AUTH-V2's second half — RESOLVED by AUTH-005.

    `_calculate_overall` averaged IAL, AAL and FAL, so a hardware key and a
    strong federation lifted an identity proofed only to IAL1 up to an overall
    IAL2. Independent axes do not average: the overall is the weakest of them.
    """
    from app.identity.trust.models import AAL1, AAL3, FAL1, FAL3, IAL1, IAL3
    from app.identity.trust.services import AssuranceService

    calculate = AssuranceService.__dict__["_calculate_overall"]

    class _Unbound:
        pass

    assert calculate(_Unbound(), IAL1, AAL3, FAL3) == IAL1, (
        "strong authentication raised an unproofed identity again"
    )
    assert calculate(_Unbound(), IAL3, AAL1, FAL1) == IAL1, (
        "strong proofing hid weak authentication"
    )


def test_the_verification_domain_now_has_a_writer() -> None:
    """NR-040 — RESOLVED by AUTH-005.

    The domain was built, migrated, unit-tested and never written to. One place
    *read* it — `_professional_eligible` gates professional workspace creation
    on a verified professional record — so with no writer that query could only
    ever return nothing and professional workspaces were unreachable.

    `VerificationWorkflow` is the missing half. This pins that the writer exists
    and drives the existing state machine rather than bypassing it.
    """
    workflow_source = (
        APP / "identity" / "services" / "verification_workflow.py"
    ).read_text(encoding="utf-8")
    assert "VerificationRecord(" in workflow_source, "the workflow no longer creates records"
    assert "VerificationRecordService.transition" in workflow_source, (
        "the workflow bypasses the state machine"
    )
    assert "VerificationRecordService.apply_provider_result" in workflow_source, (
        "the workflow scores results itself instead of using the policy"
    )

    callers = sorted(
        path.relative_to(APP).as_posix()
        for path in APP.rglob("*.py")
        if "__pycache__" not in path.parts
        and "VerificationRecordService" in path.read_text(encoding="utf-8", errors="ignore")
    )
    assert callers == [
        "identity/services/verification_record_service.py",
        "identity/services/verification_workflow.py",
    ], f"the set of modules driving the verification state machine changed: {callers}"
