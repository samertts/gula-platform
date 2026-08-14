from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text

from app._compat import UTC
from app.identity.base import IdentityBaseEntity


class IncidentSeverity(StrEnum):
    p0 = "P0"
    p1 = "P1"
    p2 = "P2"
    p3 = "P3"


class IncidentStatus(StrEnum):
    open = "OPEN"
    triaged = "TRIAGED"
    contained = "CONTAINED"
    investigating = "INVESTIGATING"
    resolved = "RESOLVED"
    closed = "CLOSED"
    false_positive = "FALSE_POSITIVE"


class SecurityIncident(IdentityBaseEntity):
    __tablename__ = "niam_security_incidents"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    incident_key = Column(String(80), unique=True, nullable=False, index=True)
    severity = Column(String(4), nullable=False, index=True)
    category = Column(String(80), nullable=False, index=True)
    organization_id = Column(String(26), nullable=True, index=True)
    status = Column(String(20), nullable=False, default=IncidentStatus.open.value, index=True)
    detected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True)
    reported_at = Column(DateTime(timezone=True), nullable=True)
    assigned_to = Column(String(26), nullable=True, index=True)
    affected_scope = Column(JSON, nullable=True)
    containment_status = Column(String(30), nullable=True)
    resolution = Column(Text, nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(26), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")

    def is_closed(self) -> bool:
        return self.status in {IncidentStatus.closed.value, IncidentStatus.false_positive.value}
