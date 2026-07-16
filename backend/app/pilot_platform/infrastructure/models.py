from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, String, Text

from app.national.base import TenantEntity


class PilotProgramModel(TenantEntity):
    __tablename__ = "pilot_programs"

    module_name = Column(String(200), nullable=False)
    module_path = Column(String(200), nullable=True)
    version = Column(String(50), nullable=False)
    current_phase = Column(String(50), default="planned")
    status = Column(String(50), default="planned")
    strategy = Column(String(50), default="canary")
    pilot_lead = Column(String(200), nullable=True)
    technical_lead = Column(String(200), nullable=True)
    clinical_lead = Column(String(200), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    target_completion = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    description = Column(Text, nullable=True)
    phases = Column(JSON, nullable=True)
    facilities = Column(JSON, nullable=True)


class PilotFacilityModel(TenantEntity):
    __tablename__ = "pilot_facilities"

    pilot_id = Column(String(100), ForeignKey("pilot_programs.id"), nullable=False, index=True)
    facility_id = Column(String(100), nullable=False)
    facility_name = Column(String(200), nullable=True)
    phase = Column(String(50), nullable=True)
    readiness_level = Column(String(50), default="not_ready")
    readiness_score = Column(Float, default=0.0)
    enrolled_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    go_no_go_approved = Column(Boolean, default=False)
    issues = Column(JSON, nullable=True)


class ReadinessChecklistModel(TenantEntity):
    __tablename__ = "pilot_readiness_checklists"

    pilot_id = Column(String(100), ForeignKey("pilot_programs.id"), nullable=True)
    facility_id = Column(String(100), nullable=True)
    items = Column(JSON, nullable=True)
    overall_score = Column(Float, default=0.0)
    level = Column(String(50), default="not_ready")
    assessed_by = Column(String(200), nullable=True)
    assessed_at = Column(DateTime(timezone=True), nullable=True)


class GoNoGoGateModel(TenantEntity):
    __tablename__ = "pilot_go_no_go_gates"

    pilot_id = Column(String(100), ForeignKey("pilot_programs.id"), nullable=False, index=True)
    facility_id = Column(String(100), nullable=True)
    gate_name = Column(String(100), nullable=False)
    result = Column(String(50), default="not_run")
    certification_level = Column(String(50), nullable=True)
    metrics = Column(JSON, nullable=True)
    approver = Column(String(200), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    comments = Column(Text, nullable=True)


class DeploymentRecordModel(TenantEntity):
    __tablename__ = "pilot_deployment_records"

    pilot_id = Column(String(100), ForeignKey("pilot_programs.id"), nullable=False, index=True)
    module = Column(String(200), nullable=True)
    version = Column(String(50), nullable=True)
    facility_id = Column(String(100), nullable=True)
    strategy = Column(String(50), nullable=True)
    status = Column(String(50), default="pending")
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    deployed_by = Column(String(200), nullable=True)
    health_check_passed = Column(Boolean, default=False)
    rollback_at = Column(DateTime(timezone=True), nullable=True)
    rollback_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
