from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from security.modules.compliance.models import (
    ComplianceControl,
    ComplianceFramework,
    ComplianceReport,
    ControlStatus,
)

logger = logging.getLogger(__name__)


class CSF2Function(str, Enum):
    GOVERN = "GOVERN"
    IDENTIFY = "IDENTIFY"
    PROTECT = "PROTECT"
    DETECT = "DETECT"
    RESPOND = "RESPOND"
    RECOVER = "RECOVER"


class CSFTier(str, Enum):
    PARTIAL = "PARTIAL"
    RISK_INFORMED = "RISK_INFORMED"
    REPEATABLE = "REPEATABLE"
    ADAPTIVE = "ADAPTIVE"


NIST_CSF2_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "GV.OC": {"function": CSF2Function.GOVERN, "name": "Organizational Context"},
    "GV.RM": {"function": CSF2Function.GOVERN, "name": "Risk Management Strategy"},
    "GV.RR": {"function": CSF2Function.GOVERN, "name": "Roles and Responsibilities"},
    "GV.PO": {"function": CSF2Function.GOVERN, "name": "Policy"},
    "GV.OV": {"function": CSF2Function.GOVERN, "name": "Oversight"},
    "GV.SC": {"function": CSF2Function.GOVERN, "name": "Supply Chain Risk Management"},
    "ID.AM": {"function": CSF2Function.IDENTIFY, "name": "Asset Management"},
    "ID.RA": {"function": CSF2Function.IDENTIFY, "name": "Risk Assessment"},
    "ID.IM": {"function": CSF2Function.IDENTIFY, "name": "Improvement"},
    "PR.AC": {"function": CSF2Function.PROTECT, "name": "Identity Management and Access Control"},
    "PR.AW": {"function": CSF2Function.PROTECT, "name": "Awareness and Training"},
    "PR.DS": {"function": CSF2Function.PROTECT, "name": "Data Security"},
    "PR.IP": {"function": CSF2Function.PROTECT, "name": "Information Protection Processes"},
    "PR.MA": {"function": CSF2Function.PROTECT, "name": "Maintenance"},
    "PR.PS": {"function": CSF2Function.PROTECT, "name": "Protective Technology"},
    "DE.AE": {"function": CSF2Function.DETECT, "name": "Anomalies and Events"},
    "DE.CM": {"function": CSF2Function.DETECT, "name": "Continuous Monitoring"},
    "DE.DP": {"function": CSF2Function.DETECT, "name": "Detection Processes"},
    "RS.MA": {"function": CSF2Function.RESPOND, "name": "Incident Management"},
    "RS.CO": {"function": CSF2Function.RESPOND, "name": "Communications"},
    "RS.AN": {"function": CSF2Function.RESPOND, "name": "Analysis"},
    "RS.MI": {"function": CSF2Function.RESPOND, "name": "Mitigation"},
    "RS.IM": {"function": CSF2Function.RESPOND, "name": "Improvements"},
    "RC.RP": {"function": CSF2Function.RECOVER, "name": "Recovery Planning"},
    "RC.IM": {"function": CSF2Function.RECOVER, "name": "Improvements"},
    "RC.CO": {"function": CSF2Function.RECOVER, "name": "Communications"},
}

