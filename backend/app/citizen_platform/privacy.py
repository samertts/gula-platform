from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from app._compat import UTC

logger = logging.getLogger("gula.citizen.privacy")


@dataclass
class ConsentRecord:
    id: str = ""
    citizen_id: str = ""
    scope: str = ""
    granted_to: str = ""
    granted_to_name: str = ""
    status: str = "active"
    granted_at: str = ""
    expires_at: str = ""
    revoked_at: str = ""
    revocation_reason: str = ""
    purpose: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessLogEntry:
    id: str = ""
    citizen_id: str = ""
    accessed_by: str = ""
    accessed_by_name: str = ""
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    ip_address: str = ""
    user_agent: str = ""
    purpose: str = ""
    accessed_at: str = ""
    is_emergency: bool = False
    emergency_reason: str = ""


class ConsentEngine:
    def __init__(self) -> None:
        self._consents: dict[str, list[ConsentRecord]] = {}

    def grant_consent(
        self,
        citizen_id: str,
        scope: str,
        granted_to: str,
        granted_to_name: str = "",
        purpose: str = "",
        expires_in_days: int | None = None,
    ) -> ConsentRecord:
        record = ConsentRecord(
            id=str(uuid.uuid4()),
            citizen_id=citizen_id,
            scope=scope,
            granted_to=granted_to,
            granted_to_name=granted_to_name,
            status="active",
            granted_at=datetime.now(UTC).isoformat(),
            purpose=purpose,
        )
        if expires_in_days:
            record.expires_at = (
                datetime.now(UTC) + timedelta(days=expires_in_days)
            ).isoformat()
        if citizen_id not in self._consents:
            self._consents[citizen_id] = []
        self._consents[citizen_id].append(record)
        return record

    def revoke_consent(
        self, citizen_id: str, consent_id: str, reason: str = "",
    ) -> bool:
        consents = self._consents.get(citizen_id, [])
        for c in consents:
            if c.id == consent_id and c.status == "active":
                c.status = "revoked"
                c.revoked_at = datetime.now(UTC).isoformat()
                c.revocation_reason = reason
                return True
        return False

    def check_consent(
        self, citizen_id: str, scope: str, granted_to: str,
    ) -> bool:
        consents = self._consents.get(citizen_id, [])
        now = datetime.now(UTC).isoformat()
        for c in consents:
            if (
                c.scope == scope
                and c.granted_to == granted_to
                and c.status == "active"
            ):
                if c.expires_at and c.expires_at < now:
                    c.status = "expired"
                    return False
                return True
        return False

    def get_active_consents(self, citizen_id: str) -> list[ConsentRecord]:
        consents = self._consents.get(citizen_id, [])
        now = datetime.now(UTC).isoformat()
        active = []
        for c in consents:
            if c.status == "active":
                if c.expires_at and c.expires_at < now:
                    c.status = "expired"
                else:
                    active.append(c)
        return active

    def get_consent_history(self, citizen_id: str) -> list[ConsentRecord]:
        return self._consents.get(citizen_id, [])


class PrivacyDashboard:
    def __init__(self, consent_engine: ConsentEngine) -> None:
        self._consent_engine = consent_engine

    def get_privacy_summary(self, citizen_id: str) -> dict[str, Any]:
        consents = self._consent_engine.get_consent_history(citizen_id)
        active = [c for c in consents if c.status == "active"]
        return {
            "total_consents": len(consents),
            "active_consents": len(active),
            "revoked_consents": sum(1 for c in consents if c.status == "revoked"),
            "expired_consents": sum(1 for c in consents if c.status == "expired"),
            "consent_scopes": list({c.scope for c in active}),
            "data_shared_with": list({c.granted_to_name or c.granted_to for c in active}),
        }

    def get_recent_access_activity(
        self, access_logs: list[AccessLogEntry], limit: int = 20,
    ) -> list[AccessLogEntry]:
        access_logs.sort(key=lambda a: a.accessed_at, reverse=True)
        return access_logs[:limit]


