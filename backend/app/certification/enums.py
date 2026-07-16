from __future__ import annotations

from app._compat import StrEnum


class CertificationLevel(StrEnum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


class CertificationDimension(StrEnum):
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ACCESSIBILITY = "accessibility"
    FHIR_COMPLIANCE = "fhir_compliance"
    OFFLINE = "offline"
    RELIABILITY = "reliability"
    MAINTAINABILITY = "maintainability"
    TEST_COVERAGE = "test_coverage"
    DOCUMENTATION = "documentation"
    CODE_QUALITY = "code_quality"
    API_COMPATIBILITY = "api_compatibility"
    DB_INTEGRITY = "db_integrity"


class MetricCategory(StrEnum):
    COVERAGE = "coverage"
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    TECH_DEBT = "tech_debt"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    AVAILABILITY = "availability"
    SCALABILITY = "scalability"
    DOCUMENTATION = "documentation"


class ReleaseGate(StrEnum):
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CLINICAL_SAFETY = "clinical_safety"
    DOCUMENTATION = "documentation"
    SBOM = "sbom"
    RISK_ASSESSMENT = "risk_assessment"
