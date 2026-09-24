from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.models.audit import AuditAction
from app.identity.services.audit_service import AuditService

from .services import (
    AssuranceService,
    FederationTrustService,
    IdentityProofingService,
    TrustAnchorService,
    TrustEvaluationService,
    TrustFrameworkService,
)

# This router is mounted under app/identity/api/router.py, which already
# carries prefix="/niam". Declaring "/niam" here as well served every one of
# these routes at /niam/niam/..., which no client calls: frontend-v3 asks for
# the single-prefix path and got 404. 60 served paths were doubled this way.
router = APIRouter(prefix="/trust", tags=["NIAM Trust"])


def _require_assurance_administrator(db: Session, actor: NiamActor) -> None:
    """Only an active administrative assignment may act for another account.

    Fail-closed: no assignment, an inactive one, or one in another organization
    is a refusal. This guards *who may ask*; the answer itself is derived from
    evidence either way, so a forged request cannot raise an assurance level.
    """
    from sqlalchemy import select as _select

    from app.identity.models.assignment import Assignment, AssignmentStatus
    from app.identity.models.identity import IdentityRecord

    # NR-052. This filtered on `Assignment.account_id`, which is not a column:
    # an assignment belongs to a *person*, and an account reaches one through
    # `Account.identity_id -> IdentityRecord.person_id`. So the gate raised
    # AttributeError instead of deciding anything — invisibly, because NR-044
    # meant this route could not execute at all. It failed closed, as a 500, so
    # nothing was ever wrongly allowed; but the check had never once been
    # evaluated, and "fails closed by crashing" is not a control.
    #
    # This walks the same account -> identity -> person chain that
    # ClinicalAuthorizationContextService uses, and keeps the identity's own
    # standing in the conjunction rather than trusting the account alone. The
    # predicate is therefore at least as strict as the one that was intended.
    result = db.execute(
        _select(Assignment.id)
        .join(IdentityRecord, IdentityRecord.person_id == Assignment.person_id)
        .where(
            IdentityRecord.id == actor.account.identity_id,
            IdentityRecord.status == "active",
            IdentityRecord.is_active.is_(True),
            Assignment.status == AssignmentStatus.active.value,
            Assignment.is_active.is_(True),
        )
        .limit(1),
    )
    if result.scalars().first() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Asserting an assurance profile for another account requires an active administrative assignment",
        )


# ── Trust Frameworks ──────────────────────────────────────────────────────────


@router.post("/frameworks")
def create_framework(
    framework_id: str,
    name_en: str,
    name_ar: str,
    version: str,
    effective_date: datetime | None = None,
    supersedes_framework_id: str | None = None,
    authority_id: str | None = None,
    scope: dict | None = None,
    assurance_policies: dict | None = None,
    db: Session = Depends(get_db),
):
    service = TrustFrameworkService(db)
    entity = service.create_framework(
        framework_id=framework_id,
        name_en=name_en,
        name_ar=name_ar,
        version=version,
        effective_date=effective_date,
        supersedes_framework_id=supersedes_framework_id,
        authority_id=authority_id,
        scope=scope,
        assurance_policies=assurance_policies,
    )
    return {"uuid": entity.uuid, "id": entity.id, "framework_id": entity.framework_id}


@router.get("/frameworks")
def list_frameworks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    service = TrustFrameworkService(db)
    frameworks = service.list_frameworks(skip=skip, limit=limit)
    return [
        {
            "uuid": f.uuid,
            "framework_id": f.framework_id,
            "name_en": f.name_en,
            "name_ar": f.name_ar,
            "version": f.version,
            "status": f.status,
        }
        for f in frameworks
    ]


@router.get("/frameworks/{framework_id}")
def get_framework(
    framework_id: str,
    db: Session = Depends(get_db),
):
    service = TrustFrameworkService(db)
    entity = service.get_framework(framework_id)
    if not entity:
        return {"error": "not_found"}
    return entity.to_dict()


@router.put("/frameworks/{framework_id}")
def update_framework(
    framework_id: str,
    body: dict[str, Any],
    db: Session = Depends(get_db),
):
    service = TrustFrameworkService(db)
    entity = service.update_framework(framework_id, **body)
    if not entity:
        return {"error": "not_found"}
    return entity.to_dict()


@router.post("/frameworks/{framework_id}/activate")
def activate_framework(
    framework_id: str,
    db: Session = Depends(get_db),
):
    service = TrustFrameworkService(db)
    entity = service.activate_framework(framework_id)
    if not entity:
        return {"error": "not_found"}
    return {"uuid": entity.uuid, "status": entity.status}


