from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import time
from datetime import datetime, timedelta

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app._compat import UTC
from app.config import SECRET_KEY
from app.national.base import _ulid
from app.national.exceptions import NationalDomainError

from .models import (
    Partner,
    PartnerAuditLog,
    PartnerCertificate,
    PartnerCredential,
    PartnerRateLimit,
)

logger = logging.getLogger("gula.ecosystem.partners")


class PartnerNotFoundError(NationalDomainError):
    def __init__(self, partner_id: str) -> None:
        self.partner_id = partner_id
        super().__init__(f"Partner not found: {partner_id}")


class CredentialNotFoundError(NationalDomainError):
    def __init__(self, credential_id: int) -> None:
        self.credential_id = credential_id
        super().__init__(f"Credential not found: {credential_id}")


class RateLimitExceededError(NationalDomainError):
    def __init__(self, partner_id: str, endpoint: str) -> None:
        self.partner_id = partner_id
        self.endpoint = endpoint
        super().__init__(f"Rate limit exceeded for partner {partner_id} on {endpoint}")


class PartnerManager:
    def __init__(self, db: Session) -> None:
        self._db = db

    def register_partner(self, data: dict) -> Partner:
        partner = Partner(
            id=_ulid(),
            name=data["name"],
            org_type=data["org_type"],
            contact_name=data.get("contact_name"),
            contact_email=data.get("contact_email"),
            contact_phone=data.get("contact_phone"),
            status="active",
            tier=data.get("tier", "bronze"),
            agreement_date=data.get("agreement_date"),
            agreement_version=data.get("agreement_version"),
            api_quota=data.get("api_quota", 1000),
            rate_limit=data.get("rate_limit", 60),
            created_by=data.get("created_by"),
            metadata_=data.get("metadata", {}),
        )
        self._db.add(partner)
        self._db.commit()
        self._db.refresh(partner)
        logger.info("Partner registered: %s (%s)", partner.id, partner.name)
        return partner

    def update_partner(self, partner_id: str, data: dict) -> Partner:
        partner = self.get_partner(partner_id)
        for field in ("name", "org_type", "contact_name", "contact_email", "contact_phone", "tier",
                      "agreement_date", "agreement_version", "api_quota", "rate_limit", "metadata_"):
            if field in data:
                setattr(partner, field, data[field])
        partner.updated_at = datetime.now(UTC)
        self._db.commit()
        self._db.refresh(partner)
        return partner

    def suspend_partner(self, partner_id: str, reason: str = "") -> Partner:
        partner = self.get_partner(partner_id)
        partner.status = "suspended"
        partner.updated_at = datetime.now(UTC)
        self._db.commit()
        self._db.refresh(partner)
        logger.warning("Partner suspended: %s reason=%s", partner_id, reason)
        return partner

    def activate_partner(self, partner_id: str) -> Partner:
        partner = self.get_partner(partner_id)
        partner.status = "active"
        partner.updated_at = datetime.now(UTC)
        self._db.commit()
        self._db.refresh(partner)
        return partner

    def disable_partner(self, partner_id: str, reason: str = "") -> Partner:
        partner = self.get_partner(partner_id)
        partner.status = "disabled"
        partner.updated_at = datetime.now(UTC)
        self._db.commit()
        self._db.refresh(partner)
        logger.warning("Partner disabled: %s reason=%s", partner_id, reason)
        return partner

    def get_partner(self, partner_id: str) -> Partner:
        partner = self._db.query(Partner).filter(Partner.id == partner_id, ~Partner.is_deleted).first()
        if not partner:
            raise PartnerNotFoundError(partner_id)
        return partner

    def list_partners(
        self,
        status: str | None = None,
        tier: str | None = None,
        org_type: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Partner]:
        query = self._db.query(Partner).filter(~~Partner.is_deleted)
        if status:
            query = query.filter(Partner.status == status)
        if tier:
            query = query.filter(Partner.tier == tier)
        if org_type:
            query = query.filter(Partner.org_type == org_type)
        return query.order_by(desc(Partner.created_at)).offset(offset).limit(limit).all()

    def count_partners(self, status: str | None = None) -> int:
        query = self._db.query(func.count(Partner.id)).filter(~~Partner.is_deleted)
        if status:
            query = query.filter(Partner.status == status)
        return query.scalar() or 0


