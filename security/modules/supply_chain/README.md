# GSF-007: Supply Chain Security Module

Comprehensive supply chain security including dependency scanning,
code analysis, and dependency review.

## Components

### SupplyChainScanner
- Syft SBOM generation (CycloneDX/SPDX)
- Grype vulnerability scanning
- Trivy container image scanning
- License compliance checking
- Report generation (JSON, CycloneDX, SPDX, SARIF, HTML)

### CodeScanner
- CodeQL query execution and result parsing
- Semgrep rule selection and processing
- Bandit Python SAST scanning
- Checkov IaC scanning
- Result aggregation and deduplication
- SARIF output and PR comment generation
- Quality gate evaluation

### DependencyReviewer
- Dependabot config validation and alert parsing
- New dependency review (license, malicious package detection)
- Transitive dependency analysis
- Malicious package detection (typosquatting, dependency confusion)
- Lockfile integrity validation (npm, yarn, poetry, pipenv)
- OpenSSF Scorecard integration
