# Architecture Rules — PROGRAM-CONSTITUTION-001

**Version:** 1.0.0
**Date:** 2026-07-23
**Authority:** Platform Constitution — Permanent Amendment
**Status:** ADOPTED — FROZEN — PERMANENT

---

## Rule Set: Cost Governance & Open Source Mandate

These architecture rules are automatically enforced by CI and all AI agents.
Violations BLOCK pull requests and MUST be remediated.

---

## Rule AR-001: Free First Compliance

| Property | Value |
|----------|-------|
| **Rule** | Every implementation MUST search for a FREE solution first |
| **Check** | CI scans `requirements.txt`, `package.json`, `pyproject.toml` for paid service patterns |
| **Violation** | Paid service reference without ADR approval → BLOCK PR |
| **Enforcement** | `scripts/constitution_enforcer.py` Rule 21 |
| **Exception** | Architecture Decision Record with cost analysis and Engineering Lead approval |

---

## Rule AR-002: Open Source License Compliance

| Property | Value |
|----------|-------|
| **Rule** | All dependencies MUST have OSI-approved open source licenses |
| **Check** | CI validates license of every dependency |
| **Violation** | Proprietary/commercial license → BLOCK PR |
| **Enforcement** | `scripts/constitution_enforcer.py` Rule 22 |
| **Exception** | Architecture Review Board approval with documented business need |

---

## Rule AR-003: Vendor Lock-In Prohibition

| Property | Value |
|----------|-------|
| **Rule** | Every component MUST be replaceable with an abstraction layer |
| **Check** | CI scans for direct vendor SDK imports (boto3, azure, google.cloud, firebase, supabase, auth0, okta, stripe, twilio, sendgrid) |
| **Violation** | Direct vendor SDK import in core domain → BLOCK PR |
| **Enforcement** | `scripts/constitution_enforcer.py` Rule 23, startup guard |
| **Exception** | Architecture Review Board supermajority + documented exit strategy |

### Prohibited Direct Imports

```python
# BLOCKED — direct vendor coupling
import boto3
from azure.storage.blob import BlobServiceClient
from google.cloud import storage
import firebase_admin
from supabase import create_client
from auth0 import Auth0
import stripe
import twilio

# ACCEPTABLE — through abstraction layer
from app.gateways.storage import StorageBackend
from app.gateways.notification import NotificationProvider
from app.gateways.payment import PaymentGateway
```

---

## Rule AR-004: Self-Hosted First

| Property | Value |
|----------|-------|
| **Rule** | Self-hosted infrastructure SHALL be preferred over hosted SaaS |
| **Check** | CI scans for SaaS endpoint references in configuration files |
| **Violation** | SaaS reference without documented self-hosted alternative → WARN |
| **Enforcement** | `scripts/constitution_enforcer.py` Rule 24 |
| **Exception** | Self-hosted option requires >2 FTE to maintain OR has higher TCO |

### Approved Self-Hosted Stack

| Need | Self-Hosted Solution | SaaS Alternative (requires exception) |
|------|---------------------|---------------------------------------|
| Database | PostgreSQL | Supabase, AWS RDS, Google Cloud SQL |
| Cache | Redis | Redis Cloud, AWS ElastiCache |
| Storage | MinIO | AWS S3, Google Cloud Storage |
| Monitoring | Grafana + Prometheus | Datadog, New Relic |
| Logging | Loki | Logz.io, Datadog Logs |
| Auth | Keycloak / Authentik | Auth0, Okta |
| AI | Ollama | OpenAI, Anthropic |
| Search | OpenSearch | Algolia, Elastic Cloud |
| Email | Self-hosted SMTP | SendGrid, Mailgun |
| CDN | Nginx + MinIO | Cloudflare (Free ok), Fastly |
| CI/CD | GitHub Actions (Free) | CircleCI, Jenkins (cloud) |

---

## Rule AR-005: Cost Governance

| Property | Value |
|----------|-------|
| **Rule** | Every implementation MUST optimize for lowest cost and highest sovereignty |
| **Check** | Architecture review verifies cost optimization in every ADR |
| **Violation** | Unnecessary paid infrastructure → BLOCK PR |
| **Enforcement** | `scripts/constitution_enforcer.py` Rule 25, Architecture Review Board |

### Cost Priorities

