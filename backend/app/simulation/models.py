from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app._compat import UTC, StrEnum

from ..database import Base


class TwinType(StrEnum):
    HOSPITAL = "hospital"
    LABORATORY = "laboratory"
    DIRECTORATE = "directorate"
    NATIONAL_HEALTH = "national_health"


class SimulationStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DigitalTwin(Base):
    __tablename__ = "digital_twins"

    id = Column(Integer, primary_key=True, index=True)
    twin_type = Column(Enum(TwinType), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False)
    entity_type = Column(String(100), nullable=False)
    name = Column(String(200), nullable=False)
    config = Column(JSON, nullable=True, default=dict)
    state = Column(JSON, nullable=True, default=dict)
    metrics = Column(JSON, nullable=True, default=dict)
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    simulations = relationship(
        "Simulation",
        back_populates="twin",
        cascade="all, delete-orphan",
    )


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)
    twin_id = Column(
        Integer,
        ForeignKey("digital_twins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(200), nullable=False)
    simulation_type = Column(String(100), nullable=False, index=True)
    parameters = Column(JSON, nullable=True, default=dict)
    status = Column(Enum(SimulationStatus), default=SimulationStatus.PENDING, index=True)
    result = Column(JSON, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    triggered_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    twin = relationship("DigitalTwin", back_populates="simulations")
    snapshots = relationship(
        "SimulationSnapshot",
        back_populates="simulation",
        cascade="all, delete-orphan",
    )


class SimulationSnapshot(Base):
    __tablename__ = "simulation_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(
        Integer,
        ForeignKey("simulations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    state_snapshot = Column(JSON, nullable=True)
    metrics_snapshot = Column(JSON, nullable=True)

    simulation = relationship("Simulation", back_populates="snapshots")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    twin_id = Column(
        Integer,
        ForeignKey("digital_twins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prediction_type = Column(String(100), nullable=False, index=True)
    target_date = Column(DateTime(timezone=True), nullable=False)
    predicted_value = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    model_name = Column(String(100), nullable=True)
    features_used = Column(JSON, nullable=True)
    actual_value = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    twin = relationship("DigitalTwin")


class CapacityPlan(Base):
    __tablename__ = "capacity_plans"

    id = Column(Integer, primary_key=True, index=True)
    twin_id = Column(
        Integer,
        ForeignKey("digital_twins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_date = Column(DateTime(timezone=True), nullable=False)
    metric = Column(String(100), nullable=False)
    predicted_demand = Column(Float, nullable=True)
    current_capacity = Column(Float, nullable=True)
    recommended_capacity = Column(Float, nullable=True)
    priority = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    twin = relationship("DigitalTwin")
