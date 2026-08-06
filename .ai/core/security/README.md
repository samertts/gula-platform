---
id: SEC-000001
type: security
title: "Security Knowledge Bridge"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [security, bridge, index]
---

# Security Knowledge — Bridge Reference

## Security Constitution
- `docs/constitution/08_SECURITY_CONSTITUTION.md` — Security law
- `docs/constitution/11_AI_CONSTITUTION.md` — AI security rules

## Security Policies
- `docs/security/secret_management.md` — Secret handling
- `docs/security/secret_rotation_plan.md` — Rotation schedule
- `docs/security/repository_security.md` — Repo security
- `docs/security/public_repository_policy.md` — Public repo rules
- `docs/security/security_baseline.md` — Baseline config

## Security Architecture
- `docs/architecture/security-platform.md` — Security platform design
- `docs/decisions/SECURITY_DECISIONS.md` — All security decisions (84KB)

## Security Tools
- bandit — Python SAST (in CI)
- trivy — Container scanning
- gitleaks — Secret detection (pre-commit)
- CodeQL — GitHub security analysis
- OpenSSF Scorecard — Supply chain security

## OWASP Compliance
- ASVS — Application Security Verification
- API Top 10 — API security
- Top 10 — Web application security

## Key Security Patterns
- Immutable audit log — append-only, ISO 15189
- RBAC + ABAC — role + attribute-based access
- JWT + Refresh tokens — stateless auth
- Fernet encryption — symmetric, at-rest
- Rate limiting — per-role API limits
- CORS strict — no wildcards in production

## Related
- `.ai/core/memory/PROJECT_MEMORY.md` — Security decisions
- `shared/security/` — Encryption module
- `backend/app/security/` — Auth, Redis, middleware
