from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.base import _ulid
from app.identity.models.security import IncidentSeverity, IncidentStatus, SecurityIncident
from app.identity.services.canonical_audit import AuditEventInput, CanonicalAuditService


class IncidentError(ValueError):
    pass


class IncidentAccessDenied(PermissionError):
    pass


class IncidentService:
    TRANSITIONS: dict[str, frozenset[str]] = {
        IncidentStatus.open.value: frozenset({IncidentStatus.triaged.value, IncidentStatus.false_positive.value}),
        IncidentStatus.triaged.value: frozenset({IncidentStatus.contained.value, IncidentStatus.investigating.value, IncidentStatus.false_positive.value}),
        IncidentStatus.contained.value: frozenset({IncidentStatus.investigating.value, IncidentStatus.resolved.value}),
        IncidentStatus.investigating.value: frozenset({IncidentStatus.contained.value, IncidentStatus.resolved.value}),
        IncidentStatus.resolved.value: frozenset({IncidentStatus.closed.value, IncidentStatus.investigating.value}),
        IncidentStatus.closed.value: frozenset(),
        IncidentStatus.false_positive.value: frozenset(),
    }

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit = CanonicalAuditService(session)

    async def create(
        self,
        *,
        actor_id: str,
        severity: str,
        category: str,
        organization_id: str | None,
        affected_scope: dict[str, Any] | None = None,
    ) -> SecurityIncident:
        if severity not in {item.value for item in IncidentSeverity}:
            raise IncidentError("invalid incident severity")
        if not category or len(category) > 80:
            raise IncidentError("incident category is required")
        incident = SecurityIncident(
            uuid=_ulid(),
            incident_key=f"INC-{_ulid()}",
            severity=severity,
            category=category,
            organization_id=organization_id,
            status=IncidentStatus.open.value,
            reported_at=datetime.now(UTC),
            affected_scope=affected_scope or {},
            created_by=actor_id,
            is_active=True,
        )
        self.session.add(incident)
        await self.session.flush()
        await self.audit.record(
            AuditEventInput(
                event_type="SECURITY_INCIDENT_CREATED",
                category="SECURITY",
                action="incident.create",
                actor_id=actor_id,
                organization_id=organization_id,
                target_type="security_incident",
                target_id=incident.id,
                decision="ALLOW",
                reason_code="INCIDENT_REPORTED",
                data_classification="CONFIDENTIAL",
                metadata={"severity": severity, "category": category},
            ),
        )
        return incident

    async def transition(
        self,
        *,
        actor_id: str,
        incident_id: str,
        target_status: str,
        expected_version: int,
        resolution: str | None = None,
        containment_status: str | None = None,
    ) -> SecurityIncident:
        if target_status not in {item.value for item in IncidentStatus}:
            raise IncidentError("invalid incident status")
        incident = await self.session.get(SecurityIncident, incident_id, with_for_update=True)
        if incident is None:
            raise IncidentError("incident not found")
        if incident.version != expected_version:
            raise IncidentError("stale incident version")
        if target_status not in self.TRANSITIONS.get(incident.status, frozenset()):
            raise IncidentError(f"invalid transition {incident.status} -> {target_status}")
        incident.status = target_status
        incident.version += 1
        if containment_status is not None:
            incident.containment_status = containment_status[:120]
        if resolution is not None:
            incident.resolution = resolution[:4000]
        if target_status in {IncidentStatus.closed.value, IncidentStatus.false_positive.value}:
            incident.closed_at = datetime.now(UTC)
        await self.session.flush()
        await self.audit.record(
            AuditEventInput(
                event_type="SECURITY_INCIDENT_STATUS_CHANGED",
                category="SECURITY",
                action="incident.transition",
                actor_id=actor_id,
                organization_id=incident.organization_id,
                target_type="security_incident",
                target_id=incident.id,
                decision="ALLOW",
                reason_code="STATE_MACHINE_TRANSITION",
                data_classification="CONFIDENTIAL",
                changes={"status": target_status, "version": incident.version},
            ),
        )
        return incident

    async def list(self, *, organization_id: str | None, limit: int = 100, offset: int = 0) -> list[SecurityIncident]:
        conditions = []
        if organization_id is not None:
            conditions.append(SecurityIncident.organization_id == organization_id)
        result = await self.session.execute(
            select(SecurityIncident)
            .where(*conditions)
            .order_by(SecurityIncident.detected_at.desc())
            .offset(max(offset, 0))
            .limit(min(max(limit, 1), 100)),
        )
        return list(result.scalars().all())
