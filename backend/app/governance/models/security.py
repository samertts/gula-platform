from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app._compat import UTC

from ..base import GovernanceBaseEntity
from ..enums import (
    CertificateStatus,
    DataClassificationLevel,
    IncidentStatus,
    SecurityPolicyCategory,
    ThreatSeverity,
)


class NationalAuditEvent(GovernanceBaseEntity):
    __tablename__ = "gov_national_audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(Enum(ThreatSeverity), nullable=False, default=ThreatSeverity.LOW)
    source = Column(String(200), nullable=True)
    actor_id = Column(String(100), nullable=True, index=True)
    actor_role = Column(String(100), nullable=True)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="success")
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    details = Column(JSON, nullable=True)
    node_id = Column(Integer, ForeignKey("gov_hierarchy_nodes.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)


class SecurityPolicy(GovernanceBaseEntity):
    __tablename__ = "gov_security_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_code = Column(String(50), unique=True, nullable=False, index=True)
    title_ar = Column(String(300), nullable=False)
    title_en = Column(String(300), nullable=True)
    category = Column(Enum(SecurityPolicyCategory), nullable=False, index=True)
    version = Column(String(20), nullable=False, default="1.0")
    content_ar = Column(Text, nullable=False)
    content_en = Column(Text, nullable=True)
    status = Column(String(20), default="active", index=True)
    effective_date = Column(Date, nullable=True)
    review_date = Column(Date, nullable=True)
    approved_by = Column(String(200), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class BreakGlassPolicy(GovernanceBaseEntity):
    __tablename__ = "gov_break_glass_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_code = Column(String(50), unique=True, nullable=False, index=True)
    title_ar = Column(String(300), nullable=False)
    title_en = Column(String(300), nullable=True)
    allowed_reasons = Column(JSON, nullable=False)
    auto_approve_roles = Column(JSON, nullable=True)
    require_approval_roles = Column(JSON, nullable=True)
    max_duration_minutes = Column(Integer, nullable=False, default=120)
    notify_roles = Column(JSON, nullable=True)
    audit_required = Column(Boolean, default=True)
    require_justification = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class ThreatIntelligenceEvent(GovernanceBaseEntity):
    __tablename__ = "gov_threat_intel"

    id = Column(Integer, primary_key=True, autoincrement=True)
    threat_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(Enum(ThreatSeverity), nullable=False, index=True)
    source = Column(String(200), nullable=True)
    affected_systems = Column(JSON, nullable=True)
    indicators = Column(JSON, nullable=True)
    mitre_attack_id = Column(String(50), nullable=True)
    detected_at = Column(DateTime(timezone=True), nullable=False)
    mitigated_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="open", index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class IncidentRecord(GovernanceBaseEntity):
    __tablename__ = "gov_incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(Enum(ThreatSeverity), nullable=False, index=True)
    status = Column(
        Enum(IncidentStatus), nullable=False, default=IncidentStatus.DETECTED, index=True
    )
    category = Column(String(100), nullable=False)
    affected_node_id = Column(Integer, ForeignKey("gov_hierarchy_nodes.id"), nullable=True)
    detected_at = Column(DateTime(timezone=True), nullable=False)
    contained_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    assigned_to = Column(String(200), nullable=True)
    resolution = Column(Text, nullable=True)
    lessons_learned = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class RiskRegistryItem(GovernanceBaseEntity):
    __tablename__ = "gov_risk_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    risk_id = Column(String(100), unique=True, nullable=False, index=True)
    title_ar = Column(String(300), nullable=False)
    title_en = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    likelihood = Column(Integer, nullable=False)
    impact = Column(Integer, nullable=False)
    risk_score = Column(Integer, nullable=False)
    owner = Column(String(200), nullable=True)
    mitigation = Column(Text, nullable=True)
    contingency = Column(Text, nullable=True)
    status = Column(String(20), default="open", index=True)
    target_date = Column(Date, nullable=True)
    review_date = Column(Date, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class DataClassification(GovernanceBaseEntity):
    __tablename__ = "gov_data_classification"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_type = Column(String(100), unique=True, nullable=False, index=True)
    name_ar = Column(String(300), nullable=False)
    name_en = Column(String(300), nullable=True)
    classification_level = Column(Enum(DataClassificationLevel), nullable=False, index=True)
    description = Column(Text, nullable=True)
    encryption_required = Column(Boolean, default=True)
    retention_days = Column(Integer, nullable=True)
    pii = Column(Boolean, default=False, index=True)
    phi = Column(Boolean, default=False, index=True)
    access_roles = Column(JSON, nullable=True)
    sharing_allowed = Column(Boolean, default=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class DigitalCertificate(GovernanceBaseEntity):
    __tablename__ = "gov_digital_certificates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    certificate_id = Column(String(100), unique=True, nullable=False, index=True)
    common_name = Column(String(300), nullable=False)
    issuer = Column(String(300), nullable=False)
    serial_number = Column(String(200), nullable=True, index=True)
    status = Column(
        Enum(CertificateStatus), nullable=False, default=CertificateStatus.PENDING, index=True
    )
    type = Column(String(50), nullable=False)
    issued_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    revocation_date = Column(Date, nullable=True)
    revocation_reason = Column(String(200), nullable=True)
    owner = Column(String(200), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
