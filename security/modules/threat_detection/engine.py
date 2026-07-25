from __future__ import annotations

import logging
import re
import statistics
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from security.modules.threat_detection.models import DetectionRule, ThreatEvent

logger = logging.getLogger(__name__)

MITRE_ATTACK_MAPPING: dict[str, str] = {
    "brute_force": "T1110",
    "credential_access": "T1003",
    "exploit_public_facing": "T1190",
    "phishing": "T1566",
    "valid_accounts": "T1078",
    "privilege_escalation": "T1068",
    "lateral_movement": "T1021",
    "exfiltration": "T1048",
    "command_and_control": "T1071",
    "defense_evasion": "T1562",
    "discovery": "T1087",
    "collection": "T1005",
    "impact": "T1485",
    "initial_access": "T1091",
    "persistence": "T1098",
    "execution": "T1204",
    "data_destruction": "T1485",
    "injection": "T1055",
    "privileged_access": "T1078",
    "resource_development": "T1583",
}


class CorrelationRule(BaseModel):
    name: str
    description: str
    severity: str
    conditions: dict[str, Any] = Field(default_factory=dict)
    window_seconds: int = 300


class DetectionResult(BaseModel):
    alert_id: str
    rule_id: str
    severity: str
    title: str
    description: str
    mitre_id: str | None = None
    events: list[ThreatEvent] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    response_actions: list[str] = Field(default_factory=list)


