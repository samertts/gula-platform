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

HIPAA_SECURITY_RULE_CATEGORIES: Dict[str, str] = {
    "Administrative": "Administrative Safeguards",
    "Physical": "Physical Safeguards",
    "Technical": "Technical Safeguards",
    "Organizational": "Organizational Requirements",
    "Documentation": "Documentation and Policies",
}

HIPAA_CONTROLS: Dict[str, Dict[str, Any]] = {
    "ADM-1": {"category": "Administrative", "description": "Security management process - risk analysis and management"},
    "ADM-2": {"category": "Administrative", "description": "Security management process - sanction policy"},
    "ADM-3": {"category": "Administrative", "description": "Security management process - information system activity review"},
    "ADM-4": {"category": "Administrative", "description": "Assigned security responsibility - named security official"},
    "ADM-5": {"category": "Administrative", "description": "Workforce security - authorization and supervision"},
    "ADM-6": {"category": "Administrative", "description": "Workforce security - workforce clearance procedures"},
    "ADM-7": {"category": "Administrative", "description": "Workforce security - termination procedures"},
    "ADM-8": {"category": "Administrative", "description": "Information access management - authorization policies"},
    "ADM-9": {"category": "Administrative", "description": "Information access management - access authorization"},
    "ADM-10": {"category": "Administrative", "description": "Information access management - access establishment and modification"},
    "ADM-11": {"category": "Administrative", "description": "Security awareness and training - security reminders"},
    "ADM-12": {"category": "Administrative", "description": "Security awareness and training - protection from malicious software"},
    "ADM-13": {"category": "Administrative", "description": "Security awareness and training - login monitoring"},
    "ADM-14": {"category": "Administrative", "description": "Security awareness and training - password management"},
    "ADM-15": {"category": "Administrative", "description": "Security incident procedures - response and reporting"},
    "ADM-16": {"category": "Administrative", "description": "Contingency plan - data backup plan"},
    "ADM-17": {"category": "Administrative", "description": "Contingency plan - disaster recovery plan"},
    "ADM-18": {"category": "Administrative", "description": "Contingency plan - emergency mode operation plan"},
    "ADM-19": {"category": "Administrative", "description": "Contingency plan - testing and revision procedures"},
    "ADM-20": {"category": "Administrative", "description": "Contingency plan - applications and data criticality analysis"},
    "ADM-21": {"category": "Administrative", "description": "Evaluation - periodic security evaluations"},
    "ADM-22": {"category": "Administrative", "description": "Business associate contracts - written contracts with BAs"},
    "PHY-1": {"category": "Physical", "description": "Facility access controls - contingency operations"},
    "PHY-2": {"category": "Physical", "description": "Facility access controls - facility security plan"},
    "PHY-3": {"category": "Physical", "description": "Facility access controls - access control and validation"},
    "PHY-4": {"category": "Physical", "description": "Facility access controls - maintenance records"},
    "PHY-5": {"category": "Physical", "description": "Workstation use - proper workstation use policies"},
    "PHY-6": {"category": "Physical", "description": "Workstation security - physical safeguards for workstations"},
    "PHY-7": {"category": "Physical", "description": "Device and media controls - disposal of devices"},
    "PHY-8": {"category": "Physical", "description": "Device and media controls - media re-use"},
    "PHY-9": {"category": "Physical", "description": "Device and media controls - accountability for hardware"},
    "PHY-10": {"category": "Physical", "description": "Device and media controls - data backup and storage"},
    "TEC-1": {"category": "Technical", "description": "Access control - unique user identification"},
    "TEC-2": {"category": "Technical", "description": "Access control - emergency access procedure"},
    "TEC-3": {"category": "Technical", "description": "Access control - automatic logoff"},
    "TEC-4": {"category": "Technical", "description": "Access control - encryption and decryption for ePHI"},
    "TEC-5": {"category": "Technical", "description": "Audit controls - hardware, software, and procedural mechanisms"},
    "TEC-6": {"category": "Technical", "description": "Integrity controls - mechanism to authenticate ePHI"},
    "TEC-7": {"category": "Technical", "description": "Integrity controls - person or entity authentication"},
    "TEC-8": {"category": "Technical", "description": "Transmission security - integrity controls"},
    "TEC-9": {"category": "Technical", "description": "Transmission security - encryption for ePHI in transit"},
    "ORG-1": {"category": "Organizational", "description": "Business associate contract requirements"},
    "ORG-2": {"category": "Organizational", "description": "Group health plan requirements"},
    "DOC-1": {"category": "Documentation", "description": "Written privacy policies and procedures"},
    "DOC-2": {"category": "Documentation", "description": "Documentation retention (6 years minimum)"},
    "DOC-3": {"category": "Documentation", "description": "Documentation availability for review"},
    "DOC-4": {"category": "Documentation", "description": "Policy and procedure updates as needed"},
}

