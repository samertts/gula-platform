from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.citizen_platform.enums import CertificateType

logger = logging.getLogger("gula.citizen.certificates")


@dataclass
class HealthCertificate:
    id: str = ""
    citizen_id: str = ""
    certificate_type: CertificateType = CertificateType.HEALTH
    certificate_number: str = ""
    issuer: str = ""
    issued_at: str = ""
    valid_from: str = ""
    valid_until: str = ""
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MedicalLeaveDocument:
    id: str = ""
    citizen_id: str = ""
    leave_number: str = ""
    diagnosis: str = ""
    from_date: str = ""
    to_date: str = ""
    total_days: int = 0
    issued_by: str = ""
    issued_by_name: str = ""
    facility_name: str = ""
    status: str = "active"
    notes: str = ""


@dataclass
class Referral:
    id: str = ""
    citizen_id: str = ""
    from_facility: str = ""
    to_facility: str = ""
    from_practitioner: str = ""
    to_practitioner: str = ""
    reason: str = ""
    priority: str = "routine"
    status: str = "active"
    referral_date: str = ""
    notes: str = ""


class HealthCertificateService:
    def __init__(self) -> None:
        self._certificates: dict[str, list[HealthCertificate]] = {}

    def issue_certificate(
        self,
        citizen_id: str,
        certificate_type: CertificateType,
        issuer: str,
        valid_for_days: int = 365,
        metadata: dict[str, Any] | None = None,
    ) -> HealthCertificate:
        from datetime import timedelta
        now = datetime.now(UTC)
        cert = HealthCertificate(
            id=str(uuid.uuid4()),
            citizen_id=citizen_id,
            certificate_type=certificate_type,
            certificate_number=f"CERT-{uuid.uuid4().hex[:8].upper()}",
            issuer=issuer,
            issued_at=now.isoformat(),
            valid_from=now.isoformat(),
            valid_until=(now + timedelta(days=valid_for_days)).isoformat(),
            status="active",
            metadata=metadata or {},
        )
        if citizen_id not in self._certificates:
            self._certificates[citizen_id] = []
        self._certificates[citizen_id].append(cert)
        return cert

    def revoke_certificate(self, citizen_id: str, certificate_id: str) -> bool:
        certificates = self._certificates.get(citizen_id, [])
        for c in certificates:
            if c.id == certificate_id and c.status == "active":
                c.status = "revoked"
                return True
        return False

    def get_certificates(
        self,
        citizen_id: str,
        certificate_type: CertificateType | None = None,
        status: str | None = None,
    ) -> list[HealthCertificate]:
        certificates = self._certificates.get(citizen_id, [])
        if certificate_type:
            certificates = [c for c in certificates if c.certificate_type == certificate_type]
        if status:
            certificates = [c for c in certificates if c.status == status]
        certificates.sort(key=lambda c: c.issued_at, reverse=True)
        return certificates

    def verify_certificate(self, certificate_number: str) -> dict[str, Any]:
        for certificates in self._certificates.values():
            for c in certificates:
                if c.certificate_number == certificate_number:
                    now = datetime.now(UTC).isoformat()
                    return {
                        "valid": c.status == "active" and c.valid_until >= now,
                        "certificate_type": c.certificate_type.value,
                        "issued_at": c.issued_at,
                        "valid_until": c.valid_until,
                        "issuer": c.issuer,
                        "status": c.status,
                    }
        return {"valid": False, "reason": "certificate_not_found"}


