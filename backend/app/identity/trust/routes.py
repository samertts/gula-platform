from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

from .services import (
    AssuranceService,
    FederationTrustService,
    IdentityProofingService,
    TrustAnchorService,
    TrustEvaluationService,
    TrustFrameworkService,
)


def _reject_unscoped_trust_workflow() -> None:
    """Trust/proofing APIs stay unavailable until server-side scope is wired."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Identity trust workflow is unavailable until governed authorization is enabled.",
    )


router = APIRouter(
    prefix="/niam/trust",
    tags=["NIAM Trust"],
    dependencies=[Depends(_reject_unscoped_trust_workflow)],
)


# ── Trust Frameworks ──────────────────────────────────────────────────────────


@router.post("/frameworks")
async def create_framework(
    framework_id: str,
    name_en: str,
    name_ar: str,
    version: str,
    effective_date: datetime | None = None,
    supersedes_framework_id: str | None = None,
    authority_id: str | None = None,
    scope: dict | None = None,
    assurance_policies: dict | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = TrustFrameworkService(db)
    entity = await service.create_framework(
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
async def list_frameworks(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    service = TrustFrameworkService(db)
    frameworks = await service.list_frameworks(skip=skip, limit=limit)
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
async def get_framework(
    framework_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = TrustFrameworkService(db)
    entity = await service.get_framework(framework_id)
    if not entity:
        return {"error": "not_found"}
    return entity.to_dict()


@router.put("/frameworks/{framework_id}")
async def update_framework(
    framework_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    service = TrustFrameworkService(db)
    entity = await service.update_framework(framework_id, **body)
    if not entity:
        return {"error": "not_found"}
    return entity.to_dict()


@router.post("/frameworks/{framework_id}/activate")
async def activate_framework(
    framework_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = TrustFrameworkService(db)
    entity = await service.activate_framework(framework_id)
    if not entity:
        return {"error": "not_found"}
    return {"uuid": entity.uuid, "status": entity.status}


# ── Assurance Profiles ────────────────────────────────────────────────────────


@router.post("/assurance-profiles")
async def create_assurance_profile(
    person_id: str,
    identity_id: str,
    ial: str = "IAL1",
    aal: str = "AAL1",
    fal: str = "FAL1",
    assessed_by: str | None = None,
    evidence: dict | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = AssuranceService(db)
    entity = await service.assign_profile(
        person_id=person_id,
        identity_id=identity_id,
        ial=ial,
        aal=aal,
        fal=fal,
        assessed_by=assessed_by,
        evidence=evidence,
    )
    return {
        "uuid": entity.uuid,
        "id": entity.id,
        "overall_assurance": entity.overall_assurance,
        "status": entity.status,
    }


@router.get("/assurance-profiles")
async def list_assurance_profiles(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    service = AssuranceService(db)
    profiles = await service.list_profiles(skip=skip, limit=limit)
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
async def get_assurance_profile(
    profile_uuid: str,
    db: AsyncSession = Depends(get_db),
):
    service = AssuranceService(db)
    entity = await service.get_profile(profile_uuid)
    if not entity:
        return {"error": "not_found"}
    return entity.to_dict()


@router.get("/assurance-profiles/identity/{identity_id}")
async def get_profiles_for_identity(
    identity_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = AssuranceService(db)
    profiles = await service.get_profiles_for_identity(identity_id)
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
async def revoke_assurance_profile(
    profile_uuid: str,
    db: AsyncSession = Depends(get_db),
):
    service = AssuranceService(db)
    entity = await service.revoke_profile(profile_uuid)
    if not entity:
        return {"error": "not_found"}
    return {"uuid": entity.uuid, "status": entity.status}


# ── Trust Anchors ─────────────────────────────────────────────────────────────


@router.post("/anchors")
async def create_anchor(
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
    db: AsyncSession = Depends(get_db),
):
    service = TrustAnchorService(db)
    entity = await service.create_anchor(
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
async def list_anchors(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    service = TrustAnchorService(db)
    anchors = await service.list_anchors(skip=skip, limit=limit)
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
async def get_anchor(
    anchor_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = TrustAnchorService(db)
    entity = await service.get_anchor(anchor_id)
    if not entity:
        return {"error": "not_found"}
    return entity.to_dict()


@router.get("/anchors/{anchor_id}/validate")
async def validate_anchor_chain(
    anchor_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = TrustAnchorService(db)
    return await service.validate_chain(anchor_id)


@router.post("/anchors/{anchor_id}/revoke")
async def revoke_anchor(
    anchor_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db),
):
    service = TrustAnchorService(db)
    entity = await service.revoke_anchor(anchor_id, reason)
    if not entity:
        return {"error": "not_found"}
    return {"uuid": entity.uuid, "status": entity.status}


# ── Federation Trust ──────────────────────────────────────────────────────────


@router.post("/federation")
async def create_federation_trust(
    trust_id: str,
    source_org_id: str,
    target_org_id: str,
    trust_type: str = "direct",
    trust_level: str = "limited",
    scope: dict | None = None,
    agreement_id: str | None = None,
    expires_at: datetime | None = None,
    terms: dict | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = FederationTrustService(db)
    entity = await service.create_trust(
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
async def list_federation_trusts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    service = FederationTrustService(db)
    trusts = await service.list_all(skip=skip, limit=limit)
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
async def get_federation_trust(
    trust_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = FederationTrustService(db)
    entity = await service.get_trust(trust_id)
    if not entity:
        return {"error": "not_found"}
    return entity.to_dict()


@router.get("/federation/org/{org_id}")
async def list_federation_for_org(
    org_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = FederationTrustService(db)
    trusts = await service.list_for_org(org_id)
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
async def suspend_federation_trust(
    trust_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = FederationTrustService(db)
    entity = await service.suspend_trust(trust_id)
    if not entity:
        return {"error": "not_found"}
    return {"uuid": entity.uuid, "status": entity.status}


@router.post("/federation/{trust_id}/terminate")
async def terminate_federation_trust(
    trust_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = FederationTrustService(db)
    entity = await service.terminate_trust(trust_id)
    if not entity:
        return {"error": "not_found"}
    return {"uuid": entity.uuid, "status": entity.status}


# ── Identity Proofing ─────────────────────────────────────────────────────────


@router.post("/proofing")
async def create_proofing(
    proofing_id: str,
    person_id: str,
    identity_id: str,
    proofing_level: str = "IAL1",
    method: str = "remote",
    evidence_type: dict | None = None,
    evidence_documents: dict | None = None,
    authority_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = IdentityProofingService(db)
    entity = await service.create_proofing(
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
async def list_proofing(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    service = IdentityProofingService(db)
    records = await service.list_all(skip=skip, limit=limit)
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
async def get_proofing(
    proofing_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = IdentityProofingService(db)
    entity = await service.get_proofing(proofing_id)
    if not entity:
        return {"error": "not_found"}
    return entity.to_dict()


@router.get("/proofing/person/{person_id}")
async def list_proofing_for_person(
    person_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = IdentityProofingService(db)
    records = await service.list_for_person(person_id)
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
async def verify_proofing(
    proofing_id: str,
    verified_by: str,
    db: AsyncSession = Depends(get_db),
):
    service = IdentityProofingService(db)
    entity = await service.verify_proofing(proofing_id, verified_by)
    if not entity:
        return {"error": "not_found"}
    return {"uuid": entity.uuid, "status": entity.status}


@router.post("/proofing/{proofing_id}/reject")
async def reject_proofing(
    proofing_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db),
):
    service = IdentityProofingService(db)
    entity = await service.reject_proofing(proofing_id, reason)
    if not entity:
        return {"error": "not_found"}
    return {"uuid": entity.uuid, "status": entity.status}


# ── Trust Evaluations ─────────────────────────────────────────────────────────


@router.post("/evaluations")
async def create_evaluation(
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
    db: AsyncSession = Depends(get_db),
):
    service = TrustEvaluationService(db)
    entity = await service.create_evaluation(
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
async def list_evaluations(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    service = TrustEvaluationService(db)
    evaluations = await service.list_all(skip=skip, limit=limit)
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
async def get_evaluation(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = TrustEvaluationService(db)
    entity = await service.get_evaluation(evaluation_id)
    if not entity:
        return {"error": "not_found"}
    return entity.to_dict()


@router.get("/evaluations/target/{target_type}/{target_id}")
async def get_evaluations_for_target(
    target_type: str,
    target_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = TrustEvaluationService(db)
    evaluations = await service.list_for_target(target_type, target_id)
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
