from __future__ import annotations

from .dimensions.accessibility import AccessibilityEvaluator
from .dimensions.api_compatibility import APICompatibilityEvaluator
from .dimensions.architecture import ArchitectureEvaluator
from .dimensions.code_quality import CodeQualityEvaluator
from .dimensions.db_integrity import DBIntegrityEvaluator
from .dimensions.documentation import DocumentationEvaluator
from .dimensions.fhir_compliance import FHIRComplianceEvaluator
from .dimensions.maintainability import MaintainabilityEvaluator
from .dimensions.offline import OfflineEvaluator
from .dimensions.performance import PerformanceEvaluator
from .dimensions.reliability import ReliabilityEvaluator
from .dimensions.security import SecurityEvaluator
from .dimensions.test_coverage import TestCoverageEvaluator
from .engine import CertificationEngine
from .enums import CertificationDimension, CertificationLevel, MetricCategory, ReleaseGate
from .metrics import MetricsCollector
from .release_gates import ReleaseGateChecker
from .report import CertificationReport

__all__ = [
    "APICompatibilityEvaluator",
    "AccessibilityEvaluator",
    "ArchitectureEvaluator",
    "CertificationDimension",
    "CertificationEngine",
    "CertificationLevel",
    "CertificationReport",
    "CodeQualityEvaluator",
    "DBIntegrityEvaluator",
    "DocumentationEvaluator",
    "FHIRComplianceEvaluator",
    "MaintainabilityEvaluator",
    "MetricCategory",
    "MetricsCollector",
    "OfflineEvaluator",
    "PerformanceEvaluator",
    "ReleaseGate",
    "ReleaseGateChecker",
    "ReliabilityEvaluator",
    "SecurityEvaluator",
    "TestCoverageEvaluator",
]

_EVALUATOR_MAP: dict[CertificationDimension, type] = {
    CertificationDimension.ARCHITECTURE: ArchitectureEvaluator,
    CertificationDimension.SECURITY: SecurityEvaluator,
    CertificationDimension.PERFORMANCE: PerformanceEvaluator,
    CertificationDimension.ACCESSIBILITY: AccessibilityEvaluator,
    CertificationDimension.FHIR_COMPLIANCE: FHIRComplianceEvaluator,
    CertificationDimension.OFFLINE: OfflineEvaluator,
    CertificationDimension.RELIABILITY: ReliabilityEvaluator,
    CertificationDimension.MAINTAINABILITY: MaintainabilityEvaluator,
    CertificationDimension.TEST_COVERAGE: TestCoverageEvaluator,
    CertificationDimension.DOCUMENTATION: DocumentationEvaluator,
    CertificationDimension.CODE_QUALITY: CodeQualityEvaluator,
    CertificationDimension.API_COMPATIBILITY: APICompatibilityEvaluator,
    CertificationDimension.DB_INTEGRITY: DBIntegrityEvaluator,
}
