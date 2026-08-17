"""Durable EHR connector state and synchronization records.

The connector remains disabled unless its contract, endpoint, trust material, and
human approval are all present. Secrets are never stored in this model.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, UniqueConstraint

from app._compat import UTC
from ..database import Base


class EHRConnectorConfig(Base):
    __tablename__ = "ehr_connector_configs"
    __table_args__ = (UniqueConstraint("lab_id", "connector_name", name="uq_ehr_connector_lab_name"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)
    connector_name = Column(String(80), nullable=False, default="ehr")
    protocol = Column(String(20), nullable=False, default="fhir_r4")
    endpoint = Column(String(500), nullable=False)
    contract_version = Column(String(80), nullable=False)
    trust_material_ref = Column(String(200), nullable=True)
    enabled = Column(Boolean, nullable=False, default=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String(160), nullable=True)
    last_health_status = Column(String(30), nullable=False, default="unverified")
    last_health_checked_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class EHRSyncRecord(Base):
    __tablename__ = "ehr_sync_records"
    __table_args__ = (UniqueConstraint("lab_id", "idempotency_key", name="uq_ehr_sync_lab_idempotency"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String(120), nullable=False, index=True)
    entity_type = Column(String(80), nullable=False)
    entity_id = Column(String(160), nullable=False, index=True)
    idempotency_key = Column(String(200), nullable=False)
    status = Column(String(30), nullable=False, default="queued", index=True)
    outbox_event_id = Column(Integer, nullable=True, index=True)
    external_id = Column(String(200), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