HIPAA_PRIVACY_RULE_CONTROLS: Dict[str, str] = {
    "PRIV-1": "Patient rights to access PHI",
    "PRIV-2": "Patient rights to amend PHI",
    "PRIV-3": "Patient rights to accounting of disclosures",
    "PRIV-4": "Notice of privacy practices",
    "PRIV-5": "Minimum necessary use of PHI",
    "PRIV-6": "Restriction requests by patients",
    "PRIV-7": "Alternative communications",
    "PRIV-8": "Authorization for uses and disclosures",
    "PRIV-9": "Verification requirements",
    "PRIV-10": "Patient complaint procedures",
    "PRIV-11": "Sale of PHI restrictions",
    "PRIV-12": "Marketing communications restrictions",
}

HITECH_CONTROLS: Dict[str, str] = {
    "HITECH-1": "Breach notification to affected individuals",
    "HITECH-2": "Breach notification to HHS",
    "HITECH-3": "Breach notification to media",
    "HITECH-4": "Business associate direct liability",
    "HITECH-5": "Accounting of disclosures for EHR",
    "HITECH-6": "Prohibition on sale of ePHI",
    "HITECH-7": "Access to PHI in electronic format",
    "HITECH-8": "Restriction requests for PHI disclosures",
    "HITECH-9": "Audit and enforcement provisions",
    "HITECH-10": "Penalty increases for violations",
}


