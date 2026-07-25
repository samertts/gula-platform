from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from security.modules.compliance.models import (
    ComplianceControl,
    ComplianceFramework,
    ComplianceReport,
    ControlStatus,
)

logger = logging.getLogger(__name__)

CROSS_FRAMEWORK_MAPPINGS: Dict[str, Dict[str, List[str]]] = {
    "HIPAA-SEC-TEC-4": {
        "description": "Encryption and decryption of ePHI",
        "mappings": {
            "NIST_CSF": ["PR.DS-1", "PR.DS-2"],
            "ISO_27001": ["A.8.24"],
            "OWASP_ASVS": ["ASVS-6.4.1", "ASVS-6.4.2", "ASVS-9.1.1"],
            "GDPR": ["GDPR-ART-32"],
        },
    },
    "HIPAA-SEC-TEC-1": {
        "description": "Unique user identification",
        "mappings": {
            "NIST_CSF": ["PR.AC-1"],
            "ISO_27001": ["A.8.2", "A.8.3"],
            "OWASP_ASVS": ["ASVS-2.1.1", "ASVS-2.2.1"],
            "GDPR": ["GDPR-ART-5"],
        },
    },
    "HIPAA-SEC-ADM-1": {
        "description": "Risk analysis and management",
        "mappings": {
            "NIST_CSF": ["ID.RA-1", "ID.RA-2", "ID.RA-3"],
            "ISO_27001": ["A.5.22"],
            "OWASP_ASVS": ["ASVS-1.1.1", "ASVS-1.1.2"],
            "GDPR": ["GDPR-ART-32"],
        },
    },
}


class FrameworkMapping(BaseModel):
    from_framework: ComplianceFramework
    from_control: str
    to_framework: ComplianceFramework
    to_control: str
    confidence: float = 1.0
    description: str = ""


class MappedControl(BaseModel):
    original_id: str
    original_framework: ComplianceFramework
    mapped_ids: Dict[str, List[str]] = Field(default_factory=dict)


