# Security Assessment

## Scope
Authentication, authorisation (RBAC), encryption, audit logging, rate limiting, firewall, secrets management.

## Contents
- `auth-audit.md` — JWT, password hashing, token lifecycle
- `rbac-audit.md` — Role and permission matrix verification
- `encryption-audit.md` — AES-256 at rest, key management
- `audit-integrity.md` — Audit log hash chain verification
- `rate-limiting.md` — Rate limiter coverage and effectiveness
- `secrets-audit.md` — Secrets management (env vars, no hardcoded secrets)
- `bandit-report.md` — Bandit SAST scan results
- `recommendations.md` — Security improvement recommendations