class HIPAAValidator:
    def __init__(self):
        self._security_controls: Dict[str, ComplianceControl] = {}
        self._privacy_controls: Dict[str, ComplianceControl] = {}
        self._hitech_controls: Dict[str, ComplianceControl] = {}
        self._initialize_controls()

    def _initialize_controls(self) -> None:
        for cid, info in HIPAA_CONTROLS.items():
            self._security_controls[cid] = ComplianceControl(
                control_id=f"HIPAA-SEC-{cid}",
                framework=ComplianceFramework.HIPAA,
                category=f"Security Rule: {info['category']}",
                description=f"HIPAA Security Rule {info['category']}: {info['description']}",
                implementation_status=ControlStatus.NOT_IMPLEMENTED,
                test_procedure=f"Verify HIPAA {info['category']} control {cid}",
                risk_if_missing=f"HIPAA violation - {info['description']}",
            )

        for cid, desc in HIPAA_PRIVACY_RULE_CONTROLS.items():
            self._privacy_controls[cid] = ComplianceControl(
                control_id=f"HIPAA-PRIV-{cid}",
                framework=ComplianceFramework.HIPAA,
                category="Privacy Rule",
                description=f"HIPAA Privacy Rule: {desc}",
                implementation_status=ControlStatus.NOT_IMPLEMENTED,
                test_procedure=f"Verify HIPAA Privacy Rule {cid}",
                risk_if_missing=f"HIPAA privacy violation - {desc}",
            )

        for cid, desc in HITECH_CONTROLS.items():
            self._hitech_controls[cid] = ComplianceControl(
                control_id=f"HITECH-{cid}",
                framework=ComplianceFramework.HIPAA,
                category="HITECH Act",
                description=f"HITECH Act: {desc}",
                implementation_status=ControlStatus.NOT_IMPLEMENTED,
                test_procedure=f"Verify HITECH {cid}",
                risk_if_missing=f"HITECH violation - {desc}",
            )

    def update_control(self, control_set: str, control_id: str,
                        status: ControlStatus, evidence: Optional[List[str]] = None) -> bool:
        target = self._get_control_set(control_set)
        if not target or control_id not in target:
            return False
        target[control_id].implementation_status = status
        if evidence:
            target[control_id].evidence = evidence
        target[control_id].last_assessed = datetime.now(timezone.utc)
        return True

    def _get_control_set(self, name: str) -> Optional[Dict[str, ComplianceControl]]:
        mapping = {
            "security": self._security_controls,
            "privacy": self._privacy_controls,
            "hitech": self._hitech_controls,
            "all": {**self._security_controls, **self._privacy_controls, **self._hitech_controls},
        }
        return mapping.get(name.lower())

    def verify_breach_notification(self, breach_data: Dict[str, Any]) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        phi_involved = breach_data.get("phi_involved", False)
        individuals_affected = breach_data.get("individuals_affected", 0)
        notification_days = breach_data.get("notification_days", 0)

        if phi_involved and individuals_affected > 0:
            if notification_days > 60:
                findings.append(f"Breach notification took {notification_days} days (max 60)")
                passed = False
            if individuals_affected > 500:
                findings.append("Breach > 500 individuals requires media notification and HHS notification")
                passed = False

        return {"passed": passed, "findings": findings}

    def verify_patient_rights(self, capability_data: Dict[str, bool]) -> Dict[str, Any]:
        required = ["access_phi", "amend_phi", "accounting_disclosures", "restrict_uses", "request_alternative_comms"]
        findings: List[str] = []
        passed = True

        for right in required:
            if not capability_data.get(right, False):
                findings.append(f"Patient right '{right}' is not implemented")
                passed = False

        return {"passed": passed, "findings": findings}

    def check_edi_transaction_security(self, edi_capabilities: Dict[str, bool]) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        required_edi = ["x12_837", "x12_835", "x12_270", "x12_271", "x12_276", "x12_277", "x12_278", "x12_820", "x12_834"]
        for transaction in required_edi:
            if edi_capabilities.get(transaction, False):
                if not edi_capabilities.get(f"{transaction}_secure", False):
                    findings.append(f"EDI transaction {transaction} is not secured")
                    passed = False

        if not edi_capabilities.get("tls_enabled", False):
            findings.append("EDI transactions not transmitted over TLS")
            passed = False

        if not edi_capabilities.get("edi_agreement", False):
            findings.append("EDI trading partner agreement not in place")
            passed = False

        return {"passed": passed, "findings": findings}

    def verify_covered_entity(self, entity_type: str) -> Dict[str, Any]:
        covered_entities = ["health_plan", "healthcare_clearinghouse", "healthcare_provider"]
        business_associates = ["billing_company", "transcription", "cloud_provider", "analytics", "consultant"]

        findings: List[str] = []
        passed = True

        if entity_type in covered_entities:
            findings.append("Entity is a Covered Entity - must comply with full HIPAA requirements")
        elif entity_type in business_associates:
            findings.append("Entity is a Business Associate - must have BA Agreement and comply with Security Rule")
            passed = False
        else:
            findings.append("Entity type unknown - review HIPAA applicability")
            passed = False

        return {"passed": passed, "findings": findings}

    def integrate_healthcare_security(self) -> Dict[str, Any]:
        integration_points: List[str] = [
            "Patient data encryption (AES-256 at rest, TLS 1.2+ in transit)",
            "Access control: role-based access for healthcare staff",
            "Audit logging: track all ePHI access and modifications",
            "Authentication: MFA for all clinical system access",
            "Session management: automatic timeout for clinical workstations",
            "Backup and recovery: encrypted backups with DR testing",
            "Vulnerability management: regular scanning of clinical systems",
            "Incident response: HIPAA-compliant breach notification procedures",
        ]

        return {
            "integration_points": integration_points,
            "description": "Healthcare security modules integrated with HIPAA compliance controls",
        }

    def generate_report(self) -> ComplianceReport:
        all_controls = {**self._security_controls, **self._privacy_controls, **self._hitech_controls}
        controls = list(all_controls.values())
        passed = sum(1 for c in controls if c.implementation_status == ControlStatus.IMPLEMENTED)
        failed = sum(1 for c in controls if c.implementation_status in (
            ControlStatus.NOT_IMPLEMENTED, ControlStatus.PARTIALLY_IMPLEMENTED))

        not_implemented = [c for c in controls if c.implementation_status == ControlStatus.NOT_IMPLEMENTED]
        remediation = {c.control_id: c.description[:60] for c in not_implemented[:20]}

        total = len(controls)
        if passed / max(total, 1) >= 0.9:
            overall = ControlStatus.IMPLEMENTED
        elif passed / max(total, 1) >= 0.5:
            overall = ControlStatus.PARTIALLY_IMPLEMENTED
        else:
            overall = ControlStatus.NOT_IMPLEMENTED

        return ComplianceReport(
            framework=ComplianceFramework.HIPAA,
            overall_status=overall,
            control_count=total,
            passed=passed,
            failed=failed,
            not_applicable=sum(1 for c in controls if c.implementation_status == ControlStatus.NOT_APPLICABLE),
            findings=not_implemented[:50],
            remediation_plan=remediation,
        )
