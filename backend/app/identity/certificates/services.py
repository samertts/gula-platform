from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.certificates.models import (
    APIKey,
    CertificateAuthority,
    CertificateRevocationList,
    DigitalCertificate,
)


def _generate_key_pair() -> tuple[str, str]:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    return priv_pem, pub_pem


def _compute_thumbprint(cert_pem: str) -> str:
    return hashlib.sha256(cert_pem.encode()).hexdigest()


def _generate_api_key() -> tuple[str, str, str]:
    raw = "gula_" + secrets.token_urlsafe(32)
    prefix = raw[:10]
    h = hashlib.sha256(raw.encode()).hexdigest()
    return raw, prefix, h


def _now() -> datetime:
    return datetime.now(UTC)


class CertificateService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def issue_certificate(
        self,
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
    ) -> DigitalCertificate:
        priv_pem, pub_pem = _generate_key_pair()

        cert_pem = pub_pem
        thumbprint = _compute_thumbprint(cert_pem)
        serial_number = str(uuid.uuid4()).replace("-", "").upper()[:32]
        certificate_id = f"cert-{uuid.uuid4().hex[:16]}"
        issued_at = _now()
        expires_at = issued_at + timedelta(days=validity_days)

        cert = DigitalCertificate(
            id=self._ulid(),
            uuid=str(uuid.uuid4()),
            certificate_id=certificate_id,
            serial_number=serial_number,
            subject=subject,
            issuer=issuer or subject,
            certificate_type=cert_type,
            organization_id=organization_id,
            person_id=person_id,
            machine_id=machine_id,
            public_key=pub_pem,
            private_key_encrypted=priv_pem,
            certificate_pem=cert_pem,
            signature_algorithm=signature_algorithm,
            key_size=key_size,
            thumbprint=thumbprint,
            issued_at=issued_at,
            expires_at=expires_at,
            status="active",
            rotation_period_days=rotation_period_days,
            issuer_ca_id=issuer_ca_id,
            is_active=True,
        )
        self.session.add(cert)
        await self.session.flush()
        return cert

    async def revoke_certificate(
        self, certificate_id: str, reason: str
    ) -> DigitalCertificate | None:
        stmt = select(DigitalCertificate).where(
            DigitalCertificate.certificate_id == certificate_id,
            DigitalCertificate.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        cert = result.scalar_one_or_none()
        if not cert:
            return None
        now = _now()
        cert.status = "revoked"
        cert.revoked_at = now
        cert.revocation_reason = reason
        cert.revocation_date = now
        cert.is_active = False
        await self.session.flush()
        return cert

    async def rotate_certificate(self, certificate_id: str) -> DigitalCertificate | None:
        stmt = select(DigitalCertificate).where(
            DigitalCertificate.certificate_id == certificate_id,
        )
        result = await self.session.execute(stmt)
        old_cert = result.scalar_one_or_none()
        if not old_cert:
            return None

        old_cert.status = "expired"
        old_cert.is_active = False

        new_cert = await self.issue_certificate(
            cert_type=old_cert.certificate_type,
            subject=old_cert.subject,
            issuer=old_cert.issuer,
            organization_id=old_cert.organization_id,
            person_id=old_cert.person_id,
            machine_id=old_cert.machine_id,
            signature_algorithm=old_cert.signature_algorithm,
            key_size=old_cert.key_size or 2048,
            validity_days=old_cert.rotation_period_days or 365,
            issuer_ca_id=old_cert.issuer_ca_id,
        )
        new_cert.last_rotated_at = _now()
        old_cert.last_rotated_at = _now()
        await self.session.flush()
        return new_cert

    async def validate_certificate(self, thumbprint: str) -> dict[str, Any]:
        stmt = select(DigitalCertificate).where(
            DigitalCertificate.thumbprint == thumbprint,
        )
        result = await self.session.execute(stmt)
        cert = result.scalar_one_or_none()
        if not cert:
            return {"valid": False, "reason": "not_found"}
        if not cert.is_active:
            return {"valid": False, "reason": "inactive"}
        now = _now()
        if cert.status == "revoked":
            return {
                "valid": False,
                "reason": "revoked",
                "revoked_at": cert.revoked_at.isoformat() if cert.revoked_at else None,
            }
        if cert.expires_at and now > cert.expires_at:
            return {"valid": False, "reason": "expired", "expires_at": cert.expires_at.isoformat()}
        return {
            "valid": True,
            "subject": cert.subject,
            "certificate_type": cert.certificate_type,
            "expires_at": cert.expires_at.isoformat() if cert.expires_at else None,
        }

    async def get_certificate(self, thumbprint: str) -> DigitalCertificate | None:
        stmt = select(DigitalCertificate).where(DigitalCertificate.thumbprint == thumbprint)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_organization(self, org_id: str) -> list[DigitalCertificate]:
        stmt = (
            select(DigitalCertificate)
            .where(
                DigitalCertificate.organization_id == org_id,
                DigitalCertificate.is_active.is_(True),
            )
            .order_by(DigitalCertificate.issued_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_expiring(self, days: int = 30) -> list[DigitalCertificate]:
        cutoff = _now() + timedelta(days=days)
        stmt = (
            select(DigitalCertificate)
            .where(
                DigitalCertificate.expires_at <= cutoff,
                DigitalCertificate.expires_at > _now(),
                DigitalCertificate.status == "active",
                DigitalCertificate.is_active.is_(True),
            )
            .order_by(DigitalCertificate.expires_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def _ulid() -> str:
        return str(uuid.uuid4()).replace("-", "").upper()[:26]


class CertificateAuthorityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register_ca(
        self,
        name: str,
        ca_type: str,
        organization_id: str | None = None,
        signing_algorithm: str = "SHA256withRSA",
        key_size: int = 4096,
        validity_days: int = 3650,
        path_length_constraint: int | None = None,
        parent_ca_id: str | None = None,
    ) -> CertificateAuthority:
        priv_pem, pub_pem = _generate_key_pair()
        cert_pem = pub_pem
        thumbprint = _compute_thumbprint(cert_pem)
        serial_number = str(uuid.uuid4()).replace("-", "").upper()[:32]
        ca_id = f"ca-{uuid.uuid4().hex[:16]}"
        now = _now()
        valid_to = now + timedelta(days=validity_days)

        ca = CertificateAuthority(
            id=self._ulid(),
            uuid=str(uuid.uuid4()),
            ca_id=ca_id,
            name=name,
            ca_type=ca_type,
            organization_id=organization_id,
            certificate=cert_pem,
            private_key_encrypted=priv_pem,
            public_key=pub_pem,
            serial_number=serial_number,
            thumbprint=thumbprint,
            valid_from=now,
            valid_to=valid_to,
            status="active",
            signing_algorithm=signing_algorithm,
            key_size=key_size,
            path_length_constraint=path_length_constraint,
            issued_certificate_count=0,
            revoked_certificate_count=0,
            parent_ca_id=parent_ca_id,
            is_active=True,
        )
        self.session.add(ca)
        await self.session.flush()
        return ca

    async def get_ca(self, ca_id: str) -> CertificateAuthority | None:
        stmt = select(CertificateAuthority).where(
            CertificateAuthority.ca_id == ca_id,
            CertificateAuthority.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_cas(self) -> list[CertificateAuthority]:
        stmt = (
            select(CertificateAuthority)
            .where(CertificateAuthority.is_active.is_(True))
            .order_by(CertificateAuthority.valid_from.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def generate_crl(self, ca_id: str) -> CertificateRevocationList | None:
        ca = await self.get_ca(ca_id)
        if not ca:
            return None

        revoked = select(DigitalCertificate).where(
            DigitalCertificate.issuer_ca_id == ca.id,
            DigitalCertificate.status == "revoked",
        )
        result = await self.session.execute(revoked)
        revoked_certs = list(result.scalars().all())

        revoked_list = []
        for rc in revoked_certs:
            revoked_list.append(
                {
                    "serial_number": rc.serial_number,
                    "revocation_date": rc.revocation_date.isoformat()
                    if rc.revocation_date
                    else None,
                    "reason": rc.revocation_reason,
                }
            )

        now = _now()
        next_update = now + timedelta(days=7)
        crl_id = f"crl-{uuid.uuid4().hex[:16]}"

        import json

        crl_pem = json.dumps({"crl_id": crl_id, "ca_id": ca_id, "issued": now.isoformat()})

        crl = CertificateRevocationList(
            id=self._ulid(),
            uuid=str(uuid.uuid4()),
            crl_id=crl_id,
            ca_id=ca.id,
            crl_number=(ca.revoked_certificate_count or 0) + 1,
            this_update=now,
            next_update=next_update,
            revoked_certificates=revoked_list,
            crl_pem=crl_pem,
            is_active=True,
        )
        self.session.add(crl)
        ca.revoked_certificate_count = (ca.revoked_certificate_count or 0) + 1
        await self.session.flush()
        return crl

    async def get_crl(self, ca_id: str) -> CertificateRevocationList | None:
        ca = await self.get_ca(ca_id)
        if not ca:
            return None
        stmt = (
            select(CertificateRevocationList)
            .where(
                CertificateRevocationList.ca_id == ca.id,
                CertificateRevocationList.is_active.is_(True),
            )
            .order_by(CertificateRevocationList.this_update.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _ulid() -> str:
        return str(uuid.uuid4()).replace("-", "").upper()[:26]


class APIKeyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def generate_key(
        self,
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
        expires_at: datetime | None = None,
    ) -> tuple[APIKey, str]:
        raw_key, prefix, key_hash = _generate_api_key()
        api_key_id = f"ak-{uuid.uuid4().hex[:16]}"

        ak = APIKey(
            id=self._ulid(),
            uuid=str(uuid.uuid4()),
            api_key_id=api_key_id,
            key_prefix=prefix,
            key_hash=key_hash,
            name=name,
            organization_id=organization_id,
            enterprise_account_id=enterprise_account_id,
            person_id=person_id,
            scopes=scopes or [],
            permissions=permissions or [],
            allowed_ips=allowed_ips,
            allowed_referrers=allowed_referrers,
            rate_limit=rate_limit,
            created_by=created_by,
            expires_at=expires_at,
            status="active",
            is_active=True,
        )
        self.session.add(ak)
        await self.session.flush()
        return ak, raw_key

    async def validate_key(self, key_prefix: str, key: str) -> APIKey | None:
        stmt = select(APIKey).where(
            APIKey.key_prefix == key_prefix,
            APIKey.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        ak = result.scalar_one_or_none()
        if not ak:
            return None

        computed_hash = hashlib.sha256(key.encode()).hexdigest()
        if not hmac.compare_digest(computed_hash, ak.key_hash):
            return None

        if ak.expires_at and _now() > ak.expires_at:
            return None

        return ak

    async def revoke_key(self, api_key_id: str) -> APIKey | None:
        stmt = select(APIKey).where(
            APIKey.api_key_id == api_key_id,
            APIKey.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        ak = result.scalar_one_or_none()
        if not ak:
            return None
        ak.status = "revoked"
        ak.is_active = False
        await self.session.flush()
        return ak

    async def rotate_key(self, api_key_id: str) -> tuple[APIKey, str] | None:
        stmt = select(APIKey).where(
            APIKey.api_key_id == api_key_id,
        )
        result = await self.session.execute(stmt)
        old_ak = result.scalar_one_or_none()
        if not old_ak:
            return None

        old_ak.status = "revoked"
        old_ak.is_active = False
        old_ak.rotated_at = _now()

        new_ak, raw_key = await self.generate_key(
            name=old_ak.name,
            organization_id=old_ak.organization_id,
            enterprise_account_id=old_ak.enterprise_account_id,
            person_id=old_ak.person_id,
            scopes=old_ak.scopes,
            permissions=old_ak.permissions,
            allowed_ips=old_ak.allowed_ips,
            allowed_referrers=old_ak.allowed_referrers,
            rate_limit=old_ak.rate_limit,
            created_by=old_ak.created_by,
            expires_at=old_ak.expires_at,
        )
        await self.session.flush()
        return new_ak, raw_key

    async def list_for_organization(self, org_id: str) -> list[APIKey]:
        stmt = (
            select(APIKey)
            .where(
                APIKey.organization_id == org_id,
                APIKey.is_active.is_(True),
            )
            .order_by(APIKey.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, api_key_id: str) -> APIKey | None:
        stmt = select(APIKey).where(APIKey.api_key_id == api_key_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _ulid() -> str:
        return str(uuid.uuid4()).replace("-", "").upper()[:26]
