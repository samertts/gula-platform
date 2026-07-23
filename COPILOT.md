# GitHub Copilot Guidance — GULA Platform

## Permanent Constitution Rules

These rules are ALWAYS in effect. Copilot MUST enforce them automatically.

### Cost Governance
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
If a suggestion would violate these rules, Copilot should:
1. Explain the violation
2. Propose a compliant alternative
3. Not generate the violating code

## References
`docs/constitution/COST_GOVERNANCE.md`