class CredentialManager:
    def __init__(self, db: Session) -> None:
        self._db = db

    def issue_api_key(self, partner_id: str, name: str, expires_in_days: int | None = None) -> PartnerCredential:
        partner = self._db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise PartnerNotFoundError(partner_id)

        api_key = f"gula_{secrets.token_urlsafe(32)}"
        expires_at = datetime.now(UTC) + timedelta(days=expires_in_days) if expires_in_days else None

        credential = PartnerCredential(
            partner_id=partner_id,
            credential_type="api_key",
            credential_name=name,
            credential_value=self._hash_api_key(api_key),
            expires_at=expires_at,
            status="active",
        )
        self._db.add(credential)
        self._db.commit()
        self._db.refresh(credential)

        return api_key

    def revoke_credential(self, credential_id: int) -> None:
        credential = self._db.query(PartnerCredential).filter(PartnerCredential.id == credential_id).first()
        if not credential:
            raise CredentialNotFoundError(credential_id)
        credential.status = "revoked"
        credential.updated_at = datetime.now(UTC)
        self._db.commit()

    def rotate_credential(self, credential_id: int, expires_in_days: int | None = None) -> str:
        credential = self._db.query(PartnerCredential).filter(PartnerCredential.id == credential_id).first()
        if not credential:
            raise CredentialNotFoundError(credential_id)
        new_api_key = f"gula_{secrets.token_urlsafe(32)}"
        credential.credential_value = self._hash_api_key(new_api_key)
        credential.expires_at = datetime.now(UTC) + timedelta(days=expires_in_days) if expires_in_days else None
        credential.updated_at = datetime.now(UTC)
        self._db.commit()
        return new_api_key

    def validate_credential(self, partner_id: str, credential_type: str, credential_value: str) -> bool:
        credential = (
            self._db.query(PartnerCredential)
            .filter(
                PartnerCredential.partner_id == partner_id,
                PartnerCredential.credential_type == credential_type,
                PartnerCredential.status == "active",
            )
            .first()
        )
        if not credential:
            return False
        if credential.expires_at and credential.expires_at < datetime.now(UTC):
            return False
        if credential_type == "api_key":
            expected = self._hash_api_key(credential_value)
            if not hmac.compare_digest(credential.credential_value, expected):
                return False
        elif credential.credential_value != credential_value:
            return False
        credential.last_used_at = datetime.now(UTC)
        self._db.commit()
        return True

    def get_partner_credentials(self, partner_id: str) -> list[PartnerCredential]:
        return (
            self._db.query(PartnerCredential)
            .filter(PartnerCredential.partner_id == partner_id)
            .order_by(desc(PartnerCredential.created_at))
            .all()
        )

    def _hash_api_key(self, api_key: str) -> str:
        """Return a server-bound, non-reversible API-key fingerprint."""
        return hmac.new(
            SECRET_KEY.encode("utf-8"),
            api_key.encode("utf-8"),
            hashlib.sha3_512,
        ).hexdigest()


class CertificateManager:
    def __init__(self, db: Session) -> None:
        self._db = db

    def register_certificate(self, partner_id: str, data: dict) -> PartnerCertificate:
        partner = self._db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise PartnerNotFoundError(partner_id)

        pem = data["certificate_pem"]
        fingerprint = hashlib.sha256(pem.encode()).hexdigest()

        certificate = PartnerCertificate(
            id=_ulid(),
            partner_id=partner_id,
            certificate_pem=pem,
            certificate_serial=data.get("certificate_serial"),
            issuer=data.get("issuer"),
            valid_from=datetime.fromisoformat(data["valid_from"]) if isinstance(data.get("valid_from"), str) else data.get("valid_from", datetime.now(UTC)),
            valid_to=datetime.fromisoformat(data["valid_to"]) if isinstance(data.get("valid_to"), str) else data.get("valid_to", datetime.now(UTC) + timedelta(days=365)),
            status="active",
            fingerprint=fingerprint,
        )
        self._db.add(certificate)
        self._db.commit()
        self._db.refresh(certificate)
        return certificate

    def validate_certificate(self, fingerprint: str) -> bool:
        cert = (
            self._db.query(PartnerCertificate)
            .filter(
                PartnerCertificate.fingerprint == fingerprint,
                PartnerCertificate.status == "active",
            )
            .first()
        )
        if not cert:
            return False
        now = datetime.now(UTC)
        return not (now < cert.valid_from or now > cert.valid_to)

    def revoke_certificate(self, certificate_id: str) -> None:
        cert = self._db.query(PartnerCertificate).filter(PartnerCertificate.id == certificate_id).first()
        if not cert:
            return
        cert.status = "revoked"
        cert.updated_at = datetime.now(UTC)
        self._db.commit()

    def get_expiring_certificates(self, days: int = 30) -> list[PartnerCertificate]:
        cutoff = datetime.now(UTC) + timedelta(days=days)
        return (
            self._db.query(PartnerCertificate)
            .filter(
                PartnerCertificate.status == "active",
                PartnerCertificate.valid_to <= cutoff,
            )
            .all()
        )

    def get_partner_certificates(self, partner_id: str) -> list[PartnerCertificate]:
        return (
            self._db.query(PartnerCertificate)
            .filter(PartnerCertificate.partner_id == partner_id)
            .order_by(desc(PartnerCertificate.created_at))
            .all()
        )


