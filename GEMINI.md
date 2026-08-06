# Gemini Guidance — GULA Platform

> **AUTHORITY:** The supreme AI constitution is `AI_OPERATING_CONSTITUTION.md`.
> All rules below are summaries. The constitution is the single source of truth.
> If any conflict exists, the constitution wins. See Section 1.4 for precedence.

## Permanent Platform Constitution (PROGRAM-CONSTITUTION-001)

### Free First
- Search for FREE solution before any paid alternative
- Commercial solutions require documented exception

### Open Source First
- License priority: Apache 2.0 > MIT > BSD > MPL > GPL
- Commercial products are the final option

### Self-Hosted First
- PostgreSQL, Redis, MinIO, Grafana, Prometheus before SaaS
- Commercial SaaS requires architecture review

### No Vendor Lock-In
- Every component MUST have an abstraction layer
- Never couple to AWS, Azure, GCP, Firebase, Auth0, etc.

### Zero Paid Dependency
- Paid dependencies require: reason, cost, free alternative, migration plan

### Reuse Before Build
- Search existing codebase before writing new code
- Never duplicate existing functionality

### Local AI First
- Priority: local model > Ollama > open-weight > free API > commercial API

### Free Security First
- OpenSSL, Let's Encrypt, WireGuard, Fail2Ban, CrowdSec before commercial

## Enforcement
If a suggestion would violate these rules:
1. Explain the violation
2. Propose a compliant alternative
3. Not generate the violating code

## References
- `AI_OPERATING_CONSTITUTION.md` (supreme authority)
- `docs/constitution/COST_GOVERNANCE.md`
- `docs/architecture/FREE_FIRST_POLICY.md`
- `docs/architecture/OPEN_SOURCE_POLICY.md`
