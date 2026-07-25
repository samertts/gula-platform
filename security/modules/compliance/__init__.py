GSF-007: Compliance Module — Compliance framework mapping.

Maps GSF security controls to multiple regulatory frameworks and
standards including OWASP ASVS Level 3, NIST CSF 2.0, NIST SP 800-53,
ISO 27001:2022, ISO 27799, HIPAA Security Rule, GDPR, and Iraqi
national healthcare regulations. Provides compliance reporting and
continuous monitoring.

Exports:
    ComplianceEngine: Compliance assessment engine
    FrameworkMapper: Multi-framework control mapping
    ControlEvaluator: Security control effectiveness evaluation
    ComplianceReport: Compliance report generator
    EvidenceCollector: Automated evidence collection
    GapAnalysis: Compliance gap identification
"""

from security.modules.compliance.engine import ComplianceEngine
from security.modules.compliance.mapper import FrameworkMapper
from security.modules.compliance.evaluator import ControlEvaluator
from security.modules.compliance.reporting import ComplianceReport
from security.modules.compliance.evidence import EvidenceCollector
from security.modules.compliance.gaps import GapAnalysis

__all__ = [
    "ComplianceEngine",
    "FrameworkMapper",
    "ControlEvaluator",
    "ComplianceReport",
    "EvidenceCollector",
    "GapAnalysis",
]
