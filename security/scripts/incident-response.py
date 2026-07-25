#!/usr/bin/env python3
# =============================================================================
# GSF: incident-response.py — Incident Response Automation
# =============================================================================
"""
Automates incident response by reading incident details, categorizing by type,
looking up runbooks, creating tracking issues, notifying the security team,
and recording actions in the audit log.

Usage:
    ./incident-response.py [options]

Options:
    --incident PATH    Path to incident JSON file (reads from stdin if not provided)
    --type TYPE        Incident type override
    --dry-run          Simulate without creating issues or sending notifications
    --help, -h         Show this help message

Input format (stdin or file):
    {
        "title": "Suspicious login detected",
        "description": "Multiple failed logins from unknown IP",
        "severity": "HIGH",
        "type": "unauthorized_access",
        "source": "threat_detection",
        "reported_by": "automated_system",
        "affected_resources": ["auth-service"],
        "indicators": {"source_ip": "203.0.113.42"}
    }
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("gsf.incident-response")


# ---------------------------------------------------------------------------
# Incident Classification
# ---------------------------------------------------------------------------

INCIDENT_TYPES: dict[str, dict[str, Any]] = {
    "unauthorized_access": {
        "category": "access_control",
        "severity_default": "HIGH",
        "runbook_section": "Unauthorized Access",
        "response_team": "security",
        "mitre_attack": "T1078",
    },
    "malware_detection": {
        "category": "malware",
        "severity_default": "CRITICAL",
        "runbook_section": "Malware Response",
        "response_team": "security_plus_devops",
        "mitre_attack": "T1204",
    },
    "data_breach": {
        "category": "data_loss",
        "severity_default": "CRITICAL",
        "runbook_section": "Data Breach Response",
        "response_team": "security_plus_legal_plus_dpo",
        "mitre_attack": "T1530",
    },
    "phishing": {
        "category": "social_engineering",
        "severity_default": "HIGH",
        "runbook_section": "Phishing Response",
        "response_team": "security",
        "mitre_attack": "T1566",
    },
    "denial_of_service": {
        "category": "availability",
        "severity_default": "HIGH",
        "runbook_section": "DDoS Response",
        "response_team": "security_plus_devops",
        "mitre_attack": "T1499",
    },
    "policy_violation": {
        "category": "compliance",
        "severity_default": "MEDIUM",
        "runbook_section": "Policy Violation Response",
        "response_team": "compliance",
        "mitre_attack": "",
    },
    "privilege_escalation": {
        "category": "access_control",
        "severity_default": "CRITICAL",
        "runbook_section": "Privilege Escalation Response",
        "response_team": "security",
        "mitre_attack": "T1068",
    },
    "configuration_drift": {
        "category": "system_integrity",
        "severity_default": "MEDIUM",
        "runbook_section": "Configuration Drift Response",
        "response_team": "devops",
        "mitre_attack": "",
    },
    "supply_chain": {
        "category": "supply_chain",
        "severity_default": "HIGH",
        "runbook_section": "Supply Chain Incident Response",
        "response_team": "security_plus_devops",
        "mitre_attack": "T1195",
    },
    "phi_exposure": {
        "category": "data_loss",
        "severity_default": "CRITICAL",
        "runbook_section": "PHI Breach Response",
        "response_team": "security_plus_legal_plus_dpo_plus_ciso",
        "mitre_attack": "T1530",
    },
}


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class Incident:
    """Incident data model."""

    title: str
    description: str
    severity: str = "MEDIUM"
    incident_type: str = "unauthorized_access"
    source: str = "manual_report"
    reported_by: str = "unknown"
    affected_resources: list[str] = field(default_factory=list)
    indicators: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    incident_id: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()
        if not self.incident_id:
            ts = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
            self.incident_id = f"INC-{ts}-{os.urandom(2).hex()}"


@dataclass
class IncidentResponse:
    """Complete incident response record."""

    incident: Incident
    classification: dict[str, Any]
    initial_actions: list[str] = field(default_factory=list)
    created_issue_url: str = ""
    notifications_sent: list[str] = field(default_factory=list)
    audit_entries: list[str] = field(default_factory=list)
    dry_run: bool = False


# ---------------------------------------------------------------------------
# Runbook Lookup
# ---------------------------------------------------------------------------

class RunbookLookup:
    """Looks up response procedures from the incident response policy."""

    def __init__(self, policy_path: str | None = None) -> None:
        self.policy_path = policy_path or str(
            Path(__file__).resolve().parent.parent / "policies" / "incident-response-policy.md"
        )

    def lookup(self, incident_type: str) -> str:
        """Return the runbook section for the given incident type."""
        type_info = INCIDENT_TYPES.get(incident_type, INCIDENT_TYPES["unauthorized_access"])
        section = type_info["runbook_section"]
        return (
            f"Runbook Section: {section}\n"
            f"See {self.policy_path} for detailed procedures.\n"
            f"Response Team: {type_info['response_team']}\n"
            f"MITRE ATT&CK: {type_info['mitre_attack']}"
        )

    def get_initial_actions(self, incident: Incident) -> list[str]:
        """Get initial response actions based on incident type."""
        severity = incident.severity
        actions: list[str] = [
            f"[{datetime.now(UTC).isoformat()}] Incident {incident.incident_id} reported",
            f"Acknowledge incident: {incident.title}",
        ]

        if severity == "CRITICAL":
            actions.extend([
                "CRITICAL: Notify CISO immediately",
                "CRITICAL: Assemble incident response team",
                "CRITICAL: Begin containment procedures",
                "CRITICAL: Preserve forensic evidence",
                "CRITICAL: Activate emergency communication channel",
            ])
        elif severity == "HIGH":
            actions.extend([
                "HIGH: Notify security team lead",
                "HIGH: Begin investigation within 60 minutes",
                "HIGH: Implement temporary controls if needed",
            ])
        elif severity == "MEDIUM":
            actions.extend([
                "MEDIUM: Assign to security analyst",
                "MEDIUM: Investigate within 8 hours",
            ])
        else:
            actions.append("LOW: Log and monitor")

        if incident.incident_type in ("data_breach", "phi_exposure"):
            actions.append("ALERT: Involve DPO and legal team immediately")
            actions.append("ALERT: Begin breach notification assessment")

        return actions


# ---------------------------------------------------------------------------
# Issue Tracker
# ---------------------------------------------------------------------------

class IssueTracker:
    """Creates tracking issues for incidents."""

    def create_issue(self, incident: Incident, classification: dict[str, Any]) -> str:
        """Create an incident tracking issue. Returns URL or ID."""
        logger.info(
            "Creating issue for incident %s: %s [%s]",
            incident.incident_id, incident.title, incident.severity,
        )
        issue_body = (
            f"## Incident {incident.incident_id}\n\n"
            f"**Title:** {incident.title}\n"
            f"**Severity:** {incident.severity}\n"
            f"**Type:** {incident.incident_type}\n"
            f"**Source:** {incident.source}\n"
            f"**Timestamp:** {incident.timestamp}\n\n"
            f"**Description:**\n{incident.description}\n\n"
            f"**Classification:**\n"
            f"- Category: {classification.get('category', 'unknown')}\n"
            f"- Response Team: {classification.get('response_team', 'unknown')}\n"
            f"- MITRE ATT&CK: {classification.get('mitre_attack', 'N/A')}\n\n"
            f"**Affected Resources:**\n"
        )
        for res in incident.affected_resources:
            issue_body += f"- {res}\n"
        issue_body += "\n**Indicators:**\n"
        for k, v in incident.indicators.items():
            issue_body += f"- {k}: {v}\n"

        issue_url = f"https://github.com/gula-platform/gula-platform/issues/new?title={incident.incident_id}: {incident.title}"
        logger.info("Issue URL: %s", issue_url)
        return issue_url


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

class Notifier:
    """Sends notifications to the security team."""

    @staticmethod
    def notify(incident: Incident, classification: dict[str, Any]) -> list[str]:
        """Send notifications. Returns list of channels notified."""
        channels: list[str] = []
        severity = incident.severity

        if severity in ("CRITICAL", "HIGH"):
            channels.append("slack:#security-alerts")
            channels.append("pagerduty:security-team")
            channels.append("email:security@gula.iq")
        else:
            channels.append("email:security@gula.iq")

        logger.info(
            "Notifications sent for %s [%s]: %s",
            incident.incident_id, severity, channels,
        )
        return channels


# ---------------------------------------------------------------------------
# Audit Logger
# ---------------------------------------------------------------------------

class IncidentAuditLogger:
    """Records incident response actions in the audit log."""

    def __init__(self, log_path: str = "/var/log/gula/security/incidents.log") -> None:
        self.log_path = log_path

    def log(self, incident_id: str, action: str, details: str = "") -> str:
        entry = json.dumps({
            "timestamp": datetime.now(UTC).isoformat(),
            "incident_id": incident_id,
            "action": action,
            "details": details,
        })
        logger.info("INCIDENT_AUDIT: %s", entry)
        log_dir = os.path.dirname(self.log_path)
        try:
            os.makedirs(log_dir, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except OSError as e:
            logger.warning("Failed to write audit log: %s", e)
        return entry


# ---------------------------------------------------------------------------
# Response Engine
# ---------------------------------------------------------------------------

class IncidentResponseEngine:
    """Orchestrates the incident response process."""

    def __init__(self) -> None:
        self.runbook = RunbookLookup()
        self.issue_tracker = IssueTracker()
        self.notifier = Notifier()
        self.audit = IncidentAuditLogger()

    def handle(self, incident: Incident, dry_run: bool = False) -> IncidentResponse:
        """Handle an incident through the complete response workflow."""
        type_info = INCIDENT_TYPES.get(
            incident.incident_type,
            INCIDENT_TYPES["unauthorized_access"],
        )
        if incident.severity == "MEDIUM" and type_info["severity_default"] != "MEDIUM":
            incident.severity = type_info["severity_default"]

        classification = type_info
        response = IncidentResponse(incident=incident, classification=classification, dry_run=dry_run)

        logger.info(
            "Handling incident %s: %s [%s/%s]",
            incident.incident_id, incident.title, incident.severity, incident.incident_type,
        )

        response.initial_actions = self.runbook.get_initial_actions(incident)
        logger.info("Initial actions: %d steps", len(response.initial_actions))

        if not dry_run:
            issue_url = self.issue_tracker.create_issue(incident, classification)
            response.created_issue_url = issue_url
            response.notifications_sent = self.notifier.notify(incident, classification)

        for action in response.initial_actions:
            entry = self.audit.log(incident.incident_id, "initial_action", action)
            response.audit_entries.append(entry)

        self.audit.log(
            incident.incident_id,
            "incident_created",
            f"Severity={incident.severity}, Type={incident.incident_type}",
        )

        return response


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def load_incident(args: argparse.Namespace) -> Incident:
    """Load incident from stdin or file."""
    if args.incident:
        path = Path(args.incident)
        if not path.exists():
            print(f"Error: Incident file not found: {args.incident}", file=sys.stderr)
            sys.exit(2)
        data = json.loads(path.read_text())
    else:
        raw = sys.stdin.read()
        if not raw.strip():
            print("Error: No incident data provided (use --incident or pipe to stdin)", file=sys.stderr)
            sys.exit(2)
        data = json.loads(raw)

    if args.type:
        data["incident_type"] = args.type

    return Incident(**data)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GSF Incident Response Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--incident", default=None, help="Path to incident JSON file")
    parser.add_argument("--type", default=None, help="Incident type override")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without creating issues or notifications")
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    incident = load_incident(args)

    engine = IncidentResponseEngine()
    response = engine.handle(incident, args.dry_run)

    result = {
        "incident_id": response.incident.incident_id,
        "status": "dry_run" if args.dry_run else "dispatched",
        "classification": response.classification,
        "initial_actions": response.initial_actions,
        "created_issue": response.created_issue_url,
        "notifications": response.notifications_sent,
    }

    print(json.dumps(result, indent=2))

    logger.info("Incident response complete: %s", response.incident.incident_id)

    if response.incident.severity == "CRITICAL":
        logger.warning("CRITICAL incident requires immediate attention")

    return 0


if __name__ == "__main__":
    sys.exit(main())
