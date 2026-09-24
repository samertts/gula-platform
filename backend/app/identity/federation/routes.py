from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.federation.services import (
    CrossOrgTrustService,
    FederationAgreementService,
    FederationService,
)

router = APIRouter(prefix="/federation", tags=["NIAM Federation"])


@router.post("/providers")
def register_provider(
    provider_id: str,
    name_en: str,
    name_ar: str | None = None,
    provider_type: str = "oauth2",
    issuer_url: str = ...,
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
    db: Session = Depends(get_db),
):
    svc = FederationService(db)
    provider = svc.register_provider(
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
    )
    return {
        "uuid": provider.uuid,
        "provider_id": provider.provider_id,
        "status": provider.status,
    }


@router.get("/providers")
def list_providers(
    status: str | None = None,
    db: Session = Depends(get_db),
):
    svc = FederationService(db)
    providers = svc.list_providers(status=status)
    return [
        {
            "uuid": p.uuid,
            "provider_id": p.provider_id,
            "name_en": p.name_en,
            "provider_type": p.provider_type,
            "status": p.status,
        }
        for p in providers
    ]


@router.get("/providers/{provider_id}")
def get_provider(
    provider_id: str,
    db: Session = Depends(get_db),
):
    svc = FederationService(db)
    provider = svc.get_provider(provider_id)
    if not provider:
        return {"error": "not_found"}
    return provider.to_dict()


@router.put("/providers/{provider_id}")
def update_provider(
    provider_id: str,
    body: dict[str, Any],
    db: Session = Depends(get_db),
):
    svc = FederationService(db)
    provider = svc.update_provider(provider_id, **body)
    if not provider:
        return {"error": "not_found"}
    return provider.to_dict()


@router.post("/identities/link")
def link_identity(
    person_id: str,
    provider_id: str,
    external_subject_id: str,
    external_attributes: dict[str, Any] | None = None,
    identity_id: str | None = None,
    db: Session = Depends(get_db),
):
    svc = FederationService(db)
    identity = svc.link_identity(
        person_id=person_id,
        provider_id=provider_id,
        external_subject_id=external_subject_id,
        external_attributes=external_attributes,
        identity_id=identity_id,
    )
    return {
        "uuid": identity.uuid,
        "fed_id": identity.fed_id,
        "status": identity.status,
    }


@router.post("/identities/unlink")
def unlink_identity(
    fed_id: str,
    reason: str,
    db: Session = Depends(get_db),
):
    svc = FederationService(db)
    identity = svc.unlink_identity(fed_id, reason)
    if not identity:
        return {"error": "not_found"}
    return {
        "uuid": identity.uuid,
        "fed_id": identity.fed_id,
        "status": identity.status,
        "unlinked_at": identity.unlinked_at.isoformat() if identity.unlinked_at else None,
    }


@router.get("/identities/{person_id}")
def get_person_identities(
    person_id: str,
    db: Session = Depends(get_db),
):
    svc = FederationService(db)
    identities = svc.get_identities_for_person(person_id)
    return [
        {
            "uuid": i.uuid,
            "fed_id": i.fed_id,
            "provider_id": i.provider_id,
            "external_subject_id": i.external_subject_id,
            "status": i.status,
            "linked_at": i.linked_at.isoformat(),
        }
        for i in identities
    ]


@router.post("/trust")
def establish_trust(
    source_org_id: str,
    target_org_id: str,
    trust_level: str = "full",
    trust_type: str = "bilateral",
    agreement: dict[str, Any] | None = None,
    established_by: str | None = None,
    db: Session = Depends(get_db),
):
    svc = CrossOrgTrustService(db)
    trust = svc.establish_trust(
        source_org_id=source_org_id,
        target_org_id=target_org_id,
        trust_level=trust_level,
        trust_type=trust_type,
        agreement=agreement,
        established_by=established_by,
    )
    return {
        "uuid": trust.uuid,
        "trust_id": trust.trust_id,
        "status": trust.status,
    }


