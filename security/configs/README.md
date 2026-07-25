# GSF Configuration Files

## Overview

This directory contains the configuration files for the GULA Security Framework (GSF).
Each file governs a specific security domain and follows a structured YAML schema.

## Files

| File | Domain | Description |
|------|--------|-------------|
| `rotation.yaml` | Secret/Key Rotation | Secret and cryptographic key rotation schedules, backends, and validation |
| `security-headers.yaml` | HTTP Security Headers | CSP, HSTS, Permissions-Policy, CORS, CSRF configuration per environment |
| `scanning.yaml` | Security Scanning | SAST (bandit, semgrep, codeql), DAST, container (trivy), IaC (checkov), secrets (gitleaks), SBOM |
| `audit.yaml` | Audit Logging | Event retention, required audit events, alert rules, export schedules, immutable log |
| `threat-detection.yaml` | Threat Detection | Detection rules, severity thresholds, correlation rules, response actions, risk scoring |
| `compliance.yaml` | Compliance | Active frameworks (OWASP, NIST, ISO, HIPAA, GDPR, Iraqi), schedules, evidence requirements |
| `password-policy.yaml` | Password Policy | Complexity, expiration, history, lockout, MFA enforcement, session, API keys, breach detection |

## Usage

Configs are loaded by GSF modules and scripts at runtime:

```python
from security.modules.compliance import ComplianceEngine

engine = ComplianceEngine(config_path="security/configs/compliance.yaml")
```

## Schema Validation

All YAML files are validated against Pydantic models in the respective GSF modules.
Invalid configurations are rejected at load time with descriptive error messages.

## Environment Overrides

Some configs support environment-specific overrides (see `security-headers.yaml` for an example).
The active environment is determined by the `GULA_ENV` environment variable (default: `development`).
