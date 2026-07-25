"""
GSF-007: Supply Chain Security Module — Dependency scanning and code analysis.

Provides comprehensive supply chain security including SBOM generation,
vulnerability scanning, code quality analysis, dependency review,
and OpenSSF Scorecard integration.

Note: The directory is `supply-chain/` but Python imports use `supply_chain`.

Exports:
    DependencyVulnerability: Dependency vulnerability model
    SBOMComponent: SBOM component model
    SupplyChainPolicy: Supply chain security policy
    SecurityScorecardEntry: OpenSSF scorecard entry
    SupplyChainScanner: SBOM and vulnerability scanning
    CodeScanner: SAST/DAST code scanning
    DependencyReviewer: Dependency review and audit
"""

from security.modules.supply_chain.models import (
    DependencyVulnerability,
    SBOMComponent,
    SupplyChainPolicy,
    SecurityScorecardEntry,
)
from security.modules.supply_chain.scanner import SupplyChainScanner
from security.modules.supply_chain.code_scanning import CodeScanner
from security.modules.supply_chain.dependency_review import DependencyReviewer

__all__ = [
    "DependencyVulnerability",
    "SBOMComponent",
    "SupplyChainPolicy",
    "SecurityScorecardEntry",
    "SupplyChainScanner",
    "CodeScanner",
    "DependencyReviewer",
]
