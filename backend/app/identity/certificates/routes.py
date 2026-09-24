from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.certificates.services import (
    APIKeyService,
    CertificateAuthorityService,
    CertificateService,
)

router = APIRouter(prefix="/certificates", tags=["NIAM Certificates"])


@router.post("/issue")
def issue_certificate(
    cert_type: str,
    subject: str,
    issuer: str | None = None,
    organization_id: str | None = None,
    person_id: str | None = None,
    machine_id: str | None = None,
    signature_algorithm: str = "SHA256withRSA",
    key_size: int = 2048,
    validity_days: int = 365,
    rotation_period_days: int | None = None,
    issuer_ca_id: str | None = None,
    db: Session = Depends(get_db),
):
    svc = CertificateService(db)
    cert = svc.issue_certificate(
        cert_type=cert_type,
        subject=subject,
        issuer=issuer,
        organization_id=organization_id,
        person_id=person_id,
        machine_id=machine_id,
        signature_algorithm=signature_algorithm,
        key_size=key_size,
        validity_days=validity_days,
        rotation_period_days=rotation_period_days,
        issuer_ca_id=issuer_ca_id,
    )
    return cert.to_dict()


@router.post("/{certificate_id}/revoke")
def revoke_certificate(
    certificate_id: str,
    reason: str,
    db: Session = Depends(get_db),
):
    svc = CertificateService(db)
    cert = svc.revoke_certificate(certificate_id, reason)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return {"status": "revoked", "certificate_id": certificate_id}


@router.post("/{certificate_id}/rotate")
def rotate_certificate(
    certificate_id: str,
    db: Session = Depends(get_db),
):
    svc = CertificateService(db)
    cert = svc.rotate_certificate(certificate_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return cert.to_dict()


@router.get("/{thumbprint}")
def get_certificate(
    thumbprint: str,
    db: Session = Depends(get_db),
):
    svc = CertificateService(db)
    cert = svc.get_certificate(thumbprint)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return cert.to_dict()


@router.get("/organization/{org_id}")
def list_org_certificates(
    org_id: str,
    db: Session = Depends(get_db),
):
    svc = CertificateService(db)
    certs = svc.list_for_organization(org_id)
    return [c.to_dict() for c in certs]


@router.get("/expiring")
def list_expiring_certificates(
    days: int = 30,
    db: Session = Depends(get_db),
):
    svc = CertificateService(db)
    certs = svc.list_expiring(days)
    return [c.to_dict() for c in certs]


@router.post("/authorities")
def register_ca(
    name: str,
    ca_type: str,
    organization_id: str | None = None,
    signing_algorithm: str = "SHA256withRSA",
    key_size: int = 4096,
    validity_days: int = 3650,
    path_length_constraint: int | None = None,
    parent_ca_id: str | None = None,
    db: Session = Depends(get_db),
):
    svc = CertificateAuthorityService(db)
    ca = svc.register_ca(
        name=name,
        ca_type=ca_type,
        organization_id=organization_id,
        signing_algorithm=signing_algorithm,
        key_size=key_size,
        validity_days=validity_days,
        path_length_constraint=path_length_constraint,
        parent_ca_id=parent_ca_id,
    )
    return ca.to_dict()


@router.get("/authorities")
def list_cas(
    db: Session = Depends(get_db),
):
    svc = CertificateAuthorityService(db)
    cas = svc.list_cas()
    return [ca.to_dict() for ca in cas]


@router.post("/authorities/{ca_id}/crl")
def generate_crl(
    ca_id: str,
    db: Session = Depends(get_db),
):
    svc = CertificateAuthorityService(db)
    crl = svc.generate_crl(ca_id)
    if not crl:
        raise HTTPException(status_code=404, detail="CA not found")
    return crl.to_dict()


@router.post("/api-keys")
def generate_api_key(
    name: str,
    organization_id: str,
    enterprise_account_id: str | None = None,
    person_id: str | None = None,
    scopes: list[str] | None = None,
    permissions: list[str] | None = None,
    allowed_ips: list[str] | None = None,
    allowed_referrers: list[str] | None = None,
    rate_limit: int | None = None,
    created_by: str | None = None,
    expires_at: str | None = None,
    db: Session = Depends(get_db),
):
    svc = APIKeyService(db)
    expires = None
    if expires_at:
        from datetime import datetime
        expires = datetime.fromisoformat(expires_at)
    ak, raw_key = svc.generate_key(
        name=name,
        organization_id=organization_id,
        enterprise_account_id=enterprise_account_id,
        person_id=person_id,
        scopes=scopes,
        permissions=permissions,
        allowed_ips=allowed_ips,
        allowed_referrers=allowed_referrers,
        rate_limit=rate_limit,
        created_by=created_by,
        expires_at=expires,
    )
    result = ak.to_dict()
    result["raw_key"] = raw_key
    return result


@router.get("/api-keys/organization/{org_id}")
def list_org_api_keys(
    org_id: str,
    db: Session = Depends(get_db),
):
    svc = APIKeyService(db)
    keys = svc.list_for_organization(org_id)
    return [k.to_dict() for k in keys]


@router.post("/api-keys/{api_key_id}/revoke")
def revoke_api_key(
    api_key_id: str,
    db: Session = Depends(get_db),
):
    svc = APIKeyService(db)
    ak = svc.revoke_key(api_key_id)
    if not ak:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"status": "revoked", "api_key_id": api_key_id}


@router.post("/api-keys/{api_key_id}/rotate")
def rotate_api_key(
    api_key_id: str,
    db: Session = Depends(get_db),
):
    svc = APIKeyService(db)
    result = svc.rotate_key(api_key_id)
    if not result:
        raise HTTPException(status_code=404, detail="API key not found")
    new_ak, raw_key = result
    resp = new_ak.to_dict()
    resp["raw_key"] = raw_key
    return resp
