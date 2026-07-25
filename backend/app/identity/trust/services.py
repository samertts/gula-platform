from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC

from .models import (
    AAL1,
    AAL2,
    AAL3,
    FAL1,
    FAL2,
    FAL3,
    IAL1,
    IAL2,
    IAL3,
    IAL4,
    FederationTrust,
    IdentityAssuranceProfile,
    IdentityProofing,
    TrustAnchor,
    TrustEvaluation,
    TrustFramework,
)


class TrustFrameworkService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_framework(
        self,
        framework_id: str,
        name_en: str,
        name_ar: str,
        version: str,
        effective_date: datetime | None = None,
        supersedes_framework_id: str | None = None,
        authority_id: str | None = None,
        scope: dict | None = None,
        assurance_policies: dict | None = None,
    ) -> TrustFramework:
        entity = TrustFramework(
            uuid=str(uuid.uuid4()),
            framework_id=framework_id,
            name_en=name_en,
            name_ar=name_ar,
            version=version,
            status="draft",
            effective_date=effective_date,
            supersedes_framework_id=supersedes_framework_id,
            authority_id=authority_id,
            scope=scope,
            assurance_policies=assurance_policies,
            is_active=True,
        )
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get_framework(self, framework_id: str) -> TrustFramework | None:
        stmt = select(TrustFramework).where(
            TrustFramework.framework_id == framework_id,
            TrustFramework.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def activate_framework(self, framework_id: str) -> TrustFramework | None:
        entity = await self.get_framework(framework_id)
        if not entity:
            return None
        entity.status = "active"
        await self.session.flush()
        return entity

    async def supersede_framework(
        self,
        framework_id: str,
        superseded_by_id: str,
    ) -> TrustFramework | None:
        entity = await self.get_framework(framework_id)
        if not entity:
            return None
        entity.status = "superseded"
        entity.supersedes_framework_id = superseded_by_id
        await self.session.flush()
        return entity

    async def list_frameworks(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[TrustFramework]:
        stmt = (
            select(TrustFramework)
            .where(TrustFramework.is_active.is_(True))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_framework(
        self,
        framework_id: str,
        **kwargs: Any,
    ) -> TrustFramework | None:
        entity = await self.get_framework(framework_id)
        if not entity:
            return None
        for key, value in kwargs.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        await self.session.flush()
        return entity


class AssuranceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def assign_profile(
        self,
        person_id: str,
        identity_id: str,
        ial: str = IAL1,
        aal: str = AAL1,
        fal: str = FAL1,
        assessed_by: str | None = None,
        evidence: dict | None = None,
    ) -> IdentityAssuranceProfile:
        overall = self._calculate_overall(ial, aal, fal)
        entity = IdentityAssuranceProfile(
            uuid=str(uuid.uuid4()),
            person_id=person_id,
            identity_id=identity_id,
            ial=ial,
            aal=aal,
            fal=fal,
            overall_assurance=overall,
            profile_version="1.0",
            assessed_by=assessed_by,
            assessed_at=datetime.now(UTC),
            status="active",
            evidence=evidence,
            is_active=True,
        )
        self.session.add(entity)
        await self.session.flush()
        return entity

    def _calculate_overall(self, ial: str, aal: str, fal: str) -> str:
        levels = {IAL1: 1, IAL2: 2, IAL3: 3, IAL4: 4}
        aal_map = {AAL1: 1, AAL2: 2, AAL3: 3}
        fal_map = {FAL1: 1, FAL2: 2, FAL3: 3}
        scores = [
            levels.get(ial, 0),
            aal_map.get(aal, 0),
            fal_map.get(fal, 0),
        ]
        avg = sum(scores) / len(scores)
        if avg >= 4:
            return IAL4
        if avg >= 3:
            return IAL3
        if avg >= 2:
            return IAL2
        return IAL1

    async def get_profile(self, profile_id: str) -> IdentityAssuranceProfile | None:
        stmt = select(IdentityAssuranceProfile).where(
            IdentityAssuranceProfile.uuid == profile_id,
            IdentityAssuranceProfile.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_profiles_for_identity(
        self,
        identity_id: str,
    ) -> list[IdentityAssuranceProfile]:
        stmt = (
            select(IdentityAssuranceProfile)
            .where(
                IdentityAssuranceProfile.identity_id == identity_id,
                IdentityAssuranceProfile.is_active.is_(True),
            )
            .order_by(IdentityAssuranceProfile.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def revoke_profile(self, profile_id: str) -> IdentityAssuranceProfile | None:
        entity = await self.get_profile(profile_id)
        if not entity:
            return None
        entity.status = "revoked"
        await self.session.flush()
        return entity

    async def list_profiles(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[IdentityAssuranceProfile]:
        stmt = (
            select(IdentityAssuranceProfile)
            .where(IdentityAssuranceProfile.is_active.is_(True))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class TrustAnchorService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_anchor(
        self,
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
    ) -> TrustAnchor:
        entity = TrustAnchor(
            uuid=str(uuid.uuid4()),
            anchor_id=anchor_id,
            name=name,
            anchor_type=anchor_type,
            public_key_hash=public_key_hash,
            certificate_chain=certificate_chain,
            issuer=issuer,
            subject=subject,
            valid_from=valid_from,
            valid_to=valid_to,
            status="active",
            signed_by=signed_by,
            is_active=True,
        )
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get_anchor(self, anchor_id: str) -> TrustAnchor | None:
        stmt = select(TrustAnchor).where(
            TrustAnchor.anchor_id == anchor_id,
            TrustAnchor.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_anchor(
        self,
        anchor_id: str,
        reason: str,
    ) -> TrustAnchor | None:
        entity = await self.get_anchor(anchor_id)
        if not entity:
            return None
        entity.status = "revoked"
        entity.revoked_at = datetime.now(UTC)
        entity.revocation_reason = reason
        await self.session.flush()
        return entity

    async def list_anchors(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[TrustAnchor]:
        stmt = select(TrustAnchor).where(TrustAnchor.is_active.is_(True)).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def validate_chain(self, anchor_id: str) -> dict[str, Any]:
        entity = await self.get_anchor(anchor_id)
        if not entity:
            return {"valid": False, "reason": "anchor_not_found"}
        if entity.status == "revoked":
            return {"valid": False, "reason": "anchor_revoked"}
        if entity.status == "compromised":
            return {"valid": False, "reason": "anchor_compromised"}
        if entity.valid_to and entity.valid_to < datetime.now(UTC):
            return {"valid": False, "reason": "certificate_expired"}
        if entity.signed_by:
            parent = await self.get_anchor(entity.signed_by)
            if not parent or parent.status == "revoked":
                return {"valid": False, "reason": "signer_not_trusted"}
        return {"valid": True, "reason": None}


class FederationTrustService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_trust(
        self,
        trust_id: str,
        source_org_id: str,
        target_org_id: str,
        trust_type: str = "direct",
        trust_level: str = "limited",
        scope: dict | None = None,
        agreement_id: str | None = None,
        established_at: datetime | None = None,
        expires_at: datetime | None = None,
        terms: dict | None = None,
    ) -> FederationTrust:
        entity = FederationTrust(
            uuid=str(uuid.uuid4()),
            trust_id=trust_id,
            source_org_id=source_org_id,
            target_org_id=target_org_id,
            trust_type=trust_type,
            trust_level=trust_level,
            scope=scope,
            agreement_id=agreement_id,
            established_at=established_at or datetime.now(UTC),
            expires_at=expires_at,
            status="active",
            terms=terms,
            is_active=True,
        )
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get_trust(self, trust_id: str) -> FederationTrust | None:
        stmt = select(FederationTrust).where(
            FederationTrust.trust_id == trust_id,
            FederationTrust.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def suspend_trust(self, trust_id: str) -> FederationTrust | None:
        entity = await self.get_trust(trust_id)
        if not entity:
            return None
        entity.status = "suspended"
        await self.session.flush()
        return entity

    async def terminate_trust(self, trust_id: str) -> FederationTrust | None:
        entity = await self.get_trust(trust_id)
        if not entity:
            return None
        entity.status = "terminated"
        await self.session.flush()
        return entity

    async def list_for_org(self, org_id: str) -> list[FederationTrust]:
        stmt = (
            select(FederationTrust)
            .where(
                FederationTrust.is_active.is_(True),
                (FederationTrust.source_org_id == org_id)
                | (FederationTrust.target_org_id == org_id),
            )
            .order_by(FederationTrust.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[FederationTrust]:
        stmt = (
            select(FederationTrust)
            .where(FederationTrust.is_active.is_(True))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class IdentityProofingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_proofing(
        self,
        proofing_id: str,
        person_id: str,
        identity_id: str,
        proofing_level: str = IAL1,
        method: str = "remote",
        evidence_type: dict | None = None,
        evidence_documents: dict | None = None,
        authority_id: str | None = None,
    ) -> IdentityProofing:
        entity = IdentityProofing(
            uuid=str(uuid.uuid4()),
            proofing_id=proofing_id,
            person_id=person_id,
            identity_id=identity_id,
            proofing_level=proofing_level,
            method=method,
            evidence_type=evidence_type,
            evidence_documents=evidence_documents,
            authority_id=authority_id,
            status="pending",
            is_active=True,
        )
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def verify_proofing(
        self,
        proofing_id: str,
        verified_by: str,
    ) -> IdentityProofing | None:
        entity = await self.get_proofing(proofing_id)
        if not entity:
            return None
        entity.status = "verified"
        entity.verified_by = verified_by
        entity.verified_at = datetime.now(UTC)
        entity.valid_from = datetime.now(UTC)
        await self.session.flush()
        return entity

    async def reject_proofing(
        self,
        proofing_id: str,
        reason: str,
    ) -> IdentityProofing | None:
        entity = await self.get_proofing(proofing_id)
        if not entity:
            return None
        entity.status = "rejected"
        entity.rejection_reason = reason
        await self.session.flush()
        return entity

    async def get_proofing(self, proofing_id: str) -> IdentityProofing | None:
        stmt = select(IdentityProofing).where(
            IdentityProofing.proofing_id == proofing_id,
            IdentityProofing.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_person(
        self,
        person_id: str,
    ) -> list[IdentityProofing]:
        stmt = (
            select(IdentityProofing)
            .where(
                IdentityProofing.person_id == person_id,
                IdentityProofing.is_active.is_(True),
            )
            .order_by(IdentityProofing.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[IdentityProofing]:
        stmt = (
            select(IdentityProofing)
            .where(IdentityProofing.is_active.is_(True))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class TrustEvaluationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_evaluation(
        self,
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
    ) -> TrustEvaluation:
        entity = TrustEvaluation(
            uuid=str(uuid.uuid4()),
            evaluation_id=evaluation_id,
            target_type=target_type,
            target_id=target_id,
            evaluated_by=evaluated_by,
            evaluated_at=datetime.now(UTC),
            assurance_score=assurance_score,
            confidence_score=confidence_score,
            risk_score=risk_score,
            evaluation_method=evaluation_method,
            findings=findings,
            recommendations=recommendations,
            status="completed",
            is_active=True,
        )
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get_evaluation(self, evaluation_id: str) -> TrustEvaluation | None:
        stmt = select(TrustEvaluation).where(
            TrustEvaluation.evaluation_id == evaluation_id,
            TrustEvaluation.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_target(
        self,
        target_type: str,
        target_id: str,
    ) -> list[TrustEvaluation]:
        stmt = (
            select(TrustEvaluation)
            .where(
                TrustEvaluation.target_type == target_type,
                TrustEvaluation.target_id == target_id,
                TrustEvaluation.is_active.is_(True),
            )
            .order_by(TrustEvaluation.evaluated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[TrustEvaluation]:
        stmt = (
            select(TrustEvaluation)
            .where(TrustEvaluation.is_active.is_(True))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