NIST_CSF2_CONTROLS: Dict[str, Dict[str, Any]] = {
    "GV.OC-1": {"category": "GV.OC", "description": "Organizational mission, vision, and stakeholder expectations are understood"},
    "GV.OC-2": {"category": "GV.OC", "description": "Legal, regulatory, and contractual requirements are identified"},
    "GV.OC-3": {"category": "GV.OC", "description": "Critical services and dependencies are identified"},
    "GV.RM-1": {"category": "GV.RM", "description": "Risk management objectives are established"},
    "GV.RM-2": {"category": "GV.RM", "description": "Risk appetite and tolerance are defined"},
    "GV.RM-3": {"category": "GV.RM", "description": "Risk assessment methodology is established"},
    "GV.RR-1": {"category": "GV.RR", "description": "Cybersecurity roles and responsibilities are defined"},
    "GV.RR-2": {"category": "GV.RR", "description": "Authority and accountability are assigned"},
    "GV.PO-1": {"category": "GV.PO", "description": "Cybersecurity policy is established and communicated"},
    "GV.PO-2": {"category": "GV.PO", "description": "Policy compliance is monitored and enforced"},
    "GV.OV-1": {"category": "GV.OV", "description": "Cybersecurity program oversight is established"},
    "GV.OV-2": {"category": "GV.OV", "description": "Independent reviews of cybersecurity program are conducted"},
    "GV.SC-1": {"category": "GV.SC", "description": "Supply chain risk management strategy is established"},
    "GV.SC-2": {"category": "GV.SC", "description": "Supplier cybersecurity requirements are defined"},
    "ID.AM-1": {"category": "ID.AM", "description": "Physical devices and systems are inventoried"},
    "ID.AM-2": {"category": "ID.AM", "description": "Software platforms and applications are inventoried"},
    "ID.AM-3": {"category": "ID.AM", "description": "Data is classified and cataloged"},
    "ID.AM-4": {"category": "ID.AM", "description": "External information systems are cataloged"},
    "ID.AM-5": {"category": "ID.AM", "description": "Resource prioritization is defined"},
    "ID.RA-1": {"category": "ID.RA", "description": "Vulnerabilities are identified and documented"},
    "ID.RA-2": {"category": "ID.RA", "description": "Threat intelligence is received and analyzed"},
    "ID.RA-3": {"category": "ID.RA", "description": "Risk is assessed for identified threats and vulnerabilities"},
    "ID.RA-4": {"category": "ID.RA", "description": "Risk responses are identified and prioritized"},
    "ID.IM-1": {"category": "ID.IM", "description": "Improvements from lessons learned are integrated"},
    "ID.IM-2": {"category": "ID.IM", "description": "Risk management strategy is updated based on changes"},
    "PR.AC-1": {"category": "PR.AC", "description": "Identities and credentials are managed"},
    "PR.AC-2": {"category": "PR.AC", "description": "Physical access is managed"},
    "PR.AC-3": {"category": "PR.AC", "description": "Remote access is managed"},
    "PR.AC-4": {"category": "PR.AC", "description": "Access permissions are managed"},
    "PR.AC-5": {"category": "PR.AC", "description": "Network integrity is protected"},
    "PR.AC-6": {"category": "PR.AC", "description": "Least privilege principle is enforced"},
    "PR.AC-7": {"category": "PR.AC", "description": "MFA is implemented for all privileged access"},
    "PR.AW-1": {"category": "PR.AW", "description": "Users are trained on cybersecurity awareness"},
    "PR.AW-2": {"category": "PR.AW", "description": "Specialized roles receive role-based training"},
    "PR.DS-1": {"category": "PR.DS", "description": "Data at rest is protected"},
    "PR.DS-2": {"category": "PR.DS", "description": "Data in transit is protected"},
    "PR.DS-3": {"category": "PR.DS", "description": "Assets are formally managed throughout removal"},
    "PR.DS-4": {"category": "PR.DS", "description": "Data integrity is verified"},
    "PR.DS-5": {"category": "PR.DS", "description": "Data backups are maintained"},
    "PR.DS-6": {"category": "PR.DS", "description": "Data minimization principles are applied"},
    "PR.IP-1": {"category": "PR.IP", "description": "Baseline configuration is established"},
    "PR.IP-2": {"category": "PR.IP", "description": "System development lifecycle is managed"},
    "PR.IP-3": {"category": "PR.IP", "description": "Configuration change control is implemented"},
    "PR.IP-4": {"category": "PR.IP", "description": "Security testing is conducted regularly"},
    "PR.IP-5": {"category": "PR.IP", "description": "Vulnerability management program exists"},
    "PR.MA-1": {"category": "PR.MA", "description": "Maintenance and repair of assets is managed"},
    "PR.MA-2": {"category": "PR.MA", "description": "Remote maintenance is authorized and logged"},
    "PR.PS-1": {"category": "PR.PS", "description": "Audit/log records are protected"},
    "PR.PS-2": {"category": "PR.PS", "description": "Protective technologies are deployed at logical boundaries"},
    "DE.AE-1": {"category": "DE.AE", "description": "Baseline of network operations is established"},
    "DE.AE-2": {"category": "DE.AE", "description": "Events are correlated from multiple sources"},
    "DE.AE-3": {"category": "DE.AE", "description": "Event data is analyzed for indicators of compromise"},
    "DE.CM-1": {"category": "DE.CM", "description": "Network is monitored for threats"},
    "DE.CM-2": {"category": "DE.CM", "description": "Physical environment is monitored"},
    "DE.CM-3": {"category": "DE.CM", "description": "Personnel activity is monitored"},
    "DE.CM-4": {"category": "DE.CM", "description": "Malicious code is detected"},
    "DE.DP-1": {"category": "DE.DP", "description": "Detection roles and responsibilities are defined"},
    "DE.DP-2": {"category": "DE.DP", "description": "Detection processes are tested regularly"},
    "RS.MA-1": {"category": "RS.MA", "description": "Incident response plan exists"},
    "RS.MA-2": {"category": "RS.MA", "description": "Incident response plan is tested"},
    "RS.CO-1": {"category": "RS.CO", "description": "Incident response communications plan exists"},
    "RS.CO-2": {"category": "RS.CO", "description": "Stakeholders are notified of incidents"},
    "RS.AN-1": {"category": "RS.AN", "description": "Incidents are analyzed for impact"},
    "RS.AN-2": {"category": "RS.AN", "description": "Forensic analysis is performed"},
    "RS.MI-1": {"category": "RS.MI", "description": "Incidents are contained"},
    "RS.MI-2": {"category": "RS.MI", "description": "Incidents are eradicated"},
    "RS.IM-1": {"category": "RS.IM", "description": "Response plans incorporate lessons learned"},
    "RS.IM-2": {"category": "RS.IM", "description": "Response strategies are updated"},
    "RC.RP-1": {"category": "RC.RP", "description": "Recovery plan exists and is communicated"},
    "RC.RP-2": {"category": "RC.RP", "description": "Recovery procedures are tested"},
    "RC.IM-1": {"category": "RC.IM", "description": "Recovery plans incorporate lessons learned"},
    "RC.IM-2": {"category": "RC.IM", "description": "Recovery strategies are updated"},
    "RC.CO-1": {"category": "RC.CO", "description": "Public relations and communications are managed"},
    "RC.CO-2": {"category": "RC.CO", "description": "Reputation after incidents is repaired"},
}


