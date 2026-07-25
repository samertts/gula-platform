from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DependencyVulnerability(BaseModel):
    id: str = ""
    package: str
    version: str
    severity: str = "UNKNOWN"
    cvss_score: float = 0.0
    cve_id: str = ""
    fix_version: str | None = None
    advisory_url: str | None = None
    published_date: datetime | None = None
    exploitability: str = "UNKNOWN"


class SBOMComponent(BaseModel):
    name: str
    version: str
    supplier: str | None = None
    purl: str | None = None
    license: str | None = None
    sha256: str | None = None
    originator: str | None = None


class SupplyChainPolicy(BaseModel):
    allowed_licenses: list[str] = Field(default_factory=lambda: [
        "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC",
        "CC0-1.0", "Unlicense", "Python-2.0", "MPL-2.0",
    ])
    blocked_packages: list[str] = Field(default_factory=list)
    max_critical_vulns: int = 0
    require_sbom: bool = True
    require_signatures: bool = False
    allowed_registries: list[str] = Field(default_factory=lambda: [
        "pypi.org", "npmjs.com", "registry.npmjs.org", "rubygems.org",
        "crates.io", "nuget.org", "packagist.org", "repo1.maven.org",
    ])


class SecurityScorecardEntry(BaseModel):
    date: datetime = Field(default_factory=datetime.utcnow)
    score: float = 0.0
    category_scores: dict[str, float] = Field(default_factory=dict)
    findings: list[str] = Field(default_factory=list)
