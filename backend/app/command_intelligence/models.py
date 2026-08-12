from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app._compat import UTC, StrEnum

from ..database import Base


class SituationRoomStatus(StrEnum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"


class SituationRoom(Base):
    __tablename__ = "situation_rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False, default=SituationRoomStatus.GREEN, index=True)
    metrics = Column(JSON, default=dict)
    alerts = Column(JSON, default=list)
    region = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class NationalKPI(Base):
    __tablename__ = "national_kpis"

    id = Column(Integer, primary_key=True, index=True)
    kpi_name = Column(String(200), nullable=False, index=True)
    kpi_category = Column(String(100), nullable=False, index=True)
    kpi_value = Column(Float, nullable=False)
    target_value = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    region = Column(String(100), nullable=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True, index=True)
    measured_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    lab = relationship("Lab")


class IncidentIntelligence(Base):
    __tablename__ = "incident_intelligence"

    id = Column(Integer, primary_key=True, index=True)
    incident_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    affected_entities = Column(JSON, default=list)
    root_cause = Column(Text, nullable=True)
    impact_analysis = Column(JSON, default=dict)
    recommendation = Column(JSON, default=dict)
    status = Column(String(20), nullable=False, default="active", index=True)
    detected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class CapacityIntelligence(Base):
    __tablename__ = "capacity_intelligence"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False, index=True)
    metric = Column(String(200), nullable=False)
    current_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=True)
    trend = Column(String(20), nullable=True)
    forecast = Column(JSON, default=dict)
    recommendation = Column(Text, nullable=True)
    generated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_type = Column(String(100), nullable=False, index=True)
    priority = Column(Integer, nullable=False, default=0)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    expected_impact = Column(JSON, default=dict)
    risk_assessment = Column(JSON, default=dict)
    status = Column(String(20), nullable=False, default="pending", index=True)
    created_by = Column(
        Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True,
    )
    reviewed_by = Column(
        Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True,
    )
    implemented_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    creator = relationship("LabUser", foreign_keys=[created_by])
    reviewer = relationship("LabUser", foreign_keys=[reviewed_by])
