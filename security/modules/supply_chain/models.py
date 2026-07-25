from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DependencyVulnerability(BaseModel):
    id: str = ""
    package: str
    version: str
    severity: str = "UNKNOWN"
    cvss_score: float = 0.0
    cve_id: str = ""
    fix_version: Optional[str] = None
    advisory_url: Optional[str] = None
    published_date: Optional[datetime] = None
    exploitability: str = "UNKNOWN"


class SBOMComponent(BaseModel):
    name: str
    version: str
    supplier: Optional[str] = None
    purl: Optional[str] = None
    license: Optional[str] = None
    sha256: Optional[str] = None
    originator: Optional[str] = None


class SupplyChainPolicy(BaseModel):
    allowed_licenses: List[str] = Field(default_factory=lambda: [
        "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC",
        "CC0-1.0", "Unlicense", "Python-2.0", "MPL-2.0",
    ])
    blocked_packages: List[str] = Field(default_factory=list)
    max_critical_vulns: int = 0
    require_sbom: bool = True
    require_signatures: bool = False
    allowed_registries: List[str] = Field(default_factory=lambda: [
        "pypi.org", "npmjs.com", "registry.npmjs.org", "rubygems.org",
        "crates.io", "nuget.org", "packagist.org", "repo1.maven.org",
    ])


class SecurityScorecardEntry(BaseModel):
    date: datetime = Field(default_factory=datetime.utcnow)
    score: float = 0.0
    category_scores: Dict[str, float] = Field(default_factory=dict)
    findings: List[str] = Field(default_factory=list)
