from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.federation.models import (
    CrossOrganizationTrust,
    FederatedIdentity,
    FederatedProvider,
    FederatedSession,
    FederationAgreement,
)


class FederationService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register_provider(
        self,
        provider_id: str,
        name_en: str,
        name_ar: Optional[str],
        provider_type: str,
        issuer_url: str,
        authorization_endpoint: Optional[str] = None,
        token_endpoint: Optional[str] = None,
        jwks_uri: Optional[str] = None,
        userinfo_endpoint: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret_encrypted: Optional[str] = None,
        scopes: Optional[list[str]] = None,
        redirect_uris: Optional[list[str]] = None,
        certificate: Optional[str] = None,
        signature_algorithm: Optional[str] = None,
        trust_anchor_id: Optional[str] = None,
        metadata_url: Optional[str] = None,
    ) -> FederatedProvider:
        provider = FederatedProvider(
            uuid=str(uuid.uuid4()),
            provider_id=provider_id,
            name_en=name_en,
            name_ar=name_ar,
            provider_type=provider_type,
            issuer_url=issuer_url,
            authorization_endpoint=authorization_endpoint,
            token_endpoint=token_endpoint,
            jwks_uri=jwks_uri,
            userinfo_endpoint=userinfo_endpoint,
            client_id=client_id,
            client_secret_encrypted=client_secret_encrypted,
            scopes=scopes,
            redirect_uris=redirect_uris,
            certificate=certificate,
            signature_algorithm=signature_algorithm,
            trust_anchor_id=trust_anchor_id,
            metadata_url=metadata_url,
            status="active",
            is_active=True,
        )
        self.session.add(provider)
        await self.session.flush()
        return provider

    async def get_provider(self, provider_id: str) -> Optional[FederatedProvider]:
        stmt = select(FederatedProvider).where(
            FederatedProvider.provider_id == provider_id,
            FederatedProvider.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_provider(
        self,
        provider_id: str,
        **kwargs: Any,
    ) -> Optional[FederatedProvider]:
        provider = await self.get_provider(provider_id)
        if not provider:
            return None
        for key, value in kwargs.items():
            if hasattr(provider, key) and value is not None:
                setattr(provider, key, value)
        await self.session.flush()
        return provider

    async def list_providers(
        self,
        status: Optional[str] = None,
    ) -> list[FederatedProvider]:
        stmt = select(FederatedProvider).where(FederatedProvider.is_active.is_(True))
        if status:
            stmt = stmt.where(FederatedProvider.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def link_identity(
        self,
        person_id: str,
        provider_id: str,
        external_subject_id: str,
        external_attributes: Optional[dict[str, Any]] = None,
        identity_id: Optional[str] = None,
    ) -> FederatedIdentity:
        existing = await self.find_by_external_id(provider_id, external_subject_id)
        if existing:
            existing.status = "active"
            existing.unlinked_at = None
            existing.unlink_reason = None
            existing.is_active = True
            await self.session.flush()
            return existing

        fed_id_val = f"fed_{uuid.uuid4().hex[:12]}"
        identity = FederatedIdentity(
            uuid=str(uuid.uuid4()),
            fed_id=fed_id_val,
            person_id=person_id,
            identity_id=identity_id,
            provider_id=provider_id,
            external_subject_id=external_subject_id,
            external_attributes=external_attributes,
            linked_at=datetime.now(UTC),
            status="active",
            is_active=True,
        )
        self.session.add(identity)
        await self.session.flush()
        return identity

    async def unlink_identity(self, fed_id: str, reason: str) -> Optional[FederatedIdentity]:
        stmt = select(FederatedIdentity).where(
            FederatedIdentity.fed_id == fed_id,
            FederatedIdentity.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        identity = result.scalar_one_or_none()
        if not identity:
            return None
        identity.status = "unlinked"
        identity.unlinked_at = datetime.now(UTC)
        identity.unlink_reason = reason
        identity.is_active = False
        await self.session.flush()
        return identity

    async def find_by_external_id(
        self,
        provider_id: str,
        external_subject_id: str,
    ) -> Optional[FederatedIdentity]:
        stmt = select(FederatedIdentity).where(
            FederatedIdentity.provider_id == provider_id,
            FederatedIdentity.external_subject_id == external_subject_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_identities_for_person(self, person_id: str) -> list[FederatedIdentity]:
        stmt = select(FederatedIdentity).where(
            FederatedIdentity.person_id == person_id,
            FederatedIdentity.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_session(
        self,
        account_id: str,
        provider_id: str,
        fed_identity_id: str,
        tokens: dict[str, Any],
        attributes: Optional[dict[str, Any]] = None,
    ) -> FederatedSession:
        session_id_val = f"fed_sess_{uuid.uuid4().hex[:16]}"
        fed_session = FederatedSession(
            uuid=str(uuid.uuid4()),
            session_id=session_id_val,
            account_id=account_id,
            provider_id=provider_id,
            fed_identity_id=fed_identity_id,
            id_token=tokens.get("id_token"),
            access_token_hash=tokens.get("access_token_hash"),
            refresh_token_hash=tokens.get("refresh_token_hash"),
            token_type=tokens.get("token_type", "bearer"),
            scope=tokens.get("scope"),
            session_attributes=attributes,
            started_at=datetime.now(UTC),
            expires_at=tokens.get("expires_at"),
            is_active=True,
        )
        self.session.add(fed_session)
        await self.session.flush()
        return fed_session

    async def terminate_session(self, session_id: str) -> Optional[FederatedSession]:
        stmt = select(FederatedSession).where(
            FederatedSession.session_id == session_id,
            FederatedSession.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        fed_session = result.scalar_one_or_none()
        if not fed_session:
            return None
        fed_session.terminated_at = datetime.now(UTC)
        fed_session.is_active = False
        await self.session.flush()
        return fed_session


class CrossOrgTrustService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def establish_trust(
        self,
        source_org_id: str,
        target_org_id: str,
        trust_level: str,
        agreement: Optional[dict[str, Any]] = None,
        trust_type: str = "bilateral",
        established_by: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> CrossOrganizationTrust:
        trust = CrossOrganizationTrust(
            uuid=str(uuid.uuid4()),
            trust_id=f"trust_{uuid.uuid4().hex[:12]}",
            source_org_id=source_org_id,
            target_org_id=target_org_id,
            trust_type=trust_type,
            trust_level=trust_level,
            attribute_sharing_agreement=agreement,
            established_at=datetime.now(UTC),
            established_by=established_by,
            expires_at=expires_at,
            status="active",
            is_active=True,
        )
        self.session.add(trust)
        await self.session.flush()
        return trust

    async def get_trust_relationships(self, org_id: str) -> list[CrossOrganizationTrust]:
        stmt = select(CrossOrganizationTrust).where(
            CrossOrganizationTrust.is_active.is_(True),
            (
                (CrossOrganizationTrust.source_org_id == org_id)
                | (CrossOrganizationTrust.target_org_id == org_id)
            ),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def suspend_trust(self, trust_id: str) -> Optional[CrossOrganizationTrust]:
        stmt = select(CrossOrganizationTrust).where(
            CrossOrganizationTrust.trust_id == trust_id,
            CrossOrganizationTrust.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        trust = result.scalar_one_or_none()
        if not trust:
            return None
        trust.status = "suspended"
        await self.session.flush()
        return trust

    async def terminate_trust(self, trust_id: str) -> Optional[CrossOrganizationTrust]:
        stmt = select(CrossOrganizationTrust).where(
            CrossOrganizationTrust.trust_id == trust_id,
            CrossOrganizationTrust.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        trust = result.scalar_one_or_none()
        if not trust:
            return None
        trust.status = "terminated"
        trust.is_active = False
        await self.session.flush()
        return trust


class FederationAgreementService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_agreement(
        self,
        name: str,
        parties: list[str],
        agreement_type: str,
        scope: Optional[dict[str, Any]] = None,
        terms: Optional[dict[str, Any]] = None,
        security_requirements: Optional[dict[str, Any]] = None,
        effective_date: Optional[datetime] = None,
        expiry_date: Optional[datetime] = None,
        governing_law: Optional[str] = None,
    ) -> FederationAgreement:
        agreement = FederationAgreement(
            uuid=str(uuid.uuid4()),
            agreement_id=f"agr_{uuid.uuid4().hex[:12]}",
            name=name,
            parties=parties,
            agreement_type=agreement_type,
            scope=scope,
            terms=terms,
            security_requirements=security_requirements,
            effective_date=effective_date,
            expiry_date=expiry_date,
            status="draft",
            governing_law=governing_law,
            is_active=True,
        )
        self.session.add(agreement)
        await self.session.flush()
        return agreement

    async def sign_agreement(
        self,
        agreement_id: str,
        signed_by: list[dict[str, Any]],
    ) -> Optional[FederationAgreement]:
        stmt = select(FederationAgreement).where(
            FederationAgreement.agreement_id == agreement_id,
        )
        result = await self.session.execute(stmt)
        agreement = result.scalar_one_or_none()
        if not agreement:
            return None
        agreement.signed_by = signed_by
        agreement.signed_at = datetime.now(UTC)
        if agreement.status == "draft":
            agreement.status = "active"
        await self.session.flush()
        return agreement

    async def get_active_agreements(self, org_id: str) -> list[FederationAgreement]:
        stmt = select(FederationAgreement).where(
            FederationAgreement.is_active.is_(True),
            FederationAgreement.status == "active",
        )
        result = await self.session.execute(stmt)
        return [
            a for a in result.scalars().all()
            if a.parties and org_id in a.parties
        ]

    async def get_agreement(self, agreement_id: str) -> Optional[FederationAgreement]:
        stmt = select(FederationAgreement).where(
            FederationAgreement.agreement_id == agreement_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_agreements(
        self,
        status: Optional[str] = None,
        agreement_type: Optional[str] = None,
    ) -> list[FederationAgreement]:
        stmt = select(FederationAgreement)
        if status:
            stmt = stmt.where(FederationAgreement.status == status)
        if agreement_type:
            stmt = stmt.where(FederationAgreement.agreement_type == agreement_type)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