class ComplianceMapper:
    def __init__(self):
        self._mappings: Dict[str, FrameworkMapping] = {}
        self._initialize_mappings()

    def _initialize_mappings(self) -> None:
        for source_id, mapping_data in CROSS_FRAMEWORK_MAPPINGS.items():
            for target_framework_str, target_ids in mapping_data["mappings"].items():
                for target_id in target_ids:
                    try:
                        target_framework = ComplianceFramework(target_framework_str)
                    except ValueError:
                        continue
                    mapping = FrameworkMapping(
                        from_framework=ComplianceFramework.HIPAA,
                        from_control=source_id,
                        to_framework=target_framework,
                        to_control=target_id,
                        description=mapping_data["description"],
                    )
                    key = f"{source_id}->{target_framework_str}:{target_id}"
                    self._mappings[key] = mapping

    def add_mapping(self, from_framework: ComplianceFramework, from_control: str,
                     to_framework: ComplianceFramework, to_control: str,
                     confidence: float = 1.0, description: str = "") -> None:
        key = f"{from_control}->{to_framework.value}:{to_control}"
        self._mappings[key] = FrameworkMapping(
            from_framework=from_framework,
            from_control=from_control,
            to_framework=to_framework,
            to_control=to_control,
            confidence=confidence,
            description=description,
        )

    def find_equivalent_controls(self, control_id: str,
                                  source_framework: ComplianceFramework) -> List[FrameworkMapping]:
        results: List[FrameworkMapping] = []
        for mapping in self._mappings.values():
            if mapping.from_control == control_id and mapping.from_framework == source_framework:
                results.append(mapping)
            elif mapping.to_control == control_id and mapping.to_framework == source_framework:
                results.append(mapping)
        return results

    def get_mapped_controls(self, framework: ComplianceFramework) -> List[MappedControl]:
        mapped: Dict[str, MappedControl] = {}

        for mapping in self._mappings.values():
            if mapping.from_framework == framework:
                if mapping.from_control not in mapped:
                    mapped[mapping.from_control] = MappedControl(
                        original_id=mapping.from_control,
                        original_framework=framework,
                    )
                tf = mapping.to_framework.value
                if tf not in mapped[mapping.from_control].mapped_ids:
                    mapped[mapping.from_control].mapped_ids[tf] = []
                mapped[mapping.from_control].mapped_ids[tf].append(mapping.to_control)

        return list(mapped.values())

    def deduplicate_controls(self, controls: List[ComplianceControl]) -> List[ComplianceControl]:
        seen_descriptions: Set[str] = set()
        deduped: List[ComplianceControl] = []

        for control in controls:
            desc_key = control.description[:100].lower()
            if desc_key not in seen_descriptions:
                seen_descriptions.add(desc_key)
                deduped.append(control)

        return deduped

    def calculate_composite_score(self, reports: List[ComplianceReport]) -> Dict[str, Any]:
        if not reports:
            return {"composite_score": 0.0, "framework_scores": {}, "overall_status": "NO_DATA"}

        framework_scores = {}
        total_weighted = 0.0
        total_controls = 0

        for report in reports:
            if report.control_count > 0:
                score = report.passed / report.control_count
                weight = report.control_count
                framework_scores[report.framework.value] = {
                    "score": round(score * 100, 1),
                    "passed": report.passed,
                    "total": report.control_count,
                }
                total_weighted += score * weight
                total_controls += weight

        composite = total_weighted / max(total_controls, 1) * 100

        if composite >= 90:
            status = "COMPLIANT"
        elif composite >= 70:
            status = "PARTIALLY_COMPLIANT"
        elif composite > 0:
            status = "NON_COMPLIANT"
        else:
            status = "NO_DATA"

        return {
            "composite_score": round(composite, 1),
            "framework_scores": framework_scores,
            "overall_status": status,
            "frameworks_assessed": len(reports),
        }

    def generate_unified_report(self, reports: List[ComplianceReport]) -> Dict[str, Any]:
        composite = self.calculate_composite_score(reports)

        all_controls: List[ComplianceControl] = []
        for report in reports:
            all_controls.extend(report.findings)

        deduped = self.deduplicate_controls(all_controls)

        framework_coverage = {}
        for report in reports:
            framework_coverage[report.framework.value] = {
                "control_count": report.control_count,
                "passed": report.passed,
                "failed": report.failed,
                "overall_status": report.overall_status.value,
            }

        return {
            "report_generated": reports[0].generated_at.isoformat() if reports else "",
            "composite_score": composite,
            "frameworks_assessed": len(reports),
            "framework_coverage": framework_coverage,
            "total_unique_controls": len(deduped),
            "total_controls_with_duplicates": len(all_controls),
            "deduplication_savings": len(all_controls) - len(deduped),
            "critical_gaps": [
                c.control_id for c in deduped
                if c.implementation_status == ControlStatus.NOT_IMPLEMENTED
            ][:30],
        }

    def get_framework_view(self, reports: List[ComplianceReport],
                            framework: ComplianceFramework) -> ComplianceReport:
        for report in reports:
            if report.framework == framework:
                return report
        raise ValueError(f"No report found for framework: {framework}")

    def get_mapping_matrix(self) -> str:
        lines = [
            "Cross-Framework Control Mapping Matrix",
            "=" * 80,
            "",
            "Source Control | Mapped Frameworks",
            "-" * 80,
        ]

        for source_id, mapping_data in CROSS_FRAMEWORK_MAPPINGS.items():
            target_frameworks = ", ".join(mapping_data["mappings"].keys())
            target_controls = []
            for fw, ctrls in mapping_data["mappings"].items():
                target_controls.extend(ctrls)
            lines.append(f"{source_id} -> {', '.join(target_controls)}")
            lines.append(f"  Frameworks: {target_frameworks}")
            lines.append("")

        return "\n".join(lines)
