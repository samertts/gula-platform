from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.identity.base import IdentityBaseEntity


class MachineIdentity(IdentityBaseEntity):
    __tablename__ = "niam_machine_identities"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    machine_name = Column(String(200), nullable=False)
    machine_type = Column(String(50), nullable=False)
    serial_number = Column(String(100), unique=True, nullable=True)

    ip_address = Column(String(45), nullable=True)
    mac_address = Column(String(17), unique=True, nullable=True)
    hostname = Column(String(255), nullable=True)

    os = Column(String(100), nullable=True)
    os_version = Column(String(50), nullable=True)
    agent_version = Column(String(30), nullable=True)

    public_key = Column(Text, nullable=True)
    certificate_sn = Column(String(100), unique=True, nullable=True)
    certificate = Column(Text, nullable=True)
    certificate_expires = Column(DateTime(timezone=True), nullable=True)

    assigned_to_person = Column(String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    location = Column(String(200), nullable=True)

    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_compromised = Column(Boolean, default=False, nullable=False)
    compromised_at = Column(DateTime(timezone=True), nullable=True)

    notes = Column(Text, nullable=True)

    iot_device_type = Column(String(100), nullable=True)
    robot_type = Column(String(100), nullable=True)
    ai_agent_id = Column(String(100), nullable=True)
    device_attestation = Column(Text, nullable=True)
    attested_at = Column(DateTime(timezone=True), nullable=True)
    health_status = Column(String(20), default="unknown", nullable=False)
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    firmware_version = Column(String(50), nullable=True)
    analyzer_type = Column(String(100), nullable=True)
    risk_score = Column(Integer, nullable=True)
