from __future__ import annotations

import csv
import hashlib
import hmac
import json
import logging
import threading
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from security.modules.fhir.models import ClinicalAuditEvent

logger = logging.getLogger("gula.security.modules.fhir.audit")

_CHAIN_ANCHOR_KEY = b"gula-audit-chain-anchor-2024"
_DEFAULT_RETENTION_DAYS = 3650


class ClinicalAuditor:
    def __init__(self, chain_anchor_key: str = "", retention_days: int = _DEFAULT_RETENTION_DAYS) -> None:
        self._lock = threading.Lock()
        self._events: list[dict[str, Any]] = []
        self._chain: list[dict[str, Any]] = []
        self._chain_anchor_key = (chain_anchor_key or _CHAIN_ANCHOR_KEY.decode()).encode()
        self._retention_days = retention_days
        self._last_hash = self._compute_anchor_hash()
        self._alert_callbacks: list[Callable[[ClinicalAuditEvent], None]] = []

        try:
            from backend.app.services.audit_service import log_action as _backend_log
            self._backend_log = _backend_log
        except ImportError:
            self._backend_log = None

    def _compute_anchor_hash(self) -> str:
        anchor = hmac.new(
            self._chain_anchor_key,
            b"GULA_AUDIT_CHAIN_ANCHOR",
            hashlib.sha256,
        ).hexdigest()
        return anchor

    def _compute_hash(self, previous_hash: str, event_data: dict[str, Any]) -> str:
        serialized = json.dumps(event_data, sort_keys=True, default=str).encode()
        content = (previous_hash + serialized.hex()).encode()
        return hashlib.sha256(content).hexdigest()

    def log_event(
        self,
        user_id: str,
        action: str,
        resource_type: str = "",
        resource_id: str = "",
        patient_id: str = "",
        outcome: str = "success",
        outcome_desc: str = "",
        details: dict[str, Any] | None = None,
    ) -> ClinicalAuditEvent:
        event_id = str(uuid4())
        timestamp = datetime.now(UTC)

        event_data: dict[str, Any] = {
            "event_id": event_id,
            "user_id": user_id,
            "patient_id": patient_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "outcome": outcome,
            "outcome_desc": outcome_desc,
            "timestamp": timestamp.isoformat(),
            "details": details or {},
        }

        with self._lock:
            self._last_hash = self._compute_hash(self._last_hash, event_data)
            event_data["chain_hash"] = self._last_hash
            self._events.append(event_data)

            chain_entry = {
                "hash": self._last_hash,
                "previous_hash": self._events[-2]["chain_hash"] if len(self._events) > 1 else self._compute_anchor_hash(),
                "event_id": event_id,
                "timestamp": timestamp.isoformat(),
            }
            self._chain.append(chain_entry)

        event = ClinicalAuditEvent(
            event_id=event_id,
            user_id=user_id,
            patient_id=patient_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=outcome,
            outcome_desc=outcome_desc,
            timestamp=timestamp,
            signature=self._last_hash,
            details=details or {},
        )

        if self._backend_log:
            try:
                self._backend_log(
                    db=None,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    user_id=user_id,
                    user_role="",
                    details=f"{action} on {resource_type}:{resource_id}",
                )
            except Exception as exc:
                logger.warning("Backend audit log failed: %s", exc)

        if outcome == "failure" or outcome_desc:
            self._check_alert(event)

        logger.debug("Audit event logged: %s %s/%s by %s", action, resource_type, resource_id, user_id)
        return event

    def verify_chain(self) -> dict[str, Any]:
        with self._lock:
            if not self._events:
                return {"valid": True, "message": "No events to verify"}

            expected_hash = self._compute_anchor_hash()
            for i, event in enumerate(self._events):
                event_data = {k: v for k, v in event.items() if k != "chain_hash"}
                computed = self._compute_hash(expected_hash, event_data)
                stored = event.get("chain_hash", "")

                if computed != stored:
                    return {
                        "valid": False,
                        "message": f"Chain integrity violation at event {i} ({event['event_id'][:16]})",
                        "index": i,
                        "expected_hash": computed,
                        "stored_hash": stored,
                    }
                expected_hash = stored

        return {"valid": True, "message": f"Chain verified: {len(self._events)} events intact"}

    def query_events(
        self,
        user_id: str | None = None,
        patient_id: str | None = None,
        resource_type: str | None = None,
        action: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ClinicalAuditEvent]:
        filtered = list(self._events)

        if user_id:
            filtered = [e for e in filtered if e.get("user_id") == user_id]
        if patient_id:
            filtered = [e for e in filtered if e.get("patient_id") == patient_id]
        if resource_type:
            filtered = [e for e in filtered if e.get("resource_type") == resource_type]
        if action:
            filtered = [e for e in filtered if e.get("action") == action]
        if start_time:
            filtered = [e for e in filtered if e.get("timestamp", "") >= start_time.isoformat()]
        if end_time:
            filtered = [e for e in filtered if e.get("timestamp", "") <= end_time.isoformat()]

        filtered = filtered[offset:offset + limit]

        return [
            ClinicalAuditEvent(
                event_id=e["event_id"],
                user_id=e["user_id"],
                patient_id=e.get("patient_id", ""),
                resource_type=e.get("resource_type", ""),
                resource_id=e.get("resource_id", ""),
                action=e.get("action", ""),
                outcome=e.get("outcome", "success"),
                outcome_desc=e.get("outcome_desc", ""),
                timestamp=datetime.fromisoformat(e["timestamp"]) if isinstance(e.get("timestamp"), str) else datetime.now(UTC),
                signature=e.get("chain_hash", ""),
                details=e.get("details", {}),
            )
            for e in filtered
        ]

    def export_events(
        self,
        fmt: str = "json",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> str:
        events = self._events
        if start_time:
            events = [e for e in events if e.get("timestamp", "") >= start_time.isoformat()]
        if end_time:
            events = [e for e in events if e.get("timestamp", "") <= end_time.isoformat()]

        if fmt == "json":
            return json.dumps(events, indent=2, default=str)
        if fmt == "fhir":
            bundle: dict[str, Any] = {
                "resourceType": "Bundle",
                "type": "collection",
                "entry": [
                    {
                        "resource": {
                            "resourceType": "AuditEvent",
                            "id": e["event_id"],
                            "recorded": e["timestamp"],
                            "type": {"code": e.get("action", "unknown")},
                            "outcome": e.get("outcome", "success"),
                            "agent": [{"who": {"identifier": {"value": e["user_id"]}}}],
                            "entity": [{
                                "what": {
                                    "identifier": {"value": e.get("resource_id", "")},
                                    "type": e.get("resource_type", ""),
                                },
                            }],
                        },
                    }
                    for e in events
                ],
            }
            return json.dumps(bundle, indent=2, default=str)
        if fmt == "csv":
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["event_id", "user_id", "patient_id", "resource_type", "resource_id", "action", "outcome", "timestamp", "chain_hash"])
            for e in events:
                writer.writerow([
                    e["event_id"], e["user_id"], e.get("patient_id", ""),
                    e.get("resource_type", ""), e.get("resource_id", ""),
                    e.get("action", ""), e.get("outcome", ""),
                    e.get("timestamp", ""), e.get("chain_hash", ""),
                ])
            return output.getvalue()

        return json.dumps(events, indent=2, default=str)

    def enforce_retention(self) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=self._retention_days)
        cutoff_str = cutoff.isoformat()
        count = 0

        with self._lock:
            before = len(self._events)
            self._events = [
                e for e in self._events
                if e.get("timestamp", "") >= cutoff_str
            ]
            self._chain = self._chain[:len(self._events)]
            count = before - len(self._events)

        if count > 0:
            self._last_hash = self._compute_anchor_hash()
            for event in self._events:
                event_without_hash = {k: v for k, v in event.items() if k != "chain_hash"}
                self._last_hash = self._compute_hash(self._last_hash, event_without_hash)
                event["chain_hash"] = self._last_hash

        return count

    def add_alert_callback(self, callback: Callable[[ClinicalAuditEvent], None]) -> None:
        self._alert_callbacks.append(callback)

    def _check_alert(self, event_data: dict[str, Any]) -> None:
        event = ClinicalAuditEvent(
            event_id=event_data["event_id"],
            user_id=event_data["user_id"],
            patient_id=event_data.get("patient_id", ""),
            resource_type=event_data.get("resource_type", ""),
            resource_id=event_data.get("resource_id", ""),
            action=event_data.get("action", ""),
            outcome=event_data.get("outcome", "success"),
            outcome_desc=event_data.get("outcome_desc", ""),
            timestamp=datetime.fromisoformat(event_data["timestamp"]) if isinstance(event_data.get("timestamp"), str) else datetime.now(UTC),
            signature=event_data.get("chain_hash", ""),
            details=event_data.get("details", {}),
        )

        suspicious_actions = {"delete", "purge", "anonymize", "export_bulk", "permission_change"}
        if event.action in suspicious_actions:
            for cb in self._alert_callbacks:
                try:
                    cb(event)
                except Exception as exc:
                    logger.warning("Alert callback error: %s", exc)

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            total = len(self._events)
            actions: dict[str, int] = {}
            outcomes: dict[str, int] = {}
            for e in self._events:
                act = e.get("action", "unknown")
                actions[act] = actions.get(act, 0) + 1
                out = e.get("outcome", "unknown")
                outcomes[out] = outcomes.get(out, 0) + 1

        return {
            "total_events": total,
            "actions": actions,
            "outcomes": outcomes,
            "retention_days": self._retention_days,
            "chain_integrity": self.verify_chain().get("valid", False),
        }
