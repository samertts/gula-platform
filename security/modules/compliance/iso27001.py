from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from security.modules.compliance.models import (
    ComplianceControl,
    ComplianceFramework,
    ComplianceReport,
    ControlStatus,
)

logger = logging.getLogger(__name__)

ISO27001_DOMAINS: Dict[str, str] = {
    "A.5": "Organizational Controls",
    "A.6": "People Controls",
    "A.7": "Physical Controls",
    "A.8": "Technological Controls",
}

ISO27001_ANNEX_A: Dict[str, Dict[str, Any]] = {
    "A.5.1": {"domain": "A.5", "description": "Information security policy"},
    "A.5.2": {"domain": "A.5", "description": "Information security roles and responsibilities"},
    "A.5.3": {"domain": "A.5", "description": "Segregation of duties"},
    "A.5.4": {"domain": "A.5", "description": "Management responsibilities"},
    "A.5.5": {"domain": "A.5", "description": "Contact with authorities"},
    "A.5.6": {"domain": "A.5", "description": "Contact with special interest groups"},
    "A.5.7": {"domain": "A.5", "description": "Information security in project management"},
    "A.5.8": {"domain": "A.5", "description": "Security in development and procurement"},
    "A.5.9": {"domain": "A.5", "description": "Inventory of assets"},
    "A.5.10": {"domain": "A.5", "description": "Acceptable use of assets"},
    "A.5.11": {"domain": "A.5", "description": "Return of assets"},
    "A.5.12": {"domain": "A.5", "description": "Classification of information"},
    "A.5.13": {"domain": "A.5", "description": "Labelling of information"},
    "A.5.14": {"domain": "A.5", "description": "Information transfer"},
    "A.5.15": {"domain": "A.5", "description": "Access control policy"},
    "A.5.16": {"domain": "A.5", "description": "Identity management"},
    "A.5.17": {"domain": "A.5", "description": "Authentication information"},
    "A.5.18": {"domain": "A.5", "description": "Access rights"},
    "A.5.19": {"domain": "A.5", "description": "Information security in supplier relationships"},
    "A.5.20": {"domain": "A.5", "description": "Supplier service delivery management"},
    "A.5.21": {"domain": "A.5", "description": "Managing security in ICT supply chain"},
    "A.5.22": {"domain": "A.5", "description": "Monitoring, review and evaluation of ISMS"},
    "A.5.23": {"domain": "A.5", "description": "Information security incident management"},
    "A.5.24": {"domain": "A.5", "description": "Information security incident reporting"},
    "A.5.25": {"domain": "A.5", "description": "Business continuity planning"},
    "A.5.26": {"domain": "A.5", "description": "Business continuity procedures"},
    "A.5.27": {"domain": "A.5", "description": "Business continuity testing"},
    "A.5.28": {"domain": "A.5", "description": "Business continuity plan maintenance"},
    "A.5.29": {"domain": "A.5", "description": "Information security during disruption"},
    "A.5.30": {"domain": "A.5", "description": "ICT readiness for business continuity"},
    "A.5.31": {"domain": "A.5", "description": "Legal, statutory, regulatory and contractual requirements"},
    "A.5.32": {"domain": "A.5", "description": "Intellectual property rights"},
    "A.5.33": {"domain": "A.5", "description": "Protection of records"},
    "A.5.34": {"domain": "A.5", "description": "Privacy and protection of PII"},
    "A.5.35": {"domain": "A.5", "description": "Independent review of information security"},
    "A.5.36": {"domain": "A.5", "description": "Compliance with security policies"},
    "A.6.1": {"domain": "A.6", "description": "Screening"},
    "A.6.2": {"domain": "A.6", "description": "Terms and conditions of employment"},
    "A.6.3": {"domain": "A.6", "description": "Information security awareness, education and training"},
    "A.6.4": {"domain": "A.6", "description": "Disciplinary process"},
    "A.6.5": {"domain": "A.6", "description": "Responsibilities after termination or change"},
    "A.6.6": {"domain": "A.6", "description": "Confidentiality agreements"},
    "A.6.7": {"domain": "A.6", "description": "Remote working"},
    "A.6.8": {"domain": "A.6", "description": "Information security incident reporting by personnel"},
    "A.7.1": {"domain": "A.7", "description": "Physical security perimeter"},
    "A.7.2": {"domain": "A.7", "description": "Physical entry controls"},
    "A.7.3": {"domain": "A.7", "description": "Securing offices, rooms and facilities"},
    "A.7.4": {"domain": "A.7", "description": "Physical security monitoring"},
    "A.7.5": {"domain": "A.7", "description": "Protecting against physical threats"},
    "A.7.6": {"domain": "A.7", "description": "Working in secure areas"},
    "A.7.7": {"domain": "A.7", "description": "Clear desk and clear screen policy"},
    "A.7.8": {"domain": "A.7", "description": "Equipment siting and protection"},
    "A.7.9": {"domain": "A.7", "description": "Security of assets off-premises"},
    "A.7.10": {"domain": "A.7", "description": "Storage media"},
    "A.7.11": {"domain": "A.7", "description": "Supporting utilities"},
    "A.7.12": {"domain": "A.7", "description": "Cabling security"},
    "A.7.13": {"domain": "A.7", "description": "Equipment maintenance"},
    "A.7.14": {"domain": "A.7", "description": "Secure disposal or reuse of equipment"},
    "A.8.1": {"domain": "A.8", "description": "User endpoint devices"},
    "A.8.2": {"domain": "A.8", "description": "Privileged access rights"},
    "A.8.3": {"domain": "A.8", "description": "Information access restriction"},
    "A.8.4": {"domain": "A.8", "description": "Access to source code"},
    "A.8.5": {"domain": "A.8", "description": "Secure authentication"},
    "A.8.6": {"domain": "A.8", "description": "Capacity management"},
    "A.8.7": {"domain": "A.8", "description": "Protection against malware"},
    "A.8.8": {"domain": "A.8", "description": "Management of technical vulnerabilities"},
    "A.8.9": {"domain": "A.8", "description": "Configuration management"},
    "A.8.10": {"domain": "A.8", "description": "Information deletion"},
    "A.8.11": {"domain": "A.8", "description": "Data masking"},
    "A.8.12": {"domain": "A.8", "description": "Data leakage prevention"},
    "A.8.13": {"domain": "A.8", "description": "Information backup"},
    "A.8.14": {"domain": "A.8", "description": "Redundancy of information processing facilities"},
    "A.8.15": {"domain": "A.8", "description": "Logging"},
    "A.8.16": {"domain": "A.8", "description": "Monitoring activities"},
    "A.8.17": {"domain": "A.8", "description": "Clock synchronization"},
    "A.8.18": {"domain": "A.8", "description": "Use of privileged utility programs"},
    "A.8.19": {"domain": "A.8", "description": "Installation of software on operational systems"},
    "A.8.20": {"domain": "A.8", "description": "Network controls"},
    "A.8.21": {"domain": "A.8", "description": "Security of network services"},
    "A.8.22": {"domain": "A.8", "description": "Segregation of networks"},
    "A.8.23": {"domain": "A.8", "description": "Web filtering"},
    "A.8.24": {"domain": "A.8", "description": "Use of cryptography"},
    "A.8.25": {"domain": "A.8", "description": "Secure development lifecycle"},
    "A.8.26": {"domain": "A.8", "description": "Application security requirements"},
    "A.8.27": {"domain": "A.8", "description": "Secure system architecture and engineering"},
    "A.8.28": {"domain": "A.8", "description": "Secure coding"},
    "A.8.29": {"domain": "A.8", "description": "Security testing in development"},
    "A.8.30": {"domain": "A.8", "description": "Outsourced development"},
    "A.8.31": {"domain": "A.8", "description": "Separation of development, test and production"},
    "A.8.32": {"domain": "A.8", "description": "Change management"},
    "A.8.33": {"domain": "A.8", "description": "Test information"},
    "A.8.34": {"domain": "A.8", "description": "Protection of audit information"},
}


