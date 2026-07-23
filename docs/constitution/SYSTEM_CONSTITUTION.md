# System Constitution — PROGRAM-CONSTITUTION-001

**Version:** 1.0.0
**Date:** 2026-07-23
**Classification:** SUPREME — Permanent Amendment
**Status:** FROZEN — IMMUTABLE — PERMANENT

---

## Amendment Preamble

This document is a permanent amendment to the GULA Platform Constitution
(the "Platform Constitution"). It carries the same authority as the
PLATFORM-CONSTITUTION.md and ENGINEERING_CONSTITUTION.md.

This amendment establishes the **Free First, Open Source First, Sovereign First,
and Cost Governance** principles as immutable platform rules.

**This policy NEVER expires. No future implementation may ignore it.**
Even if future prompts do not mention this policy, the platform MUST continue
enforcing it.

---

## Article 1: Free First

Every implementation MUST search for a FREE solution before any paid alternative.
Commercial solutions are prohibited unless:
- No production-grade free solution exists
- AND the free solution cannot satisfy mandatory requirements

Full policy: `docs/architecture/FREE_FIRST_POLICY.md`

---

## Article 2: Open Source First

Open Source software SHALL always be preferred over proprietary.
Priority: Apache > MIT > BSD > MPL > GPL-compatible > Self-hosted > Commercial.
Commercial products are the final option.

Full policy: `docs/architecture/OPEN_SOURCE_POLICY.md`

---

## Article 3: Self-Hosted First

Self-hosted infrastructure SHALL be used instead of hosted SaaS whenever
technically feasible. Approved self-hosted technologies include PostgreSQL,
Redis, MinIO, Grafana, Prometheus, Loki, Tempo, Jaeger, RabbitMQ, NATS,
OpenSearch, Qdrant, ChromaDB, Milvus, Ollama, Traefik, Nginx, Vault Community,
Keycloak, and Authentik.

---

## Article 4: Reuse Before Build

Before writing any code: search existing code, shared modules, platform services,
previous implementations, and reusable libraries. Never duplicate functionality.

---

## Article 5: Zero Paid Dependency

Paid software SHALL NOT be introduced unless documented with: technical reason,
cost, free alternative, migration strategy, risk, and approval.

---

## Article 6: No Vendor Lock-In

Every component MUST be replaceable. The platform MUST NOT be coupled to AWS,
Azure, Google Cloud, Firebase, Supabase, Auth0, Okta, or any commercial vendor.
Every dependency MUST have an abstraction layer.

Full policy: `docs/architecture/VENDOR_LOCK_IN_POLICY.md`

---

## Article 7: Free Cloud First

When cloud resources are required, use free plans first: Cloudflare Free,
GitHub, GitHub Actions, Let's Encrypt, Vercel Hobby, Netlify Free, Render Free,
HuggingFace Free, Google Colab Free, Oracle Cloud Free. Paid cloud resources
only after free tiers are exhausted.

---

## Article 8: Local AI First

AI inference priority: existing local model > Ollama > open-weight models >
self-hosted inference > free API > commercial API.

---

## Article 9: Local Storage First

Priority: PostgreSQL > MinIO > Redis > Filesystem > Cloud Storage.

---

## Article 10: Free Security First

Use OpenSSL, Let's Encrypt, WireGuard, Fail2Ban, CrowdSec, Vault Community,
Authentik, Keycloak, OpenTelemetry before commercial security products.

---

## Article 11: Architecture Review

Every ADR MUST contain: Open Source alternatives, Free alternatives, Commercial
alternatives, Chosen option, Reason, Cost, and Migration Plan.

---

## Article 12: Dependency Review

Every new dependency MUST include: Purpose, License, Maintenance Status,
Community Activity, Security History, Open Source Alternative, and Removal Strategy.

Full policy: `docs/architecture/DEPENDENCY_APPROVAL_POLICY.md`

---

## Article 13: CI Enforcement

CI MUST reject PRs that:
1. Introduce paid dependency without approval
2. Create vendor lock-in
3. Duplicate existing library
4. Use commercial SDK directly (without abstraction)

---

## Article 14: AI Agent Enforcement

Every AI Agent MUST assume this policy automatically. Never recommend commercial
software before evaluating free alternatives. Never introduce vendor lock-in.
Always justify external dependencies.

---

## Article 15: Cost Governance

Every implementation optimizes for: lowest cost, lowest maintenance, highest
sovereignty, highest portability, highest reusability, highest independence.

Full policy: `docs/constitution/COST_GOVERNANCE.md`

---

## Article 16: Platform Sovereignty

The platform SHALL remain deployable using only: Linux, Docker, Kubernetes,
Open Source Software, and Community Editions — without commercial subscriptions.

---

## Article 17: Permanent Rule

This Constitution Article becomes permanent. Future prompts do not need to
repeat it. Every implementation MUST automatically enforce it.

Violation of this policy is considered an Architecture Violation. The AI
must stop and report the violation before continuing.

---

## Enforcement Mechanisms

| Layer | Mechanism | Scope |
|-------|-----------|-------|
| AI Agents | Automatic policy enforcement | All code generation |
| CI/CD | Automated compliance checks | All PRs |
| Architecture Review | ADR compliance review | All decisions |
| Startup Guard | Boot-time constitutional validation | All deployments |
| Quality Gates | `make constitution-check` | Local development |

---

## References

- `CLAUDE.md` — Developer guidance (includes constitution summary)
- `AGENTS.md` — AI agent enforcement rules
- `CODEX.md` — Codex-specific constitution guidance
- `COPILOT.md` — Copilot-specific constitution guidance
- `docs/constitution/COST_GOVERNANCE.md` — Full Cost Governance policy
- `docs/architecture/FREE_FIRST_POLICY.md` — Free First policy
- `docs/architecture/OPEN_SOURCE_POLICY.md` — Open Source policy
- `docs/architecture/VENDOR_LOCK_IN_POLICY.md` — Vendor lock-in policy
- `docs/architecture/DEPENDENCY_APPROVAL_POLICY.md` — Dependency approval policy
- `PLATFORM-CONSTITUTION.md` — Supreme platform constitution
- `ENGINEERING_CONSTITUTION.md` — Engineering governance