@router.get("/trust/{org_id}")
def get_trust_relationships(
    org_id: str,
    db: Session = Depends(get_db),
):
    svc = CrossOrgTrustService(db)
    relationships = svc.get_trust_relationships(org_id)
    return [
        {
            "uuid": r.uuid,
            "trust_id": r.trust_id,
            "source_org_id": r.source_org_id,
            "target_org_id": r.target_org_id,
            "trust_level": r.trust_level,
            "status": r.status,
        }
        for r in relationships
    ]


@router.post("/agreements")
def create_agreement(
    name: str,
    parties: list[str],
    agreement_type: str,
    scope: dict[str, Any] | None = None,
    terms: dict[str, Any] | None = None,
    security_requirements: dict[str, Any] | None = None,
    effective_date: str | None = None,
    expiry_date: str | None = None,
    governing_law: str | None = None,
    db: Session = Depends(get_db),
):
    svc = FederationAgreementService(db)
    agreement = svc.create_agreement(
        name=name,
        parties=parties,
        agreement_type=agreement_type,
        scope=scope,
        terms=terms,
        security_requirements=security_requirements,
        governing_law=governing_law,
    )
    return {
        "uuid": agreement.uuid,
        "agreement_id": agreement.agreement_id,
        "status": agreement.status,
    }


@router.get("/agreements")
def list_agreements(
    status: str | None = None,
    agreement_type: str | None = None,
    db: Session = Depends(get_db),
):
    svc = FederationAgreementService(db)
    agreements = svc.list_agreements(
        status=status,
        agreement_type=agreement_type,
    )
    return [
        {
            "uuid": a.uuid,
            "agreement_id": a.agreement_id,
            "name": a.name,
            "agreement_type": a.agreement_type,
            "status": a.status,
        }
        for a in agreements
    ]


@router.post("/agreements/{agreement_id}/sign")
def sign_agreement(
    agreement_id: str,
    signed_by: list[dict[str, Any]],
    db: Session = Depends(get_db),
):
    svc = FederationAgreementService(db)
    agreement = svc.sign_agreement(
        agreement_id=agreement_id,
        signed_by=signed_by,
    )
    if not agreement:
        return {"error": "not_found"}
    return {
        "uuid": agreement.uuid,
        "agreement_id": agreement.agreement_id,
        "status": agreement.status,
        "signed_at": agreement.signed_at.isoformat() if agreement.signed_at else None,
    }


@router.get("/agreements/{agreement_id}")
def get_agreement(
    agreement_id: str,
    db: Session = Depends(get_db),
):
    svc = FederationAgreementService(db)
    agreement = svc.get_agreement(agreement_id)
    if not agreement:
        return {"error": "not_found"}
    return agreement.to_dict()


@router.post("/sessions")
def create_federated_session(
    account_id: str,
    provider_id: str,
    fed_identity_id: str,
    tokens: dict[str, Any],
    attributes: dict[str, Any] | None = None,
    db: Session = Depends(get_db),
):
    svc = FederationService(db)
    fed_session = svc.create_session(
        account_id=account_id,
        provider_id=provider_id,
        fed_identity_id=fed_identity_id,
        tokens=tokens,
        attributes=attributes,
    )
    return {
        "session_id": fed_session.session_id,
        "started_at": fed_session.started_at.isoformat(),
    }


@router.post("/sessions/{session_id}/terminate")
def terminate_federated_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    svc = FederationService(db)
    fed_session = svc.terminate_session(session_id)
    if not fed_session:
        return {"error": "not_found"}
    return {
        "session_id": fed_session.session_id,
        "terminated_at": fed_session.terminated_at.isoformat() if fed_session.terminated_at else None,
    }


@router.post("/trust/{trust_id}/suspend")
def suspend_trust(
    trust_id: str,
    db: Session = Depends(get_db),
):
    svc = CrossOrgTrustService(db)
    trust = svc.suspend_trust(trust_id)
    if not trust:
        return {"error": "not_found"}
    return {"trust_id": trust.trust_id, "status": trust.status}


@router.post("/trust/{trust_id}/terminate")
def terminate_trust(
    trust_id: str,
    db: Session = Depends(get_db),
):
    svc = CrossOrgTrustService(db)
    trust = svc.terminate_trust(trust_id)
    if not trust:
        return {"error": "not_found"}
    return {"trust_id": trust.trust_id, "status": trust.status}