class RateLimitManager:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._buckets: dict[str, dict] = {}

    def check_rate_limit(self, partner_id: str, endpoint: str) -> bool:
        limit = self._get_rate_limit(partner_id, endpoint)
        if not limit:
            return True

        key = f"{partner_id}:{endpoint}"
        now = time.time()
        bucket = self._buckets.get(key, {"minute": [], "hour": [], "day": []})

        bucket["minute"] = [t for t in bucket["minute"] if now - t < 60]
        bucket["hour"] = [t for t in bucket["hour"] if now - t < 3600]
        bucket["day"] = [t for t in bucket["day"] if now - t < 86400]

        if len(bucket["minute"]) >= limit.requests_per_minute:
            return False
        if len(bucket["hour"]) >= limit.requests_per_hour:
            return False
        if len(bucket["day"]) >= limit.requests_per_day:
            return False

        bucket["minute"].append(now)
        bucket["hour"].append(now)
        bucket["day"].append(now)
        self._buckets[key] = bucket
        return True

    def update_quota(self, partner_id: str, endpoint_pattern: str, data: dict) -> PartnerRateLimit:
        limit = (
            self._db.query(PartnerRateLimit)
            .filter(
                PartnerRateLimit.partner_id == partner_id,
                PartnerRateLimit.endpoint_pattern == endpoint_pattern,
            )
            .first()
        )
        if limit:
            for field in ("requests_per_minute", "requests_per_hour", "requests_per_day", "concurrent_limit"):
                if field in data:
                    setattr(limit, field, data[field])
            limit.updated_at = datetime.now(UTC)
        else:
            limit = PartnerRateLimit(
                partner_id=partner_id,
                endpoint_pattern=endpoint_pattern,
                requests_per_minute=data.get("requests_per_minute", 60),
                requests_per_hour=data.get("requests_per_hour", 1000),
                requests_per_day=data.get("requests_per_day", 10000),
                concurrent_limit=data.get("concurrent_limit", 10),
            )
            self._db.add(limit)
        self._db.commit()
        self._db.refresh(limit)
        return limit

    def get_usage_stats(self, partner_id: str) -> dict:
        now = time.time()
        stats = {"minute": 0, "hour": 0, "day": 0}
        for key, bucket in self._buckets.items():
            if key.startswith(f"{partner_id}:"):
                stats["minute"] += sum(1 for t in bucket["minute"] if now - t < 60)
                stats["hour"] += sum(1 for t in bucket["hour"] if now - t < 3600)
                stats["day"] += sum(1 for t in bucket["day"] if now - t < 86400)
        return stats

    def _get_rate_limit(self, partner_id: str, endpoint: str) -> PartnerRateLimit | None:
        limits = (
            self._db.query(PartnerRateLimit)
            .filter(PartnerRateLimit.partner_id == partner_id)
            .all()
        )
        for limit in limits:
            if self._match_pattern(endpoint, limit.endpoint_pattern):
                return limit

        partner = self._db.query(Partner).filter(Partner.id == partner_id).first()
        if partner:
            return PartnerRateLimit(
                partner_id=partner_id,
                endpoint_pattern="*",
                requests_per_minute=partner.rate_limit,
                requests_per_hour=partner.rate_limit * 60,
                requests_per_day=partner.api_quota,
                concurrent_limit=10,
            )
        return None

    def _match_pattern(self, endpoint: str, pattern: str) -> bool:
        if pattern == "*":
            return True
        import fnmatch
        return fnmatch.fnmatch(endpoint, pattern)


class AuditManager:
    def __init__(self, db: Session) -> None:
        self._db = db

    def log_action(
        self,
        partner_id: str,
        action: str,
        resource: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        status: str = "success",
    ) -> PartnerAuditLog:
        entry = PartnerAuditLog(
            partner_id=partner_id,
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
        )
        self._db.add(entry)
        self._db.commit()
        self._db.refresh(entry)
        return entry

    def query_logs(
        self,
        partner_id: str | None = None,
        action: str | None = None,
        status: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PartnerAuditLog]:
        query = self._db.query(PartnerAuditLog)
        if partner_id:
            query = query.filter(PartnerAuditLog.partner_id == partner_id)
        if action:
            query = query.filter(PartnerAuditLog.action == action)
        if status:
            query = query.filter(PartnerAuditLog.status == status)
        if from_date:
            query = query.filter(PartnerAuditLog.created_at >= from_date)
        if to_date:
            query = query.filter(PartnerAuditLog.created_at <= to_date)
        return query.order_by(desc(PartnerAuditLog.created_at)).offset(offset).limit(limit).all()

    def generate_audit_report(
        self,
        partner_id: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> dict:
        query = self._db.query(
            PartnerAuditLog.action,
            func.count(PartnerAuditLog.id).label("count"),
            func.count(PartnerAuditLog.id).filter(PartnerAuditLog.status == "success").label("success_count"),
            func.count(PartnerAuditLog.id).filter(PartnerAuditLog.status == "failure").label("failure_count"),
        ).filter(PartnerAuditLog.partner_id == partner_id)
        if from_date:
            query = query.filter(PartnerAuditLog.created_at >= from_date)
        if to_date:
            query = query.filter(PartnerAuditLog.created_at <= to_date)
        query = query.group_by(PartnerAuditLog.action)

        rows = query.all()
        total = sum(r.count for r in rows)
        return {
            "partner_id": partner_id,
            "total_actions": total,
            "actions": {r.action: {"total": r.count, "success": r.success_count, "failure": r.failure_count} for r in rows},
        }
