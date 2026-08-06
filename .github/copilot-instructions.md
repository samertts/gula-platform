# GitHub Copilot Instructions — GULA Platform

> **AUTHORITY:** The supreme AI constitution is `AI_OPERATING_CONSTITUTION.md`.
> All rules below are summaries. The constitution is the single source of truth.
> If any conflict exists, the constitution wins.

## Permanent Platform Constitution (PROGRAM-CONSTITUTION-001)

### Free First
- Always prefer free/open-source solutions over paid
- Never generate code with vendor-specific SDKs in core domain
- Always propose abstraction layers for external services

### Open Source First
- License priority: Apache 2.0 > MIT > BSD > MPL > GPL
- Before suggesting a commercial library, search for open-source alternative

### Self-Hosted First
- Prefer PostgreSQL, Redis, MinIO over cloud-managed services
- Prefer self-hosted monitoring (Prometheus/Grafana) over SaaS

### No Vendor Lock-In
- Generate abstraction interfaces for all external services
- Never hardcode vendor endpoints or credentials
- Always provide at least 2 implementations (primary + fallback)

### Reuse Before Build
- Before generating new code, check if the platform already has it
- Reference existing modules and services

### Local AI First
- Prefer Ollama/local models for AI features
- Commercial AI APIs require data sovereignty review

## Enforcement
If a suggestion would violate these rules:
1. Explain the violation
2. Propose a compliant alternative
3. Not generate the violating code

## References
- `AI_OPERATING_CONSTITUTION.md` (supreme authority)
- `docs/constitution/COST_GOVERNANCE.md`
- `AGENTS.md` (detailed engineering rules)
- `CLAUDE.md` (full AI operating manual)
