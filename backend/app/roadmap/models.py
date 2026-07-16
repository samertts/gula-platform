from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app._compat import UTC, StrEnum

from ..database import Base


class ProgramStatus(StrEnum):
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class MissionStatus(StrEnum):
    PLANNING = "PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


class EpicStatus(StrEnum):
    BACKLOG = "BACKLOG"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    DONE = "DONE"


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    BLOCKED = "BLOCKED"


class Priority(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Program(Base):
    __tablename__ = "roadmap_programs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), default=ProgramStatus.PLANNING, nullable=False, index=True)
    version = Column(String(20), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    target_date = Column(DateTime(timezone=True), nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    owner = Column(String(200), nullable=True)
    budget = Column(String(100), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    missions = relationship("Mission", back_populates="program", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Program(id={self.id}, code='{self.code}', status='{self.status}')>"


class Mission(Base):
    __tablename__ = "roadmap_missions"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("roadmap_programs.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), default=MissionStatus.PLANNING, nullable=False, index=True)
    priority = Column(String(20), default=Priority.MEDIUM, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=True)
    target_date = Column(DateTime(timezone=True), nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    owner = Column(String(200), nullable=True)
    risk_level = Column(String(20), default=RiskLevel.LOW, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    program = relationship("Program", back_populates="missions")
    epics = relationship("Epic", back_populates="mission", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="mission", cascade="all, delete-orphan")
    risks = relationship("Risk", back_populates="mission", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Mission(id={self.id}, code='{self.code}', status='{self.status}')>"


class Epic(Base):
    __tablename__ = "roadmap_epics"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("roadmap_missions.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), default=EpicStatus.BACKLOG, nullable=False, index=True)
    priority = Column(String(20), default=Priority.MEDIUM, nullable=False)
    story_points = Column(Integer, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    mission = relationship("Mission", back_populates="epics")
    tasks = relationship("RoadmapTask", back_populates="epic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Epic(id={self.id}, code='{self.code}', status='{self.status}')>"


class RoadmapTask(Base):
    __tablename__ = "roadmap_tasks"

    id = Column(Integer, primary_key=True, index=True)
    epic_id = Column(Integer, ForeignKey("roadmap_epics.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default=TaskStatus.TODO, nullable=False, index=True)
    priority = Column(String(20), default=Priority.MEDIUM, nullable=False)
    assignee = Column(String(200), nullable=True)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    dependencies = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    epic = relationship("Epic", back_populates="tasks")

    def __repr__(self):
        return f"<RoadmapTask(id={self.id}, name='{self.name}', status='{self.status}')>"


class Milestone(Base):
    __tablename__ = "roadmap_milestones"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("roadmap_missions.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    target_date = Column(DateTime(timezone=True), nullable=False)
    achieved_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="PENDING", nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    mission = relationship("Mission", back_populates="milestones")

    def __repr__(self):
        return f"<Milestone(id={self.id}, name='{self.name}', status='{self.status}')>"


class Risk(Base):
    __tablename__ = "roadmap_risks"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("roadmap_missions.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    risk_level = Column(String(20), default=RiskLevel.MEDIUM, nullable=False)
    probability = Column(Float, nullable=True)
    impact = Column(Float, nullable=True)
    mitigation = Column(Text, nullable=True)
    status = Column(String(20), default="OPEN", nullable=False)
    owner = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    mission = relationship("Mission", back_populates="risks")

    def __repr__(self):
        return f"<Risk(id={self.id}, risk_level='{self.risk_level}', status='{self.status}')>"


class TechnicalDebt(Base):
    __tablename__ = "roadmap_technical_debt"

    id = Column(Integer, primary_key=True, index=True)
    component = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    severity = Column(String(20), default=Priority.MEDIUM, nullable=False)
    estimated_effort_hours = Column(Float, nullable=True)
    status = Column(String(20), default="IDENTIFIED", nullable=False)
    identified_by = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<TechnicalDebt(id={self.id}, component='{self.component}', severity='{self.severity}')>"


class ArchitectureDecision(Base):
    __tablename__ = "roadmap_architecture_decisions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    context = Column(Text, nullable=False)
    decision = Column(Text, nullable=False)
    consequences = Column(Text, nullable=True)
    status = Column(String(20), default="PROPOSED", nullable=False)
    domain = Column(String(100), nullable=True, index=True)
    created_by = Column(String(200), nullable=True)
    approved_by = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    superseded_by = Column(Integer, ForeignKey("roadmap_architecture_decisions.id", ondelete="SET NULL"), nullable=True)

    superseding = relationship("ArchitectureDecision", remote_side="ArchitectureDecision.id", backref="superseded")

    def __repr__(self):
        return f"<ArchitectureDecision(id={self.id}, title='{self.title}', status='{self.status}')>"