class ThreatDetectionEngine:
    def __init__(self):
        self._rules: list[DetectionRule] = []
        self._correlation_rules: list[CorrelationRule] = []
        self._event_buffer: dict[str, list[ThreatEvent]] = defaultdict(list)
        self._alerts: list[DetectionResult] = []
        self._response_handlers: dict[str, list[Callable]] = defaultdict(list)
        self._anomaly_baselines: dict[str, dict[str, float]] = {}

        self._initialize_default_rules()

    def _initialize_default_rules(self) -> None:
        default_rules = [
            DetectionRule(
                rule_id="BRUTE-FORCE-001",
                name="Multiple Authentication Failures",
                description="Detects multiple failed authentication attempts from same source",
                severity="HIGH",
                mitre_mapping="T1110",
                detection_logic={"type": "threshold", "field": "source_ip", "count": 5, "window_seconds": 300},
                response_actions=["rate_limit_source", "notify_security_team"],
            ),
            DetectionRule(
                rule_id="PERMISSION-DENY-001",
                name="Elevated Permission Denial Rate",
                description="Detects unusual number of permission denied events",
                severity="MEDIUM",
                mitre_mapping="T1562",
                detection_logic={"type": "threshold", "field": "action", "value": "authorization.deny", "count": 10, "window_seconds": 600},
                response_actions=["investigate_source"],
            ),
            DetectionRule(
                rule_id="DATA-EXFIL-001",
                name="Large Data Transfer Detection",
                description="Detects unusually large data access or transfer events",
                severity="HIGH",
                mitre_mapping="T1048",
                detection_logic={"type": "anomaly", "field": "resource_type", "value": "data", "deviation": 3.0},
                response_actions=["block_source", "notify_security_team"],
            ),
            DetectionRule(
                rule_id="PRIV-ESCALATION-001",
                name="Privilege Escalation Attempt",
                description="Detects attempts to escalate privileges",
                severity="CRITICAL",
                mitre_mapping="T1068",
                detection_logic={"type": "pattern", "pattern": r"(escalat|sudo|su root|privileged)"},
                response_actions=["block_user", "revoke_session", "notify_admin"],
            ),
            DetectionRule(
                rule_id="SENSITIVE-ACCESS-001",
                name="Sensitive Resource Access",
                description="Detects access to sensitive resources outside business hours",
                severity="MEDIUM",
                mitre_mapping="T1005",
                detection_logic={"type": "temporal", "field": "resource_type", "value": "phi_data", "business_hours": "true"},
                response_actions=["log_full_details", "notify_compliance"],
            ),
            DetectionRule(
                rule_id="ANOMALOUS-LOCATION-001",
                name="Anomalous Access Location",
                description="Detects access from unusual geographic locations",
                severity="HIGH",
                mitre_mapping="T1078",
                detection_logic={"type": "anomaly", "field": "source_ip", "method": "geo_unusual"},
                response_actions=["require_mfa", "notify_user"],
            ),
            DetectionRule(
                rule_id="MALICIOUS-IP-001",
                name="Known Malicious IP",
                description="Detects events from known malicious IP addresses",
                severity="CRITICAL",
                mitre_mapping="T1071",
                detection_logic={"type": "blocklist", "field": "source_ip"},
                response_actions=["block_ip", "notify_security_team", "incident_response"],
            ),
        ]

        for rule in default_rules:
            self.add_rule(rule)

    def add_rule(self, rule: DetectionRule) -> None:
        if not rule.rule_id:
            rule.rule_id = f"RULE-{uuid4().hex[:8].upper()}"
        self._rules.append(rule)

    def remove_rule(self, rule_id: str) -> bool:
        for i, rule in enumerate(self._rules):
            if rule.rule_id == rule_id:
                self._rules.pop(i)
                return True
        return False

    def add_correlation_rule(self, rule: CorrelationRule) -> None:
        self._correlation_rules.append(rule)

    def register_response_handler(self, action: str, handler: Callable) -> None:
        self._response_handlers[action].append(handler)

    def process_event(self, event: ThreatEvent) -> DetectionResult | None:
        if not event.event_id:
            event.event_id = str(uuid4())

        for rule in self._rules:
            result = self._evaluate_rule(rule, event)
            if result:
                self._alerts.append(result)
                self._execute_response_actions(result)
                return result

        self._buffer_event(event)

        for corr_rule in self._correlation_rules:
            result = self._evaluate_correlation(corr_rule, event)
            if result:
                self._alerts.append(result)
                self._execute_response_actions(result)
                return result

        return None

    def process_events_batch(self, events: list[ThreatEvent]) -> list[DetectionResult]:
        alerts: list[DetectionResult] = []
        for event in events:
            alert = self.process_event(event)
            if alert:
                alerts.append(alert)
        return alerts

    def _evaluate_rule(self, rule: DetectionRule, event: ThreatEvent) -> DetectionResult | None:
        logic = rule.detection_logic
        logic_type = logic.get("type", "")

        try:
            if logic_type == "pattern":
                return self._evaluate_pattern(rule, event, logic)
            if logic_type == "threshold":
                return self._evaluate_threshold(rule, event, logic)
            if logic_type == "anomaly":
                return self._evaluate_anomaly(rule, event, logic)
            if logic_type == "temporal":
                return self._evaluate_temporal(rule, event, logic)
            if logic_type == "blocklist":
                return self._evaluate_blocklist(rule, event, logic)
        except Exception as e:
            logger.error(f"Rule evaluation error for {rule.rule_id}: {e}")

        return None

    def _evaluate_pattern(self, rule: DetectionRule, event: ThreatEvent, logic: dict[str, Any]) -> DetectionResult | None:
        pattern = logic.get("pattern", "")
        if pattern and re.search(pattern, event.description, re.IGNORECASE):
            return DetectionResult(
                alert_id=str(uuid4()),
                rule_id=rule.rule_id,
                severity=rule.severity,
                title=rule.name,
                description=f"Pattern matched: {event.description[:100]}",
                mitre_id=rule.mitre_mapping,
                events=[event],
                response_actions=rule.response_actions,
            )
        return None

    def _evaluate_threshold(self, rule: DetectionRule, event: ThreatEvent, logic: dict[str, Any]) -> DetectionResult | None:
        field = logic.get("field", "")
        value = logic.get("value", "")
        count = logic.get("count", 5)
        window = logic.get("window_seconds", 300)

        field_value = getattr(event, field, "")
        if value and str(field_value) != str(value):
            return None

        key = f"{rule.rule_id}:{field}:{field_value}"
        now = datetime.now(UTC)
        cutoff = now - timedelta(seconds=window)

        self._event_buffer[key] = [
            e for e in self._event_buffer.get(key, [])
            if e.timestamp > cutoff
        ]
        self._event_buffer[key].append(event)

        if len(self._event_buffer[key]) >= count:
            matched_events = list(self._event_buffer[key])
            self._event_buffer[key] = []
            return DetectionResult(
                alert_id=str(uuid4()),
                rule_id=rule.rule_id,
                severity=rule.severity,
                title=rule.name,
                description=f"Threshold exceeded: {len(matched_events)} events in {window}s from {field_value}",
                mitre_id=rule.mitre_mapping,
                events=matched_events,
                response_actions=rule.response_actions,
            )
        return None

    def _evaluate_anomaly(self, rule: DetectionRule, event: ThreatEvent, logic: dict[str, Any]) -> DetectionResult | None:
        field = logic.get("field", "")
        field_value = getattr(event, field, 0)
        deviation = logic.get("deviation", 2.0)

        key = f"{rule.rule_id}:{field}"
        baseline = self._anomaly_baselines.get(key, {"mean": 0.0, "std": 1.0})

        event_key = f"{rule.rule_id}:event_count:{field}:{getattr(event, field, '')}"
        freq = self._event_buffer.get(event_key, [])
        freq.append(event)

        if len(freq) > 5:
            values = [float(hash(e.source)) % 1000 for e in freq[-50:]]
            mean = statistics.mean(values)
            std = statistics.stdev(values) if len(values) > 1 else 1.0

            self._anomaly_baselines[key] = {"mean": mean, "std": max(std, 0.1)}

            current_val = float(hash(event.source)) % 1000
            z_score = abs(current_val - mean) / max(std, 0.1)

            if z_score > deviation:
                return DetectionResult(
                    alert_id=str(uuid4()),
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    title=rule.name,
                    description=f"Anomaly detected: z-score {z_score:.2f} exceeds threshold {deviation}",
                    mitre_id=rule.mitre_mapping,
                    events=[event],
                    response_actions=rule.response_actions,
                )

        self._event_buffer[event_key] = freq[-100:]
        return None

    def _evaluate_temporal(self, rule: DetectionRule, event: ThreatEvent, logic: dict[str, Any]) -> DetectionResult | None:
        field = logic.get("field", "")
        value = logic.get("value", "")

        field_value = getattr(event, field, "")
        if value and str(field_value) != str(value):
            return None

        hour = event.timestamp.hour if event.timestamp else datetime.now(UTC).hour
        is_business_hours = 8 <= hour <= 18

        if logic.get("business_hours", "true") == "true" and not is_business_hours:
            return DetectionResult(
                alert_id=str(uuid4()),
                rule_id=rule.rule_id,
                severity=rule.severity,
                title=rule.name,
                description=f"Access to {value} outside business hours ({hour}:00)",
                mitre_id=rule.mitre_mapping,
                events=[event],
                response_actions=rule.response_actions,
            )

        return None

    def _evaluate_blocklist(self, rule: DetectionRule, event: ThreatEvent, logic: dict[str, Any]) -> DetectionResult | None:
        blocklisted_ips = ["1.2.3.4", "10.0.0.1", "192.168.1.1"]
        field = logic.get("field", "")
        field_value = str(getattr(event, field, ""))

        if field_value in blocklisted_ips:
            return DetectionResult(
                alert_id=str(uuid4()),
                rule_id=rule.rule_id,
                severity=rule.severity,
                title=rule.name,
                description=f"Event from blocklisted {field}: {field_value}",
                mitre_id=rule.mitre_mapping,
                events=[event],
                response_actions=rule.response_actions,
            )
        return None

    def _evaluate_correlation(self, rule: CorrelationRule, event: ThreatEvent) -> DetectionResult | None:
        conditions = rule.conditions
        field = conditions.get("field", "")
        value = conditions.get("value", "")
        window = conditions.get("window_seconds", rule.window_seconds)

        field_value = getattr(event, field, "")
        if str(field_value) != str(value):
            return None

        key = f"corr_{rule.name}_{field}_{field_value}"
        now = datetime.now(UTC)
        cutoff = now - timedelta(seconds=window)

        self._event_buffer[key] = [
            e for e in self._event_buffer.get(key, [])
            if e.timestamp > cutoff
        ]
        self._event_buffer[key].append(event)

        min_events = conditions.get("min_events", 2)
        if len(self._event_buffer[key]) >= min_events:
            matched = list(self._event_buffer[key])
            threat_types = [e.threat_type for e in matched]

            return DetectionResult(
                alert_id=str(uuid4()),
                rule_id=rule.name,
                severity=rule.severity,
                title=f"Correlation: {rule.name}",
                description=rule.description,
                mitre_id=None,
                events=matched,
                response_actions=[],
            )

        return None

    def _execute_response_actions(self, alert: DetectionResult) -> None:
        for action in alert.response_actions:
            handlers = self._response_handlers.get(action, [])
            for handler in handlers:
                try:
                    handler(alert)
                except Exception as e:
                    logger.error(f"Response handler '{action}' failed: {e}")

    def prioritize_alerts(self, alert: DetectionResult) -> int:
        severity_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        score = severity_rank.get(alert.severity, 0)

        if len(alert.events) > 5:
            score += 1

        mitre_rank = len(alert.mitre_id or "")
        score += mitre_rank > 0

        return score

    def reduce_false_positives(self, events: list[ThreatEvent]) -> list[ThreatEvent]:
        seen_sources: dict[str, int] = defaultdict(int)
        for e in events:
            key = f"{e.threat_type}:{e.source}:{e.mitre_attack_id}"
            seen_sources[key] += 1

        filtered: list[ThreatEvent] = []
        source_counts: dict[str, int] = defaultdict(int)

        for e in sorted(events, key=lambda x: x.timestamp, reverse=True):
            source_key = f"{e.threat_type}:{e.source}"
            source_counts[source_key] += 1
            if source_counts[source_key] <= 3:
                filtered.append(e)

        return filtered

    def deduplicate_alerts(self, alerts: list[DetectionResult]) -> list[DetectionResult]:
        seen: set[str] = set()
        deduped: list[DetectionResult] = []

        for alert in alerts:
            key = f"{alert.rule_id}:{alert.description[:50]}"
            if key not in seen:
                seen.add(key)
                deduped.append(alert)

        return sorted(deduped, key=lambda a: self.prioritize_alerts(a), reverse=True)

    def get_mitre_coverage(self) -> dict[str, list[str]]:
        coverage: dict[str, list[str]] = defaultdict(list)
        for rule in self._rules:
            if rule.mitre_mapping:
                coverage[rule.mitre_mapping].append(rule.rule_id)
        return dict(coverage)

    def run_scheduled_scan(self) -> list[DetectionResult]:
        alerts: list[DetectionResult] = []
        now = datetime.now(UTC)

        for key, events in list(self._event_buffer.items()):
            if len(events) > 20:
                alerts.append(DetectionResult(
                    alert_id=str(uuid4()),
                    rule_id="SCHEDULED-SCAN-001",
                    severity="MEDIUM",
                    title="High Event Volume Detected",
                    description=f"Buffer '{key}' has {len(events)} events - possible ongoing activity",
                    mitre_id=None,
                    events=events[-10:],
                    response_actions=["review_event_buffer"],
                ))

        return alerts

    def clear_event_buffer(self) -> int:
        count = sum(len(v) for v in self._event_buffer.values())
        self._event_buffer.clear()
        return count