| Priority | Area | Target Monthly Cost |
|----------|------|-------------------|
| 1 | Compute | $0 (self-hosted Linux/Docker) |
| 2 | Database | $0 (PostgreSQL) |
| 3 | Storage | $0 (MinIO) |
| 4 | Cache | $0 (Redis) |
| 5 | Monitoring | $0 (Prometheus + Grafana) |
| 6 | CI/CD | $0 (GitHub Actions Free) |
| 7 | TLS | $0 (Let's Encrypt) |
| 8 | CDN | $0 (Cloudflare Free) |
| 9 | AI | $0 (Ollama + open-weight models) |
| 10 | Auth | $0 (Keycloak / Authentik) |

---

## Rule AR-006: Reuse Before Build

| Property | Value |
|----------|-------|
| **Rule** | Search existing codebase before implementing new functionality |
| **Check** | Architecture review validates reuse is not possible |
| **Violation** | Duplicate implementation of existing functionality → BLOCK PR |
| **Enforcement** | Code review + `scripts/constitution_enforcer.py` Rule 5 |

---

## Rule AR-007: Platform Sovereignty

| Property | Value |
|----------|-------|
| **Rule** | Platform MUST remain deployable using only Linux, Docker, Open Source Software |
| **Check** | Every deployment dependency is audited against this rule |
| **Violation** | Commercial subscription required for deployment → BLOCK PR |
| **Enforcement** | Architecture Review Board |

---

## Rule AR-008: Local AI First

| Property | Value |
|----------|-------|
| **Rule** | Self-hosted AI inference (Ollama) before commercial AI APIs |
| **Check** | Architecture review for any AI feature |
| **Violation** | Commercial AI API used without evaluating local alternative → BLOCK PR |
| **Enforcement** | Architecture Review Board |

---

## Rule AR-009: ADR Cost Section

| Property | Value |
|----------|-------|
| **Rule** | Every ADR MUST include Open Source, Free, and Commercial alternatives |
| **Check** | CI scans ADRs for required sections |
| **Violation** | ADR missing cost/open-source alternatives → WARN |
| **Enforcement** | CI constitution-compliance workflow |

---

## Rule AR-010: Dependency Approval

| Property | Value |
|----------|-------|
| **Rule** | Every new dependency MUST go through formal approval |
| **Check** | CI validates new dependencies against dependency registry |
| **Violation** | Unapproved dependency → BLOCK PR |
| **Enforcement** | `scripts/constitution_enforcer.py` Rule 7 |
| **Policy** | `docs/architecture/DEPENDENCY_APPROVAL_POLICY.md` |

---

## Violation Severity Matrix

| Severity | Rules | CI Action | Remediation |
|----------|-------|-----------|-------------|
| **BLOCKER** | AR-001 (no ADR), AR-003, AR-005, AR-007 | FAIL → block merge | Fix violation or obtain exception |
| **HIGH** | AR-001 (warn), AR-002, AR-004 | WARN → review required | Document exception or fix |
| **MEDIUM** | AR-006, AR-008, AR-009, AR-010 | PASS + WARN | Address before next release |
| **LOW** | Informational | PASS | Track for continuous improvement |

---

## Enforcement

These rules are enforced at multiple levels:

| Level | Mechanism | Frequency |
|-------|-----------|-----------|
| **AI Agents** | Automatic policy enforcement (AGENTS.md) | Every code generation |
| **Pre-commit** | Pre-commit hook runs constitution checks | Every commit |
| **CI** | `constitution-compliance.yml` workflow | Every PR |
| **CI** | `scripts/constitution_enforcer.py` Rules 21-25 | Every PR |
| **Startup** | `startup_guard.py` constitutional check | Every deployment |
| **Architecture Review** | ADR review board | Every architecture decision |
| **Quarterly** | Full dependency + cost audit | Quarterly |

---

## References

- `docs/constitution/COST_GOVERNANCE.md` — Full Cost Governance policy
- `docs/constitution/SYSTEM_CONSTITUTION.md` — System Constitution
- `docs/architecture/FREE_FIRST_POLICY.md` — Free First policy
- `docs/architecture/OPEN_SOURCE_POLICY.md` — Open Source policy
- `docs/architecture/VENDOR_LOCK_IN_POLICY.md` — Vendor lock-in policy
- `docs/architecture/DEPENDENCY_APPROVAL_POLICY.md` — Dependency approval policy
- `AGENTS.md` — AI agent enforcement
- `CLAUDE.md` — Developer guidance
- `PLATFORM-CONSTITUTION.md` — Supreme platform constitution
- `ENGINEERING_CONSTITUTION.md` — Engineering governance
