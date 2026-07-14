from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from ..enums import (
    CertificateStatus,
    DataClassificationLevel,
    IncidentStatus,
    SecurityPolicyCategory,
    ThreatSeverity,
)
from ..models.security import (
    BreakGlassPolicy,
    DataClassification,
    DigitalCertificate,
    IncidentRecord,
    NationalAuditEvent,
    RiskRegistryItem,
    SecurityPolicy,
    ThreatIntelligenceEvent,
)


class SecurityGovernanceService:
    def __init__(self, db: Session):
        self.db = db

    def create_security_policy(
        self,
        policy_code: str,
        title_ar: str,
        category: SecurityPolicyCategory,
        content_ar: str,
        title_en: str | None = None,
        content_en: str | None = None,
        effective_date: date | None = None,
        review_date: date | None = None,
        approved_by: str | None = None,
    ) -> SecurityPolicy:
        policy = SecurityPolicy(
            policy_code=policy_code,
            title_ar=title_ar,
            title_en=title_en,
            category=category,
            content_ar=content_ar,
            content_en=content_en,
            status="active",
            effective_date=effective_date or date.today(),
            review_date=review_date,
            approved_by=approved_by,
        )
        self.db.add(policy)
        return policy

    def create_break_glass_policy(
        self,
        policy_code: str,
        title_ar: str,
        allowed_reasons: list[str],
        auto_approve_roles: list[str] | None = None,
        require_approval_roles: list[str] | None = None,
        max_duration_minutes: int = 120,
        notify_roles: list[str] | None = None,
    ) -> BreakGlassPolicy:
        policy = BreakGlassPolicy(
            policy_code=policy_code,
            title_ar=title_ar,
            allowed_reasons=allowed_reasons,
            auto_approve_roles=auto_approve_roles or [],
            require_approval_roles=require_approval_roles or [],
            max_duration_minutes=max_duration_minutes,
            notify_roles=notify_roles or [],
        )
        self.db.add(policy)
        return policy

    def log_audit_event(
        self,
        event_type: str,
        actor_id: str | None = None,
        actor_role: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        action: str | None = None,
        status: str = "success",
        ip_address: str | None = None,
        details: dict[str, Any] | None = None,
        severity: ThreatSeverity = ThreatSeverity.LOW,
        node_id: int | None = None,
    ) -> NationalAuditEvent:
        event = NationalAuditEvent(
            event_type=event_type,
            severity=severity,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action or event_type,
            status=status,
            ip_address=ip_address,
            details=details,
            node_id=node_id,
        )
        self.db.add(event)
        return event

    def report_threat(
        self,
        threat_id: str,
        title: str,
        severity: ThreatSeverity,
        description: str | None = None,
        source: str | None = None,
        affected_systems: list[str] | None = None,
        indicators: list[str] | None = None,
        mitre_attack_id: str | None = None,
    ) -> ThreatIntelligenceEvent:
        threat = ThreatIntelligenceEvent(
            threat_id=threat_id,
            title=title,
            description=description,
            severity=severity,
            source=source,
            affected_systems=affected_systems,
            indicators=indicators,
            mitre_attack_id=mitre_attack_id,
            detected_at=datetime.now(UTC),
        )
        self.db.add(threat)
        return threat

    def create_incident(
        self,
        incident_id: str,
        title: str,
        severity: ThreatSeverity,
        category: str,
        description: str | None = None,
        affected_node_id: int | None = None,
        assigned_to: str | None = None,
    ) -> IncidentRecord:
        incident = IncidentRecord(
            incident_id=incident_id,
            title=title,
            description=description,
            severity=severity,
            status=IncidentStatus.DETECTED,
            category=category,
            affected_node_id=affected_node_id,
            detected_at=datetime.now(UTC),
            assigned_to=assigned_to,
        )
        self.db.add(incident)
        return incident

    def update_incident_status(
        self, incident_id: str, status: IncidentStatus, resolution: str | None = None
    ) -> IncidentRecord | None:
        incident = (
            self.db.query(IncidentRecord)
            .filter(IncidentRecord.incident_id == incident_id)
            .first()
        )
        if not incident:
            return None
        incident.status = status
        if status == IncidentStatus.CONTAINING:
            incident.contained_at = datetime.now(UTC)
        if status == IncidentStatus.RESOLVED:
            incident.resolved_at = datetime.now(UTC)
        if resolution:
            incident.resolution = resolution
        return incident

    def register_risk(
        self,
        risk_id: str,
        title_ar: str,
        category: str,
        likelihood: int,
        impact: int,
        owner: str | None = None,
        mitigation: str | None = None,
        contingency: str | None = None,
    ) -> RiskRegistryItem:
        item = RiskRegistryItem(
            risk_id=risk_id,
            title_ar=title_ar,
            category=category,
            likelihood=likelihood,
            impact=impact,
            risk_score=likelihood * impact,
            owner=owner,
            mitigation=mitigation,
            contingency=contingency,
        )
        self.db.add(item)
        return item

    def classify_data(
        self,
        data_type: str,
        name_ar: str,
        classification_level: DataClassificationLevel,
        encryption_required: bool = True,
        pii: bool = False,
        phi: bool = False,
        retention_days: int | None = None,
        access_roles: list[str] | None = None,
    ) -> DataClassification:
        classification = DataClassification(
            data_type=data_type,
            name_ar=name_ar,
            classification_level=classification_level,
            encryption_required=encryption_required,
            pii=pii,
            phi=phi,
            retention_days=retention_days,
            access_roles=access_roles,
        )
        self.db.add(classification)
        return classification

    def register_certificate(
        self,
        certificate_id: str,
        common_name: str,
        issuer: str,
        type_val: str,
        issued_date: date,
        expiry_date: date,
        serial_number: str | None = None,
        owner: str | None = None,
    ) -> DigitalCertificate:
        cert = DigitalCertificate(
            certificate_id=certificate_id,
            common_name=common_name,
            issuer=issuer,
            serial_number=serial_number,
            status=CertificateStatus.ACTIVE,
            type=type_val,
            issued_date=issued_date,
            expiry_date=expiry_date,
            owner=owner,
        )
        self.db.add(cert)
        return cert

    def revoke_certificate(
        self, certificate_id: str, reason: str | None = None
    ) -> DigitalCertificate | None:
        cert = (
            self.db.query(DigitalCertificate)
            .filter(DigitalCertificate.certificate_id == certificate_id)
            .first()
        )
        if not cert:
            return None
        cert.status = CertificateStatus.REVOKED
        cert.revocation_date = date.today()
        cert.revocation_reason = reason
        return cert
