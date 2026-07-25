from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import re
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from pydantic import BaseModel

from security.modules.audit.immutable import ImmutableAuditLog
from security.modules.audit.models import AuditEvent, AuditPolicy

logger = logging.getLogger(__name__)


class AuditQuery(BaseModel):
    actor_id: str | None = None
    actor_type: str | None = None
    action: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    outcome: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    limit: int = 1000
    offset: int = 0


class AuditService:
    def __init__(self, policy: AuditPolicy | None = None, storage_path: str | None = None):
        self.policy = policy or AuditPolicy()
        self.immutable_log = ImmutableAuditLog(storage_path=storage_path)
        self._in_memory_events: list[AuditEvent] = []
        self._alert_rules: list[dict[str, Any]] = []

    def create_event(self, event: AuditEvent) -> AuditEvent:
        if not event.event_id:
            event.event_id = str(uuid4())
        if not event.timestamp:
            event.timestamp = datetime.now(UTC)

        previous_hash = ""
        if self._in_memory_events:
            previous_hash = self._in_memory_events[-1].hash
        elif hasattr(self.immutable_log, "current_hash") and self.immutable_log.current_hash:
            previous_hash = self.immutable_log.current_hash

        event.previous_hash = previous_hash
        event.hash = self._compute_hash(event)

        self._in_memory_events.append(event)

        if self.policy.immutable_storage:
            self.immutable_log.append(event)

        if self._should_alert(event):
            self._trigger_alert(event)

        return event

    def _compute_hash(self, event: AuditEvent) -> str:
        content = f"{event.event_id}:{event.timestamp.isoformat()}:{event.actor_id}:{event.action}:{event.resource_id}:{event.outcome}:{event.previous_hash}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _should_alert(self, event: AuditEvent) -> bool:
        for alert_action in self.policy.alert_on:
            if event.action.startswith(alert_action):
                return True
        return False

    def _trigger_alert(self, event: AuditEvent) -> None:
        logger.warning(f"Audit alert triggered by event: {event.action} by {event.actor_id} on {event.resource_id}")
        for rule in self._alert_rules:
            try:
                if re.search(rule.get("pattern", ""), event.action):
                    rule.get("callback", lambda e: None)(event)
            except Exception as e:
                logger.error(f"Alert rule callback failed: {e}")

    def query_events(self, query: AuditQuery) -> list[AuditEvent]:
        results = list(self._in_memory_events)

        if query.actor_id:
            results = [e for e in results if e.actor_id == query.actor_id]
        if query.actor_type:
            results = [e for e in results if e.actor_type == query.actor_type]
        if query.action:
            results = [e for e in results if e.action == query.action]
        if query.resource_type:
            results = [e for e in results if e.resource_type == query.resource_type]
        if query.resource_id:
            results = [e for e in results if e.resource_id == query.resource_id]
        if query.outcome:
            results = [e for e in results if e.outcome == query.outcome]
        if query.start_time:
            results = [e for e in results if e.timestamp >= query.start_time]
        if query.end_time:
            results = [e for e in results if e.timestamp <= query.end_time]

        results.sort(key=lambda e: e.timestamp, reverse=True)
        results = results[query.offset:query.offset + query.limit]

        return results

    def verify_log_integrity(self) -> dict[str, Any]:
        if not self._in_memory_events:
            return {"valid": True, "checked": 0, "message": "No events to verify"}

        violations: list[str] = []
        for i in range(1, len(self._in_memory_events)):
            expected_prev_hash = self._in_memory_events[i - 1].hash
            actual_prev_hash = self._in_memory_events[i].previous_hash
            if expected_prev_hash != actual_prev_hash:
                violations.append(
                    f"Chain break at index {i}: event {self._in_memory_events[i].event_id} "
                    f"has previous_hash {actual_prev_hash} but expected {expected_prev_hash}"
                )

        for event in self._in_memory_events:
            computed = self._compute_hash(event)
            if computed != event.hash:
                violations.append(f"Hash mismatch for event {event.event_id}: stored {event.hash}, computed {computed}")

        return {
            "valid": len(violations) == 0,
            "checked": len(self._in_memory_events),
            "violations": violations,
        }

    def enforce_retention(self) -> dict[str, Any]:
        cutoff = datetime.now(UTC) - timedelta(days=self.policy.retention_days)
        before_count = len(self._in_memory_events)

        self._in_memory_events = [e for e in self._in_memory_events if e.timestamp > cutoff]
        archived = before_count - len(self._in_memory_events)

        logger.info(f"Retention enforcement: archived {archived} events older than {self.policy.retention_days} days")
        return {"archived": archived, "remaining": len(self._in_memory_events)}

    def export_events(self, format: str = "json") -> str:
        events = self._in_memory_events

        if format == "json":
            return json.dumps(
                [e.model_dump(mode="json") for e in events],
                indent=2, default=str,
            )

        if format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["event_id", "timestamp", "actor_id", "actor_type", "action",
                            "resource_type", "resource_id", "outcome", "source_ip", "hash"])
            for e in events:
                writer.writerow([
                    e.event_id, e.timestamp.isoformat(), e.actor_id, e.actor_type, e.action,
                    e.resource_type, e.resource_id, e.outcome, e.source_ip, e.hash,
                ])
            return output.getvalue()

        if format == "fhir":
            fhir_entries = []
            for e in events:
                fhir_entries.append({
                    "resourceType": "AuditEvent",
                    "id": e.event_id,
                    "recorded": e.timestamp.isoformat(),
                    "type": {"code": e.action},
                    "subtype": [{"code": e.resource_type}],
                    "agent": [{"who": {"identifier": {"value": e.actor_id}}}],
                    "entity": [{"what": {"identifier": {"value": e.resource_id}}}],
                    "outcome": e.outcome,
                    "source": {"observer": {"display": "GULA Audit Service"}},
                })
            return json.dumps(fhir_entries, indent=2, default=str)

        if format == "syslog":
            lines = []
            for e in events:
                lines.append(
                    f"<13>1 {e.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')} gula-audit "
                    f"AuditService - - [event@{e.event_id} "
                    f'actor="{e.actor_id}" action="{e.action}" '
                    f'resource="{e.resource_id}" outcome="{e.outcome}"]'
                )
            return "\n".join(lines)

        raise ValueError(f"Unsupported export format: {format}")

    def add_alert_rule(self, pattern: str, callback: Any) -> None:
        self._alert_rules.append({"pattern": pattern, "callback": callback})

    def get_statistics(self) -> dict[str, Any]:
        events = self._in_memory_events
        if not events:
            return {"total": 0, "by_action": {}, "by_outcome": {}, "by_actor": {}}

        action_counts: dict[str, int] = {}
        outcome_counts: dict[str, int] = {}
        actor_counts: dict[str, int] = {}

        for e in events:
            action_counts[e.action] = action_counts.get(e.action, 0) + 1
            outcome_counts[e.outcome] = outcome_counts.get(e.outcome, 0) + 1
            actor_counts[e.actor_id] = actor_counts.get(e.actor_id, 0) + 1

        return {
            "total": len(events),
            "by_action": action_counts,
            "by_outcome": outcome_counts,
            "by_actor": dict(sorted(actor_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
        }
