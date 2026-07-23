# Free First Policy

**Version:** 1.0.0
**Date:** 2026-07-23
**Authority:** Platform Constitution Amendment — PROGRAM-CONSTITUTION-001, Article 1
**Status:** ADOPTED — FROZEN — PERMANENT

---

## Policy Statement

Every implementation in the GULA National Digital Health Platform MUST always
search for a FREE solution before considering any paid alternative.

Commercial solutions are STRICTLY PROHIBITED unless BOTH conditions are met:
1. No production-grade free solution exists
2. The free solution cannot satisfy mandatory requirements

---

## Scope

This policy applies to ALL decisions across:
- Infrastructure hosting
- Software dependencies
- Third-party services
- APIs and integrations
- Development tools
- Monitoring and observability
- Security tools
- AI/ML models and inference
- Storage solutions
- Any other technology decision

---

## Evaluation Process

### Step 1: Search Free Alternatives
Minimum 3 free alternatives MUST be evaluated for every technology decision.
Documentation of this search MUST be included in the implementation record.

### Step 2: Evaluate Against Requirements
Each free alternative MUST be evaluated against:
- Functional requirements (does it do the job?)
- Performance requirements (does it meet SLAs?)
- Security requirements (does it meet security standards?)
- Compliance requirements (does it satisfy regulations?)
- Maintenance requirements (can the team maintain it?)

### Step 3: Document Exceptions
If no free alternative satisfies all requirements, document:
1. Each free alternative evaluated
2. Reason each was unsuitable
3. Cost comparison: free vs paid TCO over 3 years
4. Migration strategy to free alternative (future)
5. Engineering Lead approval

### Step 4: Architecture Review
Any exception to Free First policy requires Architecture Review Board approval.

---

## Free Technology Catalog

### Infrastructure
| Need | Free Solution |
|------|---------------|
| Compute | Self-hosted Linux, Docker |
| Database | PostgreSQL |
| Cache | Redis |
| Object Storage | MinIO |
| Message Broker | RabbitMQ, NATS |
| Search | OpenSearch |
| Reverse Proxy | Nginx, Traefik |
| DNS | Cloudflare Free |

### Monitoring
| Need | Free Solution |
|------|---------------|
| Metrics | Prometheus |
| Visualization | Grafana (OSS) |
| Logging | Loki |
| Tracing | OpenTelemetry, Tempo, Jaeger |
| Alerting | AlertManager |

### Security
| Need | Free Solution |
|------|---------------|
| TLS | Let's Encrypt, OpenSSL |
| VPN | WireGuard |
| IDS/IPS | Fail2Ban, CrowdSec |
| Secrets | Vault Community |
| SSO/Auth | Keycloak, Authentik |

### AI/ML
| Need | Free Solution |
|------|---------------|
| Local LLM | Ollama |
| Vector DB | Qdrant, ChromaDB, Milvus |
| Model Hub | HuggingFace |
| Notebooks | Jupyter, Google Colab Free |

### CI/CD
| Need | Free Solution |
|------|---------------|
| CI/CD | GitHub Actions Free |
| Container Registry | GitHub Container Registry |
| Artifact Storage | GitHub Releases |

---

## Compliance

### Every PR MUST include
- Statement confirming free alternatives were evaluated
- If paid dependency is introduced: the documented exception

### CI Enforcement
- CI checks for paid dependency declarations
- CI blocks merge if paid dependency lacks approved exception
- CI validates dependency license information

---

## Exceptions

Exceptions to this policy are recorded in:
- `docs/adr/` — Architecture Decision Records
- Dependency approval documents in relevant module

Every exception includes:
1. Free alternatives evaluated (minimum 3)
2. Technical reasons for rejection
3. Cost comparison (free vs paid, 3-year TCO)
4. Migration plan to free alternative
5. Expiration/review date for the exception
