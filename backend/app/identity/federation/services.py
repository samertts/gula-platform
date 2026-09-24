from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app._compat import UTC
from app.identity.federation.models import (
    CrossOrganizationTrust,
    FederatedIdentity,
    FederatedProvider,
    FederatedSession,
    FederationAgreement,
)


class FederationService:

    def __init__(self, session: Session) -> None:
        self.session = session

    def register_provider(
        self,
        provider_id: str,
        name_en: str,
        name_ar: str | None,
        provider_type: str,
        issuer_url: str,
        authorization_endpoint: str | None = None,
        token_endpoint: str | None = None,
        jwks_uri: str | None = None,
        userinfo_endpoint: str | None = None,
        client_id: str | None = None,
        client_secret_encrypted: str | None = None,
        scopes: list[str] | None = None,
        redirect_uris: list[str] | None = None,
        certificate: str | None = None,
        signature_algorithm: str | None = None,
        trust_anchor_id: str | None = None,
        metadata_url: str | None = None,
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
        self.session.flush()
        return provider

    def get_provider(self, provider_id: str) -> FederatedProvider | None:
        stmt = select(FederatedProvider).where(
            FederatedProvider.provider_id == provider_id,
            FederatedProvider.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def update_provider(
        self,
        provider_id: str,
        **kwargs: Any,
    ) -> FederatedProvider | None:
        provider = self.get_provider(provider_id)
        if not provider:
            return None
        for key, value in kwargs.items():
            if hasattr(provider, key) and value is not None:
                setattr(provider, key, value)
        self.session.flush()
        return provider

    def list_providers(
        self,
        status: str | None = None,
    ) -> list[FederatedProvider]:
        stmt = select(FederatedProvider).where(FederatedProvider.is_active.is_(True))
        if status:
            stmt = stmt.where(FederatedProvider.status == status)
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def link_identity(
        self,
        person_id: str,
        provider_id: str,
        external_subject_id: str,
        external_attributes: dict[str, Any] | None = None,
        identity_id: str | None = None,
    ) -> FederatedIdentity:
        existing = self.find_by_external_id(provider_id, external_subject_id)
        if existing:
            existing.status = "active"
            existing.unlinked_at = None
            existing.unlink_reason = None
            existing.is_active = True
            self.session.flush()
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
        self.session.flush()
        return identity

    def unlink_identity(self, fed_id: str, reason: str) -> FederatedIdentity | None:
        stmt = select(FederatedIdentity).where(
            FederatedIdentity.fed_id == fed_id,
            FederatedIdentity.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        identity = result.scalar_one_or_none()
        if not identity:
            return None
        identity.status = "unlinked"
        identity.unlinked_at = datetime.now(UTC)
        identity.unlink_reason = reason
        identity.is_active = False
        self.session.flush()
        return identity

    def find_by_external_id(
        self,
        provider_id: str,
        external_subject_id: str,
    ) -> FederatedIdentity | None:
        stmt = select(FederatedIdentity).where(
            FederatedIdentity.provider_id == provider_id,
            FederatedIdentity.external_subject_id == external_subject_id,
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def get_identities_for_person(self, person_id: str) -> list[FederatedIdentity]:
        stmt = select(FederatedIdentity).where(
            FederatedIdentity.person_id == person_id,
            FederatedIdentity.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def create_session(
        self,
        account_id: str,
        provider_id: str,
        fed_identity_id: str,
        tokens: dict[str, Any],
        attributes: dict[str, Any] | None = None,
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
        self.session.flush()
        return fed_session

    def terminate_session(self, session_id: str) -> FederatedSession | None:
        stmt = select(FederatedSession).where(
            FederatedSession.session_id == session_id,
            FederatedSession.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        fed_session = result.scalar_one_or_none()
        if not fed_session:
            return None
        fed_session.terminated_at = datetime.now(UTC)
        fed_session.is_active = False
        self.session.flush()
        return fed_session


class CrossOrgTrustService:

    def __init__(self, session: Session) -> None:
        self.session = session

    def establish_trust(
        self,
        source_org_id: str,
        target_org_id: str,
        trust_level: str,
        agreement: dict[str, Any] | None = None,
        trust_type: str = "bilateral",
        established_by: str | None = None,
        expires_at: datetime | None = None,
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
        self.session.flush()
        return trust

    def get_trust_relationships(self, org_id: str) -> list[CrossOrganizationTrust]:
        stmt = select(CrossOrganizationTrust).where(
            CrossOrganizationTrust.is_active.is_(True),
            (
                (CrossOrganizationTrust.source_org_id == org_id)
                | (CrossOrganizationTrust.target_org_id == org_id)
            ),
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def suspend_trust(self, trust_id: str) -> CrossOrganizationTrust | None:
        stmt = select(CrossOrganizationTrust).where(
            CrossOrganizationTrust.trust_id == trust_id,
            CrossOrganizationTrust.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        trust = result.scalar_one_or_none()
        if not trust:
            return None
        trust.status = "suspended"
        self.session.flush()
        return trust

    def terminate_trust(self, trust_id: str) -> CrossOrganizationTrust | None:
        stmt = select(CrossOrganizationTrust).where(
            CrossOrganizationTrust.trust_id == trust_id,
            CrossOrganizationTrust.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        trust = result.scalar_one_or_none()
        if not trust:
            return None
        trust.status = "terminated"
        trust.is_active = False
        self.session.flush()
        return trust


class FederationAgreementService:

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_agreement(
        self,
        name: str,
        parties: list[str],
        agreement_type: str,
        scope: dict[str, Any] | None = None,
        terms: dict[str, Any] | None = None,
        security_requirements: dict[str, Any] | None = None,
        effective_date: datetime | None = None,
        expiry_date: datetime | None = None,
        governing_law: str | None = None,
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
        self.session.flush()
        return agreement

    def sign_agreement(
        self,
        agreement_id: str,
        signed_by: list[dict[str, Any]],
    ) -> FederationAgreement | None:
        stmt = select(FederationAgreement).where(
            FederationAgreement.agreement_id == agreement_id,
        )
        result = self.session.execute(stmt)
        agreement = result.scalar_one_or_none()
        if not agreement:
            return None
        agreement.signed_by = signed_by
        agreement.signed_at = datetime.now(UTC)
        if agreement.status == "draft":
            agreement.status = "active"
        self.session.flush()
        return agreement

    def get_active_agreements(self, org_id: str) -> list[FederationAgreement]:
        stmt = select(FederationAgreement).where(
            FederationAgreement.is_active.is_(True),
            FederationAgreement.status == "active",
        )
        result = self.session.execute(stmt)
        return [
            a for a in result.scalars().all()
            if a.parties and org_id in a.parties
        ]

    def get_agreement(self, agreement_id: str) -> FederationAgreement | None:
        stmt = select(FederationAgreement).where(
            FederationAgreement.agreement_id == agreement_id,
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def list_agreements(
        self,
        status: str | None = None,
        agreement_type: str | None = None,
    ) -> list[FederationAgreement]:
        stmt = select(FederationAgreement)
        if status:
            stmt = stmt.where(FederationAgreement.status == status)
        if agreement_type:
            stmt = stmt.where(FederationAgreement.agreement_type == agreement_type)
        result = self.session.execute(stmt)
        return list(result.scalars().all())
