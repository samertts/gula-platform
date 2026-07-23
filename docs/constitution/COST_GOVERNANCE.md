# Cost Governance Constitution

**Version:** 1.0.0
**Date:** 2026-07-23
**Authority:** Platform Constitution — Article 15 (Cost Governance)
**Status:** ADOPTED — FROZEN — PERMANENT

---

## Preamble

This document establishes the Cost Governance framework for the GULA National
Digital Health Platform. Every implementation MUST optimize for lowest cost,
lowest maintenance, highest sovereignty, highest portability, highest reusability,
and highest independence. Commercial expenditures MUST be justified, documented,
and approved before introduction.

---

## Article 1: Free First

### Section 1.1 — Mandate

Every implementation MUST always search for a FREE solution first.

### Section 1.2 — Commercial Prohibition

Commercial solutions are prohibited unless:

1. No production-grade free solution exists
2. The free solution cannot satisfy mandatory requirements
3. Both conditions are documented and approved

### Section 1.3 — Evidence Requirement

The search for free alternatives MUST be documented in the implementation record.
At minimum:
- 3 free alternatives evaluated
- Reason each was unsuitable
- Cost comparison showing paid vs free TCO over 3 years

---

## Article 2: Open Source First

### Section 2.1 — Priority Order

| Priority | License Type | Examples |
|----------|-------------|----------|
| 1 | Apache 2.0 | Kubernetes, Hadoop, Kafka |
| 2 | MIT | React, Node.js, Express |
| 3 | BSD | PostgreSQL, Redis, Nginx |
| 4 | MPL | Mozilla tools, some libraries |
| 5 | GPL-compatible | Linux, Git, WordPress |
| 6 | Self-hosted community | Self-managed infrastructure |
| 7 | Commercial | Last resort only |

### Section 2.2 — Commercial Approval Gate

Commercial products require:
- Architecture Decision Record
- Technical justification
- Cost analysis (licensing + TCO)
- Free alternative comparison
- Migration strategy
- Security review
- Engineering Lead approval

---

## Article 3: Self-Hosted First

### Section 3.1 — Mandate

Whenever technically feasible, the platform SHALL use self-hosted infrastructure
instead of hosted SaaS.

### Section 3.2 — Approved Self-Hosted Technologies

| Category | Technology | Purpose |
|----------|-----------|---------|
| Database | PostgreSQL | Primary data store |
| Cache | Redis | In-memory cache, sessions |
| Storage | MinIO | S3-compatible object storage |
| Monitoring | Grafana | Visualization |
| Metrics | Prometheus | Time-series metrics |
| Logging | Loki | Log aggregation |
| Tracing | Tempo | Distributed tracing |
| Tracing | Jaeger | Distributed tracing (alt) |
| Messaging | RabbitMQ | Message broker |
| Messaging | NATS | Lightweight messaging |
| Search | OpenSearch | Full-text search |
| Vector DB | Qdrant | Vector embeddings |
| Vector DB | ChromaDB | Lightweight vector store |
| Vector DB | Milvus | Large-scale vector store |
| AI Inference | Ollama | Local LLM inference |
| Proxy | Traefik | Reverse proxy |
| Proxy | Nginx | Web server, reverse proxy |
| Secrets | Vault Community | Secrets management |
| Auth | Keycloak | Identity & access |
| Auth | Authentik | Identity platform |
| Email | Mail Server | Self-hosted email |
| CDN | Object Storage + Nginx | Static asset delivery |

### Section 3.3 — SaaS Exception

SaaS is permitted only when:
- Self-hosted option requires >2 FTE to maintain
- Self-hosted option has higher TCO over 3 years
- SaaS offers compliance certification unavailable self-hosted
- Exception documented in ADR

---

## Article 4: Reuse Before Build

### Section 4.1 — Mandate

Before writing any code:
1. Search existing codebase
2. Search shared modules
3. Search platform services
4. Search previous implementations
5. Search reusable libraries
6. Search open-source ecosystem

### Section 4.2 — Prohibition

Never duplicate functionality that already exists in the platform or available
as open-source software.

### Section 4.3 — Reuse Audit

Every PR MUST include a statement confirming reuse was evaluated. CI MUST
fail if new code duplicates existing functionality.

---

## Article 5: Zero Paid Dependency

### Section 5.1 — General Rule

Paid software SHALL NOT be introduced unless ALL of the following are documented:
- Technical reason
- Annual cost
- Free alternative(s) evaluated
- Migration strategy (to free alternative)
- Risk assessment
- Engineering Lead approval

### Section 5.2 — Approval Requirements

| Cost Threshold | Approval Required |
|----------------|-------------------|
| $0/mo | No approval needed |
| $1-$100/mo | Tech Lead |
| $101-$1000/mo | Engineering Lead |
| $1001+/mo | Architecture Review Board |

---

## Article 6: No Vendor Lock-In

### Section 6.1 — Abstraction Mandate

Every dependency MUST have an abstraction layer. The platform must never be
coupled to:
- AWS
- Azure
- Google Cloud
- Firebase
- Supabase
- Auth0
- Okla
- Any commercial vendor

### Section 6.2 — Replaceability

Every component MUST be replaceable with a different implementation without
affecting the rest of the system. Abstraction layers MUST be:
- Interface-based (not concrete class dependencies)
- Testable with mocks
- Documented with replacement guide

### Section 6.3 — Prohibited Patterns

- Direct SDK usage without abstraction
- Vendor-specific annotations throughout codebase
- Hardcoded vendor endpoints
- Vendor-specific data formats in core domain

---

## Article 7: Free Cloud First

### Section 7.1 — Priority

When cloud resources are required, use free plans first:

