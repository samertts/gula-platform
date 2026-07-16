from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text

from app.national.base import TenantEntity


class EmergencyDeclarationModel(TenantEntity):
    __tablename__ = "cc_emergency_declarations"

    emergency_type = Column(String(50), nullable=False)
    level = Column(String(50), default="level_1_minor")
    status = Column(String(50), default="standby")
    region = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    affected_population = Column(Integer, default=0)
    declared_by = Column(String(200), nullable=True)
    declared_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(200), nullable=True)
    activation_protocol = Column(String(200), nullable=True)
    ic_name = Column(String(200), nullable=True)
    ic_title = Column(String(200), nullable=True)
    ic_phone = Column(String(50), nullable=True)
    command_post_location = Column(Text, nullable=True)
    operational_period = Column(String(50), default="continuous")
    objectives = Column(JSON, nullable=True)
    situation_summary = Column(Text, nullable=True)


class ResourceRequestModel(TenantEntity):
    __tablename__ = "cc_resource_requests"

    emergency_id = Column(String(100), ForeignKey("cc_emergency_declarations.id"), nullable=True, index=True)
    resource_type = Column(String(50), nullable=False)
    quantity = Column(Integer, default=1)
    priority = Column(String(50), default="medium")
    status = Column(String(50), default="pending")
    requesting_facility = Column(String(200), nullable=True)
    destination_location = Column(Text, nullable=True)
    requested_by = Column(String(200), nullable=True)
    requested_at = Column(DateTime(timezone=True), nullable=False)
    fulfilled_quantity = Column(Integer, default=0)
    fulfilled_by = Column(String(200), nullable=True)
    fulfilled_at = Column(DateTime(timezone=True), nullable=True)
    source = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)


class SituationReportModel(TenantEntity):
    __tablename__ = "cc_situation_reports"

    emergency_id = Column(String(100), ForeignKey("cc_emergency_declarations.id"), nullable=True, index=True)
    report_number = Column(Integer, default=1)
    operational_period = Column(String(50), nullable=True)
    summary = Column(Text, nullable=True)
    key_actions = Column(JSON, nullable=True)
    resources_deployed = Column(JSON, nullable=True)
    casualties = Column(JSON, nullable=True)
    challenges = Column(JSON, nullable=True)
    next_steps = Column(JSON, nullable=True)
    published_by = Column(String(200), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=False)


class AfterActionReportModel(TenantEntity):
    __tablename__ = "cc_after_action_reports"

    emergency_id = Column(String(100), ForeignKey("cc_emergency_declarations.id"), nullable=True)
    emergency_type = Column(String(50), nullable=True)
    region = Column(String(100), nullable=True)
    incident_duration_hours = Column(Integer, default=0)
    overall_rating = Column(String(50), default="satisfactory")
    strengths = Column(JSON, nullable=True)
    weaknesses = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    response_time_minutes = Column(Integer, default=0)
    lives_saved = Column(Integer, default=0)
    resources_used = Column(JSON, nullable=True)
    completed_by = Column(String(200), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