class AccessLogs:
    def __init__(self) -> None:
        self._logs: dict[str, list[AccessLogEntry]] = {}

    def log_access(
        self,
        citizen_id: str,
        accessed_by: str,
        action: str,
        resource_type: str,
        resource_id: str = "",
        ip_address: str = "",
        user_agent: str = "",
        purpose: str = "",
        is_emergency: bool = False,
        emergency_reason: str = "",
    ) -> AccessLogEntry:
        entry = AccessLogEntry(
            id=str(uuid.uuid4()),
            citizen_id=citizen_id,
            accessed_by=accessed_by,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            purpose=purpose,
            accessed_at=datetime.now(UTC).isoformat(),
            is_emergency=is_emergency,
            emergency_reason=emergency_reason,
        )
        if citizen_id not in self._logs:
            self._logs[citizen_id] = []
        self._logs[citizen_id].append(entry)
        return entry

    def get_access_logs(
        self,
        citizen_id: str,
        from_date: str | None = None,
        to_date: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> list[AccessLogEntry]:
        logs = self._logs.get(citizen_id, [])
        if from_date:
            logs = [l for l in logs if l.accessed_at >= from_date]
        if to_date:
            logs = [l for l in logs if l.accessed_at <= to_date]
        if action:
            logs = [l for l in logs if l.action == action]
        logs.sort(key=lambda l: l.accessed_at, reverse=True)
        return logs[:limit]

    def get_emergency_access_logs(self, citizen_id: str) -> list[AccessLogEntry]:
        return [l for l in self._logs.get(citizen_id, []) if l.is_emergency]


class DataSharingControls:
    def __init__(self, consent_engine: ConsentEngine) -> None:
        self._consent_engine = consent_engine
        self._sharing_rules: dict[str, list[dict[str, Any]]] = {}

    def add_sharing_rule(
        self,
        citizen_id: str,
        partner: str,
        data_categories: list[str],
        purpose: str = "",
        expires_in_days: int | None = None,
    ) -> dict[str, Any]:
        consent = self._consent_engine.grant_consent(
            citizen_id=citizen_id,
            scope="data_sharing",
            granted_to=partner,
            purpose=purpose,
            expires_in_days=expires_in_days,
        )
        rule = {
            "id": consent.id,
            "partner": partner,
            "data_categories": data_categories,
            "purpose": purpose,
            "status": "active",
            "created_at": consent.granted_at,
            "expires_at": consent.expires_at,
        }
        if citizen_id not in self._sharing_rules:
            self._sharing_rules[citizen_id] = []
        self._sharing_rules[citizen_id].append(rule)
        return rule

    def remove_sharing_rule(self, citizen_id: str, rule_id: str) -> bool:
        return self._consent_engine.revoke_consent(
            citizen_id, rule_id, reason="Removed by user",
        )

    def get_active_sharing_rules(self, citizen_id: str) -> list[dict[str, Any]]:
        return self._sharing_rules.get(citizen_id, [])

    def get_shared_partners(self, citizen_id: str) -> list[str]:
        return list(
            {r["partner"] for r in self._sharing_rules.get(citizen_id, []) if r["status"] == "active"},
        )


class EmergencyBreakGlass:
    def __init__(self, access_logs: AccessLogs) -> None:
        self._access_logs = access_logs
        self._break_glass_events: list[dict[str, Any]] = []

    def activate(
        self,
        citizen_id: str,
        accessed_by: str,
        reason: str,
        resources_accessed: list[str] | None = None,
        ip_address: str = "",
    ) -> dict[str, Any]:
        event = {
            "id": str(uuid.uuid4()),
            "citizen_id": citizen_id,
            "accessed_by": accessed_by,
            "reason": reason,
            "resources_accessed": resources_accessed or [],
            "activated_at": datetime.now(UTC).isoformat(),
            "status": "active",
        }
        self._break_glass_events.append(event)
        self._access_logs.log_access(
            citizen_id=citizen_id,
            accessed_by=accessed_by,
            action="break_glass_activated",
            resource_type="emergency_access",
            ip_address=ip_address,
            is_emergency=True,
            emergency_reason=reason,
        )
        return event

    def deactivate(self, event_id: str) -> bool:
        for event in self._break_glass_events:
            if event["id"] == event_id and event["status"] == "active":
                event["status"] = "deactivated"
                event["deactivated_at"] = datetime.now(UTC).isoformat()
                return True
        return False

    def get_active_events(self, citizen_id: str) -> list[dict[str, Any]]:
        return [
            e
            for e in self._break_glass_events
            if e["citizen_id"] == citizen_id and e["status"] == "active"
        ]

    def get_break_glass_history(
        self, citizen_id: str | None = None,
    ) -> list[dict[str, Any]]:
        if citizen_id:
            return [
                e for e in self._break_glass_events if e["citizen_id"] == citizen_id
            ]
        return self._break_glass_events
