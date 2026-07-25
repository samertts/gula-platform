# GSF Scripts

## Overview

Operational scripts for the GULA Security Framework (GSF). Each script is
production-ready with proper error handling, logging, and documentation.

## Script Index

| Script | Type | Purpose |
|--------|------|---------|
| `scan-secrets.sh` | Bash | Scan repository for leaked secrets (gitleaks + Python fallback) |
| `rotate-secrets.py` | Python | Automate secret rotation across backends |
| `security-scan.sh` | Bash | Comprehensive multi-tool security scan with SARIF output |
| `audit-log-verify.py` | Python | Verify immutable audit log hash chain integrity |
| `generate-sbom.sh` | Bash | Generate CycloneDX/SPDX SBOMs with Cosign signing |
| `rotate-keys.py` | Python | Rotate cryptographic keys with re-encryption |
| `incident-response.py` | Python | Automated incident response workflow |
| `validate-compliance.py` | Python | Multi-framework compliance validation |
| `health-check.sh` | Bash | Security subsystem health check with scoring |
| `enforce-policies.sh` | Bash | Policy enforcement (pre-commit/CI) |

## Usage

All scripts support `--help` or `-h`:

```bash
./scripts/scan-secrets.sh --help
./scripts/rotate-secrets.py --help
```

## Requirements

- Python 3.12+
- Bash 4.0+
- Optional tools: gitleaks, bandit, semgrep, trivy, checkov, syft, cosign