class ISO27001Validator:
    def __init__(self):
        self._controls: Dict[str, ComplianceControl] = {}
        self._initialize_controls()

    def _initialize_controls(self) -> None:
        for control_id, control_info in ISO27001_ANNEX_A.items():
            domain = control_info["domain"]
            self._controls[control_id] = ComplianceControl(
                control_id=control_id,
                framework=ComplianceFramework.ISO_27001,
                category=ISO27001_DOMAINS.get(domain, "Unknown"),
                description=f"ISO 27001 {control_id}: {control_info['description']}",
                implementation_status=ControlStatus.NOT_IMPLEMENTED,
                test_procedure=f"Verify ISO 27001 Annex A control {control_id}",
                risk_if_missing=f"Non-compliance with ISO 27001 {control_id}",
            )

    def update_control(self, control_id: str, status: ControlStatus,
                        evidence: Optional[List[str]] = None) -> bool:
        if control_id in self._controls:
            self._controls[control_id].implementation_status = status
            if evidence:
                self._controls[control_id].evidence = evidence
            self._controls[control_id].last_assessed = datetime.now(timezone.utc)
            return True
        return False

    def update_controls_by_domain(self, domain: str, status: ControlStatus) -> int:
        updated = 0
        for control_id, control in self._controls.items():
            if control.category == ISO27001_DOMAINS.get(domain, ""):
                control.implementation_status = status
                control.last_assessed = datetime.now(timezone.utc)
                updated += 1
        return updated

    def verify_isms_implementation(self) -> Dict[str, Any]:
        isms_controls = ["A.5.1", "A.5.2", "A.5.3", "A.5.22", "A.5.23", "A.5.35", "A.5.36"]
        findings: List[str] = []
        passed = True

        for cid in isms_controls:
            control = self._controls.get(cid)
            if control:
                if control.implementation_status in (ControlStatus.NOT_IMPLEMENTED, ControlStatus.PARTIALLY_IMPLEMENTED):
                    findings.append(f"ISMS control {cid} is not fully implemented ({control.implementation_status.value})")
                    passed = False

        return {"passed": passed, "findings": findings, "isms_readiness": passed}

    def generate_soa(self) -> str:
        soa_lines = [
            "STATEMENT OF APPLICABILITY",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            f"Framework: ISO/IEC 27001:2022",
            "=" * 60,
            "",
        ]

        for domain_id, domain_name in ISO27001_DOMAINS.items():
            soa_lines.append(f"\n{domain_id}: {domain_name}")
            soa_lines.append("-" * 40)
            domain_controls = [(cid, c) for cid, c in self._controls.items() if c.category == domain_name]
            for cid, control in sorted(domain_controls, key=lambda x: x[0]):
                applicable = control.implementation_status != ControlStatus.NOT_APPLICABLE
                status_str = control.implementation_status.value.replace("_", " ").title()
                soa_lines.append(f"  {cid}: {'Applicable' if applicable else 'Not Applicable'} - {status_str}")
                soa_lines.append(f"        {control.description[:80]}")

        return "\n".join(soa_lines)

    def manage_evidence(self, control_id: str, evidence: List[str]) -> bool:
        if control_id in self._controls:
            self._controls[control_id].evidence.extend(evidence)
            self._controls[control_id].last_assessed = datetime.now(timezone.utc)
            return True
        return False

    def get_domain_summary(self) -> Dict[str, Dict[str, int]]:
        summary: Dict[str, Dict[str, int]] = {}
        for domain_id, domain_name in ISO27001_DOMAINS.items():
            controls = [c for c in self._controls.values() if c.category == domain_name]
            summary[domain_name] = {
                "total": len(controls),
                "implemented": sum(1 for c in controls if c.implementation_status == ControlStatus.IMPLEMENTED),
                "partial": sum(1 for c in controls if c.implementation_status == ControlStatus.PARTIALLY_IMPLEMENTED),
                "missing": sum(1 for c in controls if c.implementation_status == ControlStatus.NOT_IMPLEMENTED),
                "na": sum(1 for c in controls if c.implementation_status == ControlStatus.NOT_APPLICABLE),
            }
        return summary

    def generate_report(self) -> ComplianceReport:
        controls = list(self._controls.values())
        passed = sum(1 for c in controls if c.implementation_status == ControlStatus.IMPLEMENTED)
        failed = sum(1 for c in controls if c.implementation_status in (
            ControlStatus.NOT_IMPLEMENTED, ControlStatus.PARTIALLY_IMPLEMENTED))

        not_implemented = [c for c in controls if c.implementation_status == ControlStatus.NOT_IMPLEMENTED]
        remediation = {c.control_id: f"Implement ISO 27001 {c.control_id}" for c in not_implemented[:20]}

        total = len(controls)
        if passed / max(total, 1) >= 0.9:
            overall = ControlStatus.IMPLEMENTED
        elif passed / max(total, 1) >= 0.5:
            overall = ControlStatus.PARTIALLY_IMPLEMENTED
        else:
            overall = ControlStatus.NOT_IMPLEMENTED

        return ComplianceReport(
            framework=ComplianceFramework.ISO_27001,
            overall_status=overall,
            control_count=total,
            passed=passed,
            failed=failed,
            findings=not_implemented[:50],
            remediation_plan=remediation,
        )