| Provider | Free Tier | Best For |
|----------|-----------|----------|
| Cloudflare | Free | CDN, DNS, DDoS, Workers, R2 (10GB) |
| GitHub | Free | Repositories, Actions (2000 min/mo) |
| Let's Encrypt | Free | TLS certificates |
| Vercel | Hobby | Frontend hosting |
| Netlify | Free | Static sites |
| Render | Free | Web services |
| HuggingFace | Free | Model hosting |
| Google Colab | Free | Notebooks, training |
| Oracle Cloud | Free | Always-free VPS |

### Section 7.2 — Paid Cloud Approval

Paid cloud resources require:
- Free tier exhaustion documented
- Cost projection
- Exit strategy
- Engineering Lead approval

---

## Article 8: Local AI First

### Section 8.1 — Priority

AI inference priority:
1. Existing local model
2. Ollama (self-hosted)
3. Open-weight models
4. Self-hosted inference (TGI, vLLM)
5. Free API (HuggingFace, Google Colab)
6. Commercial API (last resort)

### Section 8.2 — Commercial AI Prohibition

Commercial AI APIs (OpenAI, Anthropic, Google AI, etc.) require:
- Security review (data may leave jurisdiction)
- Cost analysis
- Privacy impact assessment
- Engineering Lead approval

---

## Article 9: Local Storage First

### Section 9.1 — Priority

Priority:
1. PostgreSQL
2. MinIO (self-hosted S3)
3. Redis
4. Filesystem
5. Cloud Storage (last resort)

### Section 9.2 — Cloud Storage Exception

Cloud storage only when:
- Self-hosted infrastructure unavailable
- Geographic redundancy required by regulation
- Disaster recovery requirements exceed self-hosted capacity

---

## Article 10: Free Security First

### Section 10.1 — Mandated Free Security Tools

| Category | Tool | Purpose |
|----------|------|---------|
| TLS | OpenSSL | Certificate management |
| CA | Let's Encrypt | Automated certificates |
| VPN | WireGuard | Secure networking |
| IDS | Fail2Ban | Intrusion prevention |
| IDS | CrowdSec | Collaborative security |
| Secrets | Vault Community | Secret management |
| Auth | Authentik | Identity provider |
| Auth | Keycloak | Identity & access management |
| Tracing | OpenTelemetry | Observability |

### Section 10.2 — Commercial Security Prohibition

Commercial security products are prohibited unless:
- No free alternative exists for the specific use case
- Regulatory compliance requires specific commercial tooling
- Approved by Security Lead + Engineering Lead

---

## Article 11: Architecture Decision Records

Every ADR MUST contain:
1. Open Source alternatives considered
2. Free alternatives considered
3. Commercial alternatives considered
4. Chosen option with rationale
5. Cost analysis (licensing + TCO over 3 years)
6. Migration plan to free/open-source alternative
7. Vendor lock-in risk assessment

---

## Article 12: Dependency Review

Every new dependency MUST document:
1. Purpose
2. License (must be OSI-approved)
3. Maintenance status (updated in last 6 months)
4. Community activity (stars, contributors, forks)
5. Security history (CVEs, response time)
6. Open source alternative (if not itself open source)
7. Removal strategy (if needed in future)

---

## Article 13: CI Enforcement

### Section 13.1 — Automated Rules

CI MUST:
1. Reject PRs introducing paid dependencies without approval
2. Detect vendor lock-in patterns
3. Detect duplicate libraries
4. Reject commercial SDKs used directly (without abstraction)

### Section 13.2 — Compliance Check

A constitutional compliance check runs on every PR and blocks merge on
any violation.

---

## Article 14: AI Agent Enforcement

Every AI Agent MUST:
1. Assume this policy is always in effect
2. Never recommend commercial software before evaluating free alternatives
3. Never introduce vendor lock-in
4. Always justify external dependencies
5. Report compliance status with every recommendation

---

## Article 15: Cost Optimization Priorities

| Priority | Area | Target |
|----------|------|--------|
| 1 | Infrastructure | Zero paid hosting |
| 2 | Database | PostgreSQL only |
| 3 | Storage | MinIO or filesystem |
| 4 | Monitoring | Prometheus + Grafana (self-hosted) |
| 5 | AI | Ollama / open-weight models |
| 6 | Auth | Keycloak / Authentik |
| 7 | CDN | Cloudflare Free |
| 8 | CI/CD | GitHub Actions Free |
| 9 | Secrets | Vault Community |
| 10 | Email | Self-hosted mail server |

---

## Article 16: Platform Sovereignty

The platform SHALL remain deployable using only:
- Linux
- Docker
- Kubernetes (optional)
- Open Source Software
- Community Editions

without requiring any commercial subscriptions.

---

## Enforcement

This policy is enforced by:
1. **Automated CI checks** — every PR validated
2. **Architecture review** — every ADR includes cost/open-source section
3. **Startup guard** — system verifies compliance on boot
4. **Quarterly audit** — dependency review against this policy
5. **AI agent rules** — all AI assistants enforce this policy automatically

---

## Violations

Violation of this Cost Governance Constitution is an Architecture Violation.
Consequences:
1. PR rejection (automated CI)
2. Architecture review board notification
3. Remediation plan required within 7 days
4. Escalation to Engineering Lead if unresolved

---

## References

- `PLATFORM-CONSTITUTION.md` — Supreme platform authority
- `ENGINEERING_CONSTITUTION.md` — Engineering governance
- `docs/architecture/FREE_FIRST_POLICY.md` — Free First policy
- `docs/architecture/OPEN_SOURCE_POLICY.md` — Open Source policy
- `docs/architecture/VENDOR_LOCK_IN_POLICY.md` — Vendor lock-in policy
- `docs/architecture/DEPENDENCY_APPROVAL_POLICY.md` — Dependency approval policy