# ── Assurance Profiles ────────────────────────────────────────────────────────


@router.post("/assurance-profiles")
def create_assurance_profile(
    account_id: str,
    person_id: str,
    identity_id: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    """Recompute an account's assurance profile from its verification evidence.

    NR-038. This route used to accept `ial`, `aal`, `fal`, `assessed_by` and
    `evidence` from the caller and write them through with `status="active"`, so
    a client named its own assurance level, its own assessor and its own
    evidence, with no verification record consulted.

    Nothing a caller sends can raise a level now: the profile is derived from
    `niam_verification_records`, which only a trusted server-side verifier can
    write, and the assessor is the authenticated actor. The request names a
    subject; it does not supply an answer.

    An account may recompute its own profile. Asserting for a different account
    additionally requires an active administrative assignment — and even then it
    asserts nothing, because the inputs are evidence rather than claims.
    """
    if account_id != actor.account.id:
        _require_assurance_administrator(db, actor)

    service = AssuranceService(db)
    entity = service.derive_profile(
        account_id=account_id,
        person_id=person_id,
        identity_id=identity_id,
        assessed_by=f"account:{actor.account.id}",
    )
    AuditService(db).record(
        AuditAction.assurance_profile_assigned,
        actor_id=actor.account.id,
        actor_type="account",
        target_type="assurance_profile",
        target_id=entity.id,
        metadata={
            "subject_account_id": account_id,
            "derived": True,
            "ial": entity.ial,
            "overall_assurance": entity.overall_assurance,
        },
    )
    return {
        "uuid": entity.uuid,
        "id": entity.id,
        "ial": entity.ial,
        "overall_assurance": entity.overall_assurance,
        "status": entity.status,
    }


@router.get("/assurance-profiles")
def list_assurance_profiles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    service = AssuranceService(db)
    profiles = service.list_profiles(skip=skip, limit=limit)
    return [
        {
            "uuid": p.uuid,
            "person_id": p.person_id,
            "identity_id": p.identity_id,
            "ial": p.ial,
            "aal": p.aal,
            "fal": p.fal,
            "overall_assurance": p.overall_assurance,
            "status": p.status,
        }
        for p in profiles
    ]


@router.get("/assurance-profiles/{profile_uuid}")
def get_assurance_profile(
    profile_uuid: str,
    db: Session = Depends(get_db),
):
    service = AssuranceService(db)
    entity = service.get_profile(profile_uuid)
    if not entity:
        return {"error": "not_found"}
    return entity.to_dict()


@router.get("/assurance-profiles/identity/{identity_id}")
def get_profiles_for_identity(
    identity_id: str,
    db: Session = Depends(get_db),
):
    service = AssuranceService(db)
    profiles = service.get_profiles_for_identity(identity_id)
    return [
        {
            "uuid": p.uuid,
            "ial": p.ial,
            "aal": p.aal,
            "fal": p.fal,
            "overall_assurance": p.overall_assurance,
            "status": p.status,
        }
        for p in profiles
    ]


@router.post("/assurance-profiles/{profile_uuid}/revoke")
def revoke_assurance_profile(
    profile_uuid: str,
    db: Session = Depends(get_db),
):
    service = AssuranceService(db)
    entity = service.revoke_profile(profile_uuid)
    if not entity:
        return {"error": "not_found"}
    return {"uuid": entity.uuid, "status": entity.status}


# ── Trust Anchors ─────────────────────────────────────────────────────────────


@router.post("/anchors")
def create_anchor(
    anchor_id: str,
    name: str,
    anchor_type: str,
    public_key_hash: str | None = None,
    certificate_chain: str | None = None,
    issuer: str | None = None,
    subject: str | None = None,
    valid_from: datetime | None = None,
    valid_to: datetime | None = None,
    signed_by: str | None = None,
    db: Session = Depends(get_db),
):
    service = TrustAnchorService(db)
    entity = service.create_anchor(
        anchor_id=anchor_id,
        name=name,
        anchor_type=anchor_type,
        public_key_hash=public_key_hash,
        certificate_chain=certificate_chain,
        issuer=issuer,
        subject=subject,
        valid_from=valid_from,
        valid_to=valid_to,
        signed_by=signed_by,
    )
    return {"uuid": entity.uuid, "id": entity.id, "anchor_id": entity.anchor_id}


@router.get("/anchors")
def list_anchors(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    service = TrustAnchorService(db)
    anchors = service.list_anchors(skip=skip, limit=limit)
    return [
        {
            "uuid": a.uuid,
            "anchor_id": a.anchor_id,
            "name": a.name,
            "anchor_type": a.anchor_type,
            "status": a.status,
        }
        for a in anchors
    ]


@router.get("/anchors/{anchor_id}")
def get_anchor(
    anchor_id: str,
    db: Session = Depends(get_db),
):
    service = TrustAnchorService(db)
    entity = service.get_anchor(anchor_id)
    if not entity:
        return {"error": "not_found"}
    return entity.to_dict()


@router.get("/anchors/{anchor_id}/validate")
def validate_anchor_chain(
    anchor_id: str,
    db: Session = Depends(get_db),
):
    service = TrustAnchorService(db)
    return service.validate_chain(anchor_id)


@router.post("/anchors/{anchor_id}/revoke")
def revoke_anchor(
    anchor_id: str,
    reason: str,
    db: Session = Depends(get_db),
):
    service = TrustAnchorService(db)
    entity = service.revoke_anchor(anchor_id, reason)
    if not entity:
        return {"error": "not_found"}
    return {"uuid": entity.uuid, "status": entity.status}


# ── Federation Trust ──────────────────────────────────────────────────────────


@router.post("/federation")
def create_federation_trust(
    trust_id: str,
    source_org_id: str,
    target_org_id: str,
    trust_type: str = "direct",
    trust_level: str = "limited",
    scope: dict | None = None,
    agreement_id: str | None = None,
    expires_at: datetime | None = None,
    terms: dict | None = None,
    db: Session = Depends(get_db),
):
    service = FederationTrustService(db)
    entity = service.create_trust(
        trust_id=trust_id,
        source_org_id=source_org_id,
        target_org_id=target_org_id,
        trust_type=trust_type,
        trust_level=trust_level,
        scope=scope,
        agreement_id=agreement_id,
        expires_at=expires_at,
        terms=terms,
    )
    return {"uuid": entity.uuid, "id": entity.id, "trust_id": entity.trust_id}


@router.get("/federation")
def list_federation_trusts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    service = FederationTrustService(db)
    trusts = service.list_all(skip=skip, limit=limit)
    return [
        {
            "uuid": t.uuid,
            "trust_id": t.trust_id,
            "source_org_id": t.source_org_id,
            "target_org_id": t.target_org_id,
            "trust_type": t.trust_type,
            "trust_level": t.trust_level,
            "status": t.status,
        }
        for t in trusts
    ]


@router.get("/federation/{trust_id}")
def get_federation_trust(
    trust_id: str,
    db: Session = Depends(get_db),
):
    service = FederationTrustService(db)
    entity = service.get_trust(trust_id)
    if not entity:
        return {"error": "not_found"}
    return entity.to_dict()


@router.get("/federation/org/{org_id}")
def list_federation_for_org(
    org_id: str,
    db: Session = Depends(get_db),
):
    service = FederationTrustService(db)
    trusts = service.list_for_org(org_id)
    return [
        {
            "uuid": t.uuid,
            "trust_id": t.trust_id,
            "source_org_id": t.source_org_id,
            "target_org_id": t.target_org_id,
            "trust_type": t.trust_type,
            "status": t.status,
        }
        for t in trusts
    ]


@router.post("/federation/{trust_id}/suspend")
def suspend_federation_trust(
    trust_id: str,
    db: Session = Depends(get_db),
):
    service = FederationTrustService(db)
    entity = service.suspend_trust(trust_id)
    if not entity:
        return {"error": "not_found"}
    return {"uuid": entity.uuid, "status": entity.status}


@router.post("/federation/{trust_id}/terminate")
def terminate_federation_trust(
    trust_id: str,
    db: Session = Depends(get_db),
):
    service = FederationTrustService(db)
    entity = service.terminate_trust(trust_id)
    if not entity:
        return {"error": "not_found"}
    return {"uuid": entity.uuid, "status": entity.status}


# ── Identity Proofing ─────────────────────────────────────────────────────────


@router.post("/proofing")
def create_proofing(
    proofing_id: str,
    person_id: str,
    identity_id: str,
    proofing_level: str = "IAL1",
    method: str = "remote",
    evidence_type: dict | None = None,
    evidence_documents: dict | None = None,
    authority_id: str | None = None,
    db: Session = Depends(get_db),
):
    service = IdentityProofingService(db)
    entity = service.create_proofing(
        proofing_id=proofing_id,
        person_id=person_id,
        identity_id=identity_id,
        proofing_level=proofing_level,
        method=method,
        evidence_type=evidence_type,
        evidence_documents=evidence_documents,
        authority_id=authority_id,
    )
    return {"uuid": entity.uuid, "id": entity.id, "proofing_id": entity.proofing_id, "status": entity.status}


@router.get("/proofing")
def list_proofing(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    service = IdentityProofingService(db)
    records = service.list_all(skip=skip, limit=limit)
    return [
        {
            "uuid": r.uuid,
            "proofing_id": r.proofing_id,
            "person_id": r.person_id,
            "proofing_level": r.proofing_level,
            "method": r.method,
            "status": r.status,
        }
        for r in records
    ]


@router.get("/proofing/{proofing_id}")
def get_proofing(
    proofing_id: str,
    db: Session = Depends(get_db),
):
    service = IdentityProofingService(db)
    entity = service.get_proofing(proofing_id)
    if not entity:
        return {"error": "not_found"}
    return entity.to_dict()


@router.get("/proofing/person/{person_id}")
def list_proofing_for_person(
    person_id: str,
    db: Session = Depends(get_db),
):
    service = IdentityProofingService(db)
    records = service.list_for_person(person_id)
    return [
        {
            "uuid": r.uuid,
            "proofing_id": r.proofing_id,
            "proofing_level": r.proofing_level,
            "method": r.method,
            "status": r.status,
        }
        for r in records
    ]


@router.post("/proofing/{proofing_id}/verify")
def verify_proofing(
    proofing_id: str,
    verified_by: str,
    db: Session = Depends(get_db),
):
    service = IdentityProofingService(db)
    entity = service.verify_proofing(proofing_id, verified_by)
    if not entity:
        return {"error": "not_found"}
    return {"uuid": entity.uuid, "status": entity.status}


@router.post("/proofing/{proofing_id}/reject")
def reject_proofing(
    proofing_id: str,
    reason: str,
    db: Session = Depends(get_db),
):
    service = IdentityProofingService(db)
    entity = service.reject_proofing(proofing_id, reason)
    if not entity:
        return {"error": "not_found"}
    return {"uuid": entity.uuid, "status": entity.status}


# ── Trust Evaluations ─────────────────────────────────────────────────────────


@router.post("/evaluations")
def create_evaluation(
    evaluation_id: str,
    target_type: str,
    target_id: str,
    evaluated_by: str | None = None,
    assurance_score: int | None = None,
    confidence_score: int | None = None,
    risk_score: int | None = None,
    evaluation_method: str | None = None,
    findings: dict | None = None,
    recommendations: dict | None = None,
    db: Session = Depends(get_db),
):
    service = TrustEvaluationService(db)
    entity = service.create_evaluation(
        evaluation_id=evaluation_id,
        target_type=target_type,
        target_id=target_id,
        evaluated_by=evaluated_by,
        assurance_score=assurance_score,
        confidence_score=confidence_score,
        risk_score=risk_score,
        evaluation_method=evaluation_method,
        findings=findings,
        recommendations=recommendations,
    )
    return {"uuid": entity.uuid, "id": entity.id, "evaluation_id": entity.evaluation_id}


@router.get("/evaluations")
def list_evaluations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    service = TrustEvaluationService(db)
    evaluations = service.list_all(skip=skip, limit=limit)
    return [
        {
            "uuid": e.uuid,
            "evaluation_id": e.evaluation_id,
            "target_type": e.target_type,
            "target_id": e.target_id,
            "assurance_score": e.assurance_score,
            "confidence_score": e.confidence_score,
            "risk_score": e.risk_score,
            "status": e.status,
        }
        for e in evaluations
    ]


@router.get("/evaluations/{evaluation_id}")
def get_evaluation(
    evaluation_id: str,
    db: Session = Depends(get_db),
):
    service = TrustEvaluationService(db)
    entity = service.get_evaluation(evaluation_id)
    if not entity:
        return {"error": "not_found"}
    return entity.to_dict()


@router.get("/evaluations/target/{target_type}/{target_id}")
def get_evaluations_for_target(
    target_type: str,
    target_id: str,
    db: Session = Depends(get_db),
):
    service = TrustEvaluationService(db)
    evaluations = service.list_for_target(target_type, target_id)
    return [
        {
            "uuid": e.uuid,
            "evaluation_id": e.evaluation_id,
            "assurance_score": e.assurance_score,
            "confidence_score": e.confidence_score,
            "risk_score": e.risk_score,
            "status": e.status,
        }
        for e in evaluations
    ]