class MedicalLeaveService:
    def __init__(self) -> None:
        self._leaves: dict[str, list[MedicalLeaveDocument]] = {}

    def issue_leave(
        self,
        citizen_id: str,
        diagnosis: str,
        from_date: str,
        to_date: str,
        issued_by: str,
        issued_by_name: str = "",
        facility_name: str = "",
        notes: str = "",
    ) -> MedicalLeaveDocument:
        from datetime import date
        try:
            f = date.fromisoformat(from_date)
            t = date.fromisoformat(to_date)
            total_days = (t - f).days
        except (ValueError, TypeError):
            total_days = 0
        leave = MedicalLeaveDocument(
            id=str(uuid.uuid4()),
            citizen_id=citizen_id,
            leave_number=f"LVE-{uuid.uuid4().hex[:8].upper()}",
            diagnosis=diagnosis,
            from_date=from_date,
            to_date=to_date,
            total_days=max(total_days, 1),
            issued_by=issued_by,
            issued_by_name=issued_by_name,
            facility_name=facility_name,
            status="active",
            notes=notes,
        )
        if citizen_id not in self._leaves:
            self._leaves[citizen_id] = []
        self._leaves[citizen_id].append(leave)
        return leave

    def get_leave_history(self, citizen_id: str) -> list[MedicalLeaveDocument]:
        leaves = self._leaves.get(citizen_id, [])
        leaves.sort(key=lambda leaf: leaf.from_date, reverse=True)
        return leaves

    def verify_leave(self, leave_number: str) -> dict[str, Any]:
        for leaves in self._leaves.values():
            for leaf in leaves:
                if leaf.leave_number == leave_number:
                    return {
                        "valid": leaf.status == "active",
                        "citizen_id": leaf.citizen_id,
                        "from_date": leaf.from_date,
                        "to_date": leaf.to_date,
                        "total_days": leaf.total_days,
                        "issued_by": leaf.issued_by_name or leaf.issued_by,
                        "diagnosis": leaf.diagnosis,
                    }
        return {"valid": False, "reason": "leave_not_found"}


class ReferralService:
    def __init__(self) -> None:
        self._referrals: dict[str, list[Referral]] = {}

    def create_referral(
        self,
        citizen_id: str,
        from_facility: str,
        to_facility: str,
        from_practitioner: str = "",
        to_practitioner: str = "",
        reason: str = "",
        priority: str = "routine",
        notes: str = "",
    ) -> Referral:
        referral = Referral(
            id=str(uuid.uuid4()),
            citizen_id=citizen_id,
            from_facility=from_facility,
            to_facility=to_facility,
            from_practitioner=from_practitioner,
            to_practitioner=to_practitioner,
            reason=reason,
            priority=priority,
            status="active",
            referral_date=datetime.now(UTC).isoformat(),
            notes=notes,
        )
        if citizen_id not in self._referrals:
            self._referrals[citizen_id] = []
        self._referrals[citizen_id].append(referral)
        return referral

    def get_referrals(self, citizen_id: str, status: str | None = None) -> list[Referral]:
        referrals = self._referrals.get(citizen_id, [])
        if status:
            referrals = [r for r in referrals if r.status == status]
        referrals.sort(key=lambda r: r.referral_date, reverse=True)
        return referrals

    def update_referral_status(self, referral_id: str, status: str) -> bool:
        for referrals in self._referrals.values():
            for r in referrals:
                if r.id == referral_id:
                    r.status = status
                    return True
        return False


class InsuranceInfoService:
    def __init__(self) -> None:
        self._insurance: dict[str, list[dict[str, Any]]] = {}

    def add_insurance(
        self,
        citizen_id: str,
        provider: str,
        policy_number: str,
        coverage_type: str = "public",
        valid_from: str = "",
        valid_until: str = "",
    ) -> dict[str, Any]:
        policy = {
            "id": str(uuid.uuid4()),
            "citizen_id": citizen_id,
            "provider": provider,
            "policy_number": policy_number,
            "coverage_type": coverage_type,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "status": "active",
            "added_at": datetime.now(UTC).isoformat(),
        }
        if citizen_id not in self._insurance:
            self._insurance[citizen_id] = []
        self._insurance[citizen_id].append(policy)
        return policy

    def get_insurance_policies(self, citizen_id: str) -> list[dict[str, Any]]:
        policies = self._insurance.get(citizen_id, [])
        now = datetime.now(UTC).isoformat()
        for p in policies:
            if p["status"] == "active" and p.get("valid_until") and p["valid_until"] < now:
                p["status"] = "expired"
        return policies

    def get_active_coverage(self, citizen_id: str) -> list[dict[str, Any]]:
        policies = self.get_insurance_policies(citizen_id)
        return [p for p in policies if p["status"] == "active"]