class NISTCSFValidator:
    def __init__(self):
        self._controls: Dict[str, ComplianceControl] = {}
        self._current_tier: CSFTier = CSFTier.PARTIAL
        self._target_tier: CSFTier = CSFTier.REPEATABLE
        self._initialize_controls()

    def _initialize_controls(self) -> None:
        for control_id, control_info in NIST_CSF2_CONTROLS.items():
            category = control_info["category"]
            cat_info = NIST_CSF2_CATEGORIES.get(category, {})
            self._controls[control_id] = ComplianceControl(
                control_id=control_id,
                framework=ComplianceFramework.NIST_CSF,
                category=f"{cat_info.get('function', '').value}: {cat_info.get('name', category)}",
                description=control_info["description"],
                implementation_status=ControlStatus.NOT_IMPLEMENTED,
                test_procedure=f"Verify NIST CSF 2.0 control {control_info['category']}: {control_info['description']}",
                risk_if_missing=f"Non-compliance with NIST CSF 2.0 category {category}",
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

    def update_controls_by_category(self, category: str, status: ControlStatus) -> int:
        updated = 0
        for control_id, control in self._controls.items():
            if control.category.endswith(category):
                control.implementation_status = status
                control.last_assessed = datetime.now(timezone.utc)
                updated += 1
        return updated

    def assess_tier(self, function: CSF2Function) -> CSFTier:
        function_controls = [c for c in self._controls.values()
                            if c.category.startswith(function.value)]

        if not function_controls:
            return CSFTier.PARTIAL

        implemented = sum(1 for c in function_controls
                         if c.implementation_status == ControlStatus.IMPLEMENTED)
        ratio = implemented / len(function_controls)

        if ratio >= 0.9:
            return CSFTier.ADAPTIVE
        elif ratio >= 0.7:
            return CSFTier.REPEATABLE
        elif ratio >= 0.4:
            return CSFTier.RISK_INFORMED
        return CSFTier.PARTIAL

    def set_tier_assessment(self, current: CSFTier, target: CSFTier) -> None:
        self._current_tier = current
        self._target_tier = target

    def get_tier_gap(self) -> Dict[str, Any]:
        tier_values = {CSFTier.PARTIAL: 1, CSFTier.RISK_INFORMED: 2,
                       CSFTier.REPEATABLE: 3, CSFTier.ADAPTIVE: 4}
        gap = tier_values.get(self._target_tier, 3) - tier_values.get(self._current_tier, 1)

        return {
            "current_tier": self._current_tier.value,
            "target_tier": self._target_tier.value,
            "gap_levels": gap,
            "gap_description": "At tier" if gap == 0 else f"{gap} level(s) below target" if gap > 0 else "Above target",
        }

    def verify_control(self, control_id: str, verification_data: Dict[str, Any]) -> Dict[str, Any]:
        control = self._controls.get(control_id)
        if not control:
            return {"found": False}

        automated_checks = {
            "PR.AC-1": lambda d: d.get("identity_provider", False) and d.get("mfa_enabled", False),
            "PR.AC-7": lambda d: d.get("mfa_privileged", False),
            "PR.DS-1": lambda d: d.get("encryption_at_rest", False),
            "PR.DS-2": lambda d: d.get("encryption_in_transit", False),
            "DE.CM-1": lambda d: d.get("network_monitoring", False),
            "DE.CM-4": lambda d: d.get("antimalware", False) or d.get("edr", False),
        }

        check_fn = automated_checks.get(control_id, lambda d: False)
        return {
            "found": True,
            "control": control_id,
            "description": control.description,
            "category": control.category,
            "automated_check_passed": check_fn(verification_data),
            "current_status": control.implementation_status.value,
        }

    def get_controls_by_function(self) -> Dict[str, List[ComplianceControl]]:
        by_function: Dict[str, List[ComplianceControl]] = {}
        for function in CSF2Function:
            by_function[function.value] = []
        for control in self._controls.values():
            function_prefix = control.category.split(":")[0].strip()
            if function_prefix in by_function:
                by_function[function_prefix].append(control)
        return by_function

    def generate_report(self) -> ComplianceReport:
        controls = list(self._controls.values())
        passed = sum(1 for c in controls if c.implementation_status == ControlStatus.IMPLEMENTED)
        failed = sum(1 for c in controls if c.implementation_status in (
            ControlStatus.NOT_IMPLEMENTED, ControlStatus.PARTIALLY_IMPLEMENTED))

        function_coverage = {}
        for func in CSF2Function:
            fc = [c for c in controls if c.category.startswith(func.value)]
            implemented = sum(1 for c in fc if c.implementation_status == ControlStatus.IMPLEMENTED)
            function_coverage[func.value] = {
                "total": len(fc),
                "implemented": implemented,
                "percentage": round(implemented / max(len(fc), 1) * 100, 1),
            }

        not_implemented = [c for c in controls if c.implementation_status == ControlStatus.NOT_IMPLEMENTED]
        remediation = {c.control_id: f"Implement {c.description[:60]}..." for c in not_implemented[:20]}

        if passed / max(len(controls), 1) >= 0.9:
            overall = ControlStatus.IMPLEMENTED
        elif passed / max(len(controls), 1) >= 0.5:
            overall = ControlStatus.PARTIALLY_IMPLEMENTED
        else:
            overall = ControlStatus.NOT_IMPLEMENTED

        return ComplianceReport(
            framework=ComplianceFramework.NIST_CSF,
            overall_status=overall,
            control_count=len(controls),
            passed=passed,
            failed=failed,
            not_applicable=sum(1 for c in controls if c.implementation_status == ControlStatus.NOT_APPLICABLE),
            findings=not_implemented[:50],
            remediation_plan=remediation,
        )

    def integrate_with_risk_register(self, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        high_risk_controls = {}
        for control_id, control in self._controls.items():
            if control.implementation_status in (ControlStatus.NOT_IMPLEMENTED, ControlStatus.PARTIALLY_IMPLEMENTED):
                if any(risk_keyword in control.description.lower()
                       for risk_keyword in ["vulnerability", "threat", "access", "data", "security"]):
                    high_risk_controls[control_id] = control.description

        return {
            "risk_informed_controls": len(high_risk_controls),
            "high_risk_gaps": high_risk_controls,
            "at_risk_categories": list(set(
                c.category.split(":")[0].strip() for c in self._controls.values()
                if c.implementation_status == ControlStatus.NOT_IMPLEMENTED
            )),
        }
