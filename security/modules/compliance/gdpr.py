from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from security.modules.compliance.models import (
    ComplianceControl,
    ComplianceFramework,
    ComplianceReport,
    ControlStatus,
)

logger = logging.getLogger(__name__)

GDPR_ARTICLES: dict[str, dict[str, Any]] = {
    "ART-5": {"category": "Principles", "description": "Principles relating to processing of personal data"},
    "ART-6": {"category": "Lawfulness", "description": "Lawfulness of processing"},
    "ART-7": {"category": "Consent", "description": "Conditions for consent"},
    "ART-8": {"category": "Consent", "description": "Conditions applicable to child's consent"},
    "ART-9": {"category": "Special Categories", "description": "Processing of special categories of personal data"},
    "ART-10": {"category": "Special Categories", "description": "Processing of personal data relating to criminal convictions"},
    "ART-11": {"category": "Transparency", "description": "Processing which does not require identification"},
    "ART-12": {"category": "Transparency", "description": "Transparent information, communication and modalities"},
    "ART-13": {"category": "Transparency", "description": "Information to be provided where personal data is collected"},
    "ART-14": {"category": "Transparency", "description": "Information to be provided where data not obtained from data subject"},
    "ART-15": {"category": "Data Subject Rights", "description": "Right of access by the data subject"},
    "ART-16": {"category": "Data Subject Rights", "description": "Right to rectification"},
    "ART-17": {"category": "Data Subject Rights", "description": "Right to erasure ('right to be forgotten')"},
    "ART-18": {"category": "Data Subject Rights", "description": "Right to restriction of processing"},
    "ART-19": {"category": "Data Subject Rights", "description": "Notification obligation regarding rectification or erasure"},
    "ART-20": {"category": "Data Subject Rights", "description": "Right to data portability"},
    "ART-21": {"category": "Data Subject Rights", "description": "Right to object"},
    "ART-22": {"category": "Automated Decisions", "description": "Automated individual decision-making, including profiling"},
    "ART-23": {"category": "Restrictions", "description": "Restrictions on data subject rights"},
    "ART-24": {"category": "Controller", "description": "Responsibility of the controller"},
    "ART-25": {"category": "Data Protection by Design", "description": "Data protection by design and by default"},
    "ART-26": {"category": "Joint Controllers", "description": "Joint controllers"},
    "ART-27": {"category": "Representatives", "description": "Representatives of controllers not established in the Union"},
    "ART-28": {"category": "Processor", "description": "Processor obligations"},
    "ART-29": {"category": "Processor", "description": "Processing under the authority of the controller"},
    "ART-30": {"category": "Records", "description": "Records of processing activities"},
    "ART-31": {"category": "Cooperation", "description": "Cooperation with the supervisory authority"},
    "ART-32": {"category": "Security", "description": "Security of processing"},
    "ART-33": {"category": "Breach Notification", "description": "Notification of a personal data breach to the supervisory authority"},
    "ART-34": {"category": "Breach Notification", "description": "Communication of a personal data breach to the data subject"},
    "ART-35": {"category": "DPIA", "description": "Data protection impact assessment"},
    "ART-36": {"category": "DPIA", "description": "Prior consultation with supervisory authority"},
    "ART-37": {"category": "DPO", "description": "Designation of the data protection officer"},
    "ART-38": {"category": "DPO", "description": "Position of the data protection officer"},
    "ART-39": {"category": "DPO", "description": "Tasks of the data protection officer"},
    "ART-40": {"category": "Codes of Conduct", "description": "Codes of conduct"},
    "ART-41": {"category": "Monitoring", "description": "Monitoring of approved codes of conduct"},
    "ART-42": {"category": "Certification", "description": "Certification mechanisms"},
    "ART-43": {"category": "Certification", "description": "Certification bodies"},
    "ART-44": {"category": "Transfers", "description": "General principle for transfers"},
    "ART-45": {"category": "Transfers", "description": "Transfers on the basis of an adequacy decision"},
    "ART-46": {"category": "Transfers", "description": "Transfers subject to appropriate safeguards"},
    "ART-47": {"category": "Transfers", "description": "Binding corporate rules"},
    "ART-48": {"category": "Transfers", "description": "Transfers or disclosures not authorised by Union law"},
    "ART-49": {"category": "Transfers", "description": "Derogations for specific situations"},
    "ART-50": {"category": "Cooperation", "description": "International cooperation for data protection"},
    "ART-51": {"category": "Supervisory", "description": "Supervisory authority establishment"},
    "ART-52": {"category": "Supervisory", "description": "Independence of supervisory authorities"},
    "ART-53": {"category": "Supervisory", "description": "General conditions for members"},
    "ART-54": {"category": "Supervisory", "description": "Rules on the establishment of the supervisory authority"},
    "ART-55": {"category": "Supervisory", "description": "Competence of the lead supervisory authority"},
    "ART-56": {"category": "Supervisory", "description": "Competence of the lead supervisory authority"},
    "ART-57": {"category": "Supervisory", "description": "Tasks of the supervisory authority"},
    "ART-58": {"category": "Supervisory", "description": "Powers of the supervisory authority"},
    "ART-59": {"category": "Supervisory", "description": "Activity reports"},
    "ART-60": {"category": "Cooperation", "description": "Cooperation between lead and other concerned SAs"},
    "ART-77": {"category": "Remedies", "description": "Right to an effective judicial remedy"},
    "ART-78": {"category": "Remedies", "description": "Right to an effective judicial remedy against SA"},
    "ART-79": {"category": "Remedies", "description": "Right to an effective judicial remedy against controller/processor"},
    "ART-80": {"category": "Remedies", "description": "Representation of data subjects"},
    "ART-81": {"category": "Remedies", "description": "Suspension of proceedings"},
    "ART-82": {"category": "Liability", "description": "Right to compensation and liability"},
    "ART-83": {"category": "Penalties", "description": "General conditions for imposing administrative fines"},
    "ART-84": {"category": "Penalties", "description": "Penalties"},
    "ART-85": {"category": "Processing", "description": "Processing and freedom of expression"},
    "ART-86": {"category": "Processing", "description": "Processing and public access to official documents"},
    "ART-87": {"category": "Processing", "description": "Processing of national identification numbers"},
    "ART-88": {"category": "Employment", "description": "Processing in the context of employment"},
    "ART-89": {"category": "Archiving", "description": "Safeguards for archiving and research"},
    "ART-90": {"category": "Obligations", "description": "Obligations of secrecy"},
    "ART-91": {"category": "Existing Data", "description": "Existing data protection rules of churches"},
}


