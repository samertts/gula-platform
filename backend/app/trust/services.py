"""Trust platform business logic services."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.trust.enums import (
    ComplianceStatus,
    ConsentPurpose,
    ConsentStatus,
    DataCategory,
    SovereigntyLevel,
    TrustServiceType,
)
from app.trust.models import (
    ComplianceCheck,
    ComplianceEvidence,
    ConsentRecord,
    SovereigntyRule,
    TrustServiceLog,
)


class ConsentService:
    """Manages patient consent records and verification."""

    def __init__(self, db: Session):
        self.db = db

    def create_consent(
        self,
        patient_id: int,
        lab_id: int,
        purpose: ConsentPurpose,
        data_categories: list[DataCategory],
        guardian_id: int | None = None,
        expires_in_days: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ConsentRecord:
        purpose_str = purpose.value if isinstance(purpose, ConsentPurpose) else purpose
        categories_str = ",".join(c.value if isinstance(c, DataCategory) else c for c in data_categories)
        consent_data = f"{patient_id}:{lab_id}:{purpose_str}:{categories_str}:{int(time.time())}"
        consent_hash = hashlib.sha256(consent_data.encode()).hexdigest()

        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)

        record = ConsentRecord(
            patient_id=patient_id,
            lab_id=lab_id,
            purpose=purpose if isinstance(purpose, ConsentPurpose) else ConsentPurpose(purpose),
            status=ConsentStatus.GRANTED,
            granted_at=datetime.now(UTC),
            expires_at=expires_at,
            data_categories=categories_str,
            guardian_id=guardian_id,
            consent_hash=consent_hash,
            consent_version="1.0",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(record)
        self.db.flush()
        return record

    def verify_consent(
        self,
        patient_id: int,
        lab_id: int,
        purpose: ConsentPurpose,
        data_category: DataCategory | None = None,
    ) -> bool:
        query = self.db.query(ConsentRecord).filter(
            ConsentRecord.patient_id == patient_id,
            ConsentRecord.lab_id == lab_id,
            ConsentRecord.purpose == purpose,
            ConsentRecord.status == ConsentStatus.GRANTED,
            ConsentRecord.is_deleted.is_(None),
        )
        if data_category:
            query = query.filter(ConsentRecord.data_categories.contains(data_category.value))

        record = query.first()
        if not record:
            return False
        if record.expires_at and record.expires_at < datetime.now(UTC):
            record.status = ConsentStatus.EXPIRED
            self.db.flush()
            return False
        return True

    def withdraw_consent(self, consent_id: int, user_id: int) -> ConsentRecord | None:
        record = self.db.query(ConsentRecord).filter(
            ConsentRecord.id == consent_id,
            ConsentRecord.is_deleted.is_(None),
        ).first()
        if record:
            record.status = ConsentStatus.WITHDRAWN
            record.withdrawn_at = datetime.now(UTC)
            self.db.flush()
        return record

    def get_patient_consents(self, patient_id: int) -> list[ConsentRecord]:
        return self.db.query(ConsentRecord).filter(
            ConsentRecord.patient_id == patient_id,
            ConsentRecord.is_deleted.is_(None),
        ).all()

    def get_access_history(self, patient_id: int, limit: int = 50) -> list[dict[str, Any]]:
        from app.models.audit_log import AuditLog
        logs = self.db.query(AuditLog).filter(
            AuditLog.patient_id == patient_id,
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
        return [log.to_dict() for log in logs]


class SovereigntyService:
    """Manages data sovereignty and residency rules."""

    def __init__(self, db: Session):
        self.db = db

    def get_rule(self, data_category: DataCategory) -> SovereigntyRule | None:
        return self.db.query(SovereigntyRule).filter(
            SovereigntyRule.data_category == data_category,
            SovereigntyRule.is_deleted.is_(None),
        ).first()

    def validate_cross_border(self, data_category: DataCategory, destination: str) -> bool:
        rule = self.get_rule(data_category)
        if not rule:
            return False
        if rule.sovereignty_level == SovereigntyLevel.NATIONAL_ONLY:
            return destination == "IRQ"
        if rule.allows_cross_border:
            return True
        return destination == "IRQ"

    def requires_encryption(self, data_category: DataCategory) -> bool:
        rule = self.get_rule(data_category)
        if rule:
            return bool(rule.requires_encryption)
        return True

    def get_all_rules(self) -> list[SovereigntyRule]:
        return self.db.query(SovereigntyRule).filter(
            SovereigntyRule.is_deleted.is_(None),
        ).all()


class TrustService:
    """Trust services: digital signature, timestamping, evidence preservation."""

    def __init__(self, db: Session):
        self.db = db

    def sign_document(
        self,
        document_hash: str,
        user_id: int,
        lab_id: int,
        metadata: dict[str, Any] | None = None,
    ) -> TrustServiceLog:
        signature_data = f"{document_hash}:{user_id}:{lab_id}:{int(time.time())}"
        signature_value = hmac.new(
            key=b"gula-trust-signature-v1",
            msg=signature_data.encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()

        log = TrustServiceLog(
            service_type=TrustServiceType.DIGITAL_SIGNATURE,
            request_id=hashlib.md5(f"{document_hash}:{time.time()}".encode()).hexdigest(),
            user_id=user_id,
            lab_id=lab_id,
            document_hash=document_hash,
            signature_value=signature_value,
            status="completed",
            result_hash=hashlib.sha256(signature_value.encode()).hexdigest(),
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        self.db.add(log)
        self.db.flush()
        return log

    def timestamp_document(
        self,
        document_hash: str,
        user_id: int,
        lab_id: int,
    ) -> TrustServiceLog:
        now = datetime.now(UTC)
        timestamp_data = f"{document_hash}:{now.isoformat()}:{user_id}"
        timestamp_token = hashlib.sha256(timestamp_data.encode()).hexdigest()

        log = TrustServiceLog(
            service_type=TrustServiceType.TIMESTAMPING,
            request_id=hashlib.md5(f"ts:{document_hash}:{time.time()}".encode()).hexdigest(),
            user_id=user_id,
            lab_id=lab_id,
            document_hash=document_hash,
            timestamp_token=f"v1:{now.isoformat()}:{timestamp_token}",
            status="completed",
            result_hash=timestamp_token,
        )
        self.db.add(log)
        self.db.flush()
        return log

    def verify_document_integrity(self, document_hash: str) -> dict[str, Any]:
        logs = self.db.query(TrustServiceLog).filter(
            TrustServiceLog.document_hash == document_hash,
            TrustServiceLog.is_deleted.is_(None),
        ).order_by(TrustServiceLog.created_at.desc()).all()

        return {
            "document_hash": document_hash,
            "verified": len(logs) > 0,
            "signatures": [
                {
                    "id": l.id,
                    "type": l.service_type.value,
                    "timestamp": l.created_at.isoformat(),
                    "signature": l.signature_value[:16] + "..." if l.signature_value else None,
                }
                for l in logs
            ],
            "total_records": len(logs),
        }


class ComplianceService:
    """Compliance checking and evidence management."""

    def __init__(self, db: Session):
        self.db = db

    def run_compliance_check(
        self,
        check_type: str,
        check_name: str,
        target_id: str | None = None,
        target_type: str | None = None,
    ) -> ComplianceCheck:
        from app.core.policy_engine import check_policy_compliance
        is_compliant = check_policy_compliance(check_type, target_id)
        score = 100 if is_compliant else 0

        check = ComplianceCheck(
            check_type=check_type,
            check_name=check_name,
            target_id=target_id,
            target_type=target_type,
            result=ComplianceStatus.COMPLIANT if is_compliant else ComplianceStatus.NON_COMPLIANT,
            score=score,
            details=json.dumps({"automated_check": True, "check_type": check_type}),
            checked_at=datetime.now(UTC),
            next_check_at=datetime.now(UTC) + timedelta(days=30),
        )
        self.db.add(check)
        self.db.flush()
        return check

    def add_evidence(
        self,
        evidence_type: str,
        source: str,
        evidence_data: str,
        collected_by: int | None = None,
    ) -> ComplianceEvidence:
        evidence_id = hashlib.sha256(
            f"{evidence_type}:{source}:{int(time.time())}".encode()
        ).hexdigest()[:32]
        evidence_hash = hashlib.sha256(evidence_data.encode()).hexdigest()

        evidence = ComplianceEvidence(
            evidence_type=evidence_type,
            evidence_id=evidence_id,
            source=source,
            collected_at=datetime.now(UTC),
            collected_by=collected_by,
            status=ComplianceStatus.PENDING_REVIEW,
            evidence_hash=evidence_hash,
            evidence_data=evidence_data,
            retention_until=datetime.now(UTC) + timedelta(days=365 * 7),
        )
        self.db.add(evidence)
        self.db.flush()
        return evidence

    def get_compliance_dashboard(self, lab_id: int | None = None) -> dict[str, Any]:
        query = self.db.query(ComplianceCheck)
        if lab_id:
            query = query.filter(ComplianceCheck.target_id == str(lab_id))

        checks = query.order_by(ComplianceCheck.checked_at.desc()).limit(100).all()
        total = len(checks)
        compliant = sum(1 for c in checks if c.result == ComplianceStatus.COMPLIANT)
        non_compliant = sum(1 for c in checks if c.result == ComplianceStatus.NON_COMPLIANT)

        return {
            "total_checks": total,
            "compliant": compliant,
            "non_compliant": non_compliant,
            "score": round((compliant / total * 100), 1) if total > 0 else 0,
            "recent_checks": [
                {
                    "id": c.id,
                    "type": c.check_type,
                    "name": c.check_name,
                    "result": c.result.value,
                    "score": c.score,
                    "timestamp": c.checked_at.isoformat(),
                }
                for c in checks[:20]
            ],
        }