class GDPRValidator:
    def __init__(self):
        self._controls: dict[str, ComplianceControl] = {}
        self._dpia_records: list[dict[str, Any]] = []
        self._dpa_records: list[dict[str, Any]] = []
        self._initialize_controls()

    def _initialize_controls(self) -> None:
        for article_id, info in GDPR_ARTICLES.items():
            self._controls[article_id] = ComplianceControl(
                control_id=f"GDPR-{article_id}",
                framework=ComplianceFramework.GDPR,
                category=f"Article {article_id}: {info['category']}",
                description=f"GDPR Article {article_id}: {info['description']}",
                implementation_status=ControlStatus.NOT_IMPLEMENTED,
                test_procedure=f"Verify GDPR Article {article_id} compliance",
                risk_if_missing="GDPR non-compliance - up to 4% of global annual turnover fine",
            )

    def update_control(self, article_id: str, status: ControlStatus,
                        evidence: list[str] | None = None) -> bool:
        key = f"GDPR-{article_id}"
        if key in self._controls:
            self._controls[key].implementation_status = status
            if evidence:
                self._controls[key].evidence = evidence
            self._controls[key].last_assessed = datetime.now(UTC)
            return True
        return False

    def verify_data_subject_rights(self, capabilities: dict[str, bool]) -> dict[str, Any]:
        rights_map = {
            "access": ("ART-15", "Right of access"),
            "rectification": ("ART-16", "Right to rectification"),
            "erasure": ("ART-17", "Right to erasure"),
            "restriction": ("ART-18", "Right to restriction"),
            "portability": ("ART-20", "Right to data portability"),
            "object": ("ART-21", "Right to object"),
        }

        findings: list[str] = []
        passed = True

        for right, (article, name) in rights_map.items():
            if not capabilities.get(right, False):
                findings.append(f"Data subject right '{name}' (GDPR {article}) is not implemented")
                passed = False

        if capabilities.get("access", False):
            response_time = capabilities.get("access_response_days", 30)
            if response_time > 30:
                findings.append(f"Access request response time ({response_time} days) exceeds 30-day limit")
                passed = False

        return {"passed": passed, "findings": findings}

    def verify_consent_management(self, consent_data: dict[str, Any]) -> dict[str, Any]:
        findings: list[str] = []
        passed = True

        if not consent_data.get("explicit_consent", False):
            findings.append("Explicit consent mechanism not implemented (GDPR Art. 7)")
            passed = False

        if not consent_data.get("withdrawal_mechanism", False):
            findings.append("Consent withdrawal mechanism not implemented (GDPR Art. 7(3))")
            passed = False

        if not consent_data.get("recorded_consent", False):
            findings.append("Consent records not maintained (GDPR Art. 7(1))")
            passed = False

        if consent_data.get("pre_checked", False):
            findings.append("Pre-checked consent boxes are not valid under GDPR (Art. 7)")
            passed = False

        if consent_data.get("bundled_consent", False):
            findings.append("Consent is bundled with other purposes (not specific per purpose)")
            passed = False

        return {"passed": passed, "findings": findings}

    def perform_dpia(self, processing_activity: dict[str, Any]) -> dict[str, Any]:
        dpia_result = {
            "dpia_required": False,
            "risk_level": "LOW",
            "mitigations": [],
            "status": "NOT_REQUIRED",
        }

        high_risk_indicators = [
            "health_data" in str(processing_activity).lower(),
            "biometric" in str(processing_activity).lower(),
            "genetic" in str(processing_activity).lower(),
            "criminal" in str(processing_activity).lower(),
            "children" in str(processing_activity).lower(),
            "profiling" in str(processing_activity).lower(),
            "large_scale" in str(processing_activity).lower(),
            "systematic_monitoring" in str(processing_activity).lower(),
            "vulnerable" in str(processing_activity).lower(),
        ]

        if any(high_risk_indicators):
            dpia_result["dpia_required"] = True
            dpia_result["risk_level"] = "HIGH"
            dpia_result["status"] = "REQUIRED"
            dpia_result["mitigations"] = [
                "Implement data minimization measures",
                "Ensure encryption at rest and in transit",
                "Implement strict access controls",
                "Conduct privacy review",
            ]

        dpia_record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "activity": processing_activity,
            "result": dpia_result,
        }
        self._dpia_records.append(dpia_record)

        return dpia_result

    def verify_breach_notification(self, breach_details: dict[str, Any]) -> dict[str, Any]:
        findings: list[str] = []
        passed = True

        has_dpa_notification = breach_details.get("notified_supervisory_authority", False)
        notification_hours = breach_details.get("notification_hours", 0)

        if not has_dpa_notification:
            findings.append("Supervisory authority not notified of breach (GDPR Art. 33)")
            passed = False
        elif notification_hours > 72:
            findings.append(f"Breach notification took {notification_hours}h (max 72h under GDPR Art. 33)")
            passed = False

        has_data_subject_notification = breach_details.get("notified_data_subjects", False)
        likely_risk = breach_details.get("high_risk_to_rights", False)

        if likely_risk and not has_data_subject_notification:
            findings.append("Data subjects not notified of high-risk breach (GDPR Art. 34)")
            passed = False

        breach_documented = breach_details.get("breach_documented", False)
        if not breach_documented:
            findings.append("Breach not documented - GDPR Art. 33(5) requires breach documentation")
            passed = False

        return {"passed": passed, "findings": findings}

    def verify_dpa_requirements(self, dpa_data: dict[str, Any]) -> dict[str, Any]:
        findings: list[str] = []
        passed = True

        required_elements = [
            "subject_matter", "duration", "nature_purpose", "data_types",
            "data_subject_categories", "controller_obligations", "processor_obligations",
            "security_measures", "subprocessing_rules", "data_breach_notification",
            "audit_rights", "return_destruction", "indemnification",
        ]

        for element in required_elements:
            if not dpa_data.get(element):
                findings.append(f"DPA missing required element: '{element}'")
                passed = False

        if dpa_data.get("international_transfer", False):
            if not dpa_data.get("transfer_safeguard"):
                findings.append("International transfer without adequate safeguards (Art. 44-49)")
                passed = False

        dpa_record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "data": dpa_data,
            "compliant": passed,
        }
        self._dpa_records.append(dpa_record)

        return {"passed": passed, "findings": findings}

    def check_international_transfers(self, transfer_data: dict[str, list[str]]) -> dict[str, Any]:
        findings: list[str] = []
        passed = True

        adequacy_countries = ["EU/EEA", "United Kingdom", "Argentina", "Canada", "Japan",
                              "South Korea", "New Zealand", "Switzerland", "Uruguay",
                              "Israel", "Andorra", "Faroe Islands", "Guernsey", "Isle of Man",
                              "Jersey", "United States (Privacy Shield alternative)"]

        for country, data_types in transfer_data.items():
            if country not in adequacy_countries:
                if not transfer_data.get(f"{country}_safeguard"):
                    findings.append(f"Transfer to {country} without adequacy decision or safeguards (Art. 44-49)")
                    passed = False
                if not transfer_data.get("bcr", False) and not transfer_data.get("scc", False):
                    findings.append(f"Transfer to {country} without BCRs or SCCs")
                    passed = False

        return {"passed": passed, "findings": findings}

    def verify_data_retention(self, retention_policies: dict[str, int]) -> dict[str, Any]:
        findings: list[str] = []
        passed = True

        for data_type, retention_days in retention_policies.items():
            if retention_days <= 0:
                findings.append(f"'{data_type}' has no retention period set")
                passed = False
            elif retention_days > 3650:
                findings.append(f"'{data_type}' retention ({retention_days}d) seems excessive - verify necessity")
                passed = False

        return {"passed": passed, "findings": findings}

    def generate_report(self) -> ComplianceReport:
        controls = list(self._controls.values())
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
            framework=ComplianceFramework.GDPR,
            overall_status=overall,
            control_count=total,
            passed=passed,
            failed=failed,
            not_applicable=sum(1 for c in controls if c.implementation_status == ControlStatus.NOT_APPLICABLE),
            findings=not_implemented[:50],
            remediation_plan=remediation,
        )
