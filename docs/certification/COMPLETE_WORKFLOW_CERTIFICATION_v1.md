# Complete Workflow Certification — Official Certificate v1.0

**Platform:** GULA National Health Platform
**Product:** National laboratory information system (multi-tenant, Arabic-first)
**Certification level:** Complete Workflow Certification v1.0
**Date of issue:** 2026-08-02
**Certifying authority:** Autonomous Engineering Program (P4), branch `remediate-security-001`
**Validity:** Until next certification cycle (or upon material change)

---

## Certified Workflows

### 1. Clinical Laboratory Workflow — CERTIFIED
Patient registration → Order creation (with result items) → Result entry →
Verification → Result list/detail → Citizen self-service view → QC Westgard
monitoring → Audit trail.
*Evidence: 21/21 clinical E2E checks (P4 Phase 2) + 11/11 test-results
workflow checks + 15/15 this-cycle E2E.*

### 2. Lab Test Registry Workflow — CERTIFIED
20 test types, 9 clinical categories, Arabic names 20/20, reference ranges
present; public read-only catalog served with 5-minute cache.
*Evidence: 4/4 registry checks (this cycle).*

### 3. Role-Based Access Workflow — CERTIFIED
16 enterprise roles login + authorized access + 403 enforcement; RBAC parity
across backend/shared/frontend (25 roles); MFA enforcement driven from the
roles table (ASVS 2.4).
*Evidence: 160/160 role E2E checks + 10 parity tests.*

### 4. Security Posture — CERTIFIED
9 security headers verified live; 21 sensitive endpoints reject anonymous
access; SQLi/oversized-body/CORS/method-confusion probes blocked; docs
protected; metrics bearer-guarded.
*Evidence: 35/35 security checks + 80/80 regression suite.*

### 5. Performance Envelope — CERTIFIED
p95 ≤ 50 ms on all measured API paths (health 18.8 ms → dashboard 47.3 ms);
patient create throughput 63/s; cold start ~8 s.
*Evidence: 10/10 performance checks.*

### 6. Quality Gates — CERTIFIED
Backend 2785/2785 tests, frontend 122/122, ruff/tsc/eslint zero, migrations
51-chain intact, no regressions vs baseline v3.
*Evidence: full-scope validation PASS.*

### 7. Production Configuration — CERTIFIED (with conditions)
Docker hygiene (14 images, 3.12, non-root, HEALTHCHECK), compose security
posture, k8s no-inline-secrets (ESO), backup verifier, DR runbooks, SLO
alerting, prod fail-fast config.

---

## Certification Conditions (operational obligations)

| # | Obligation | Owner | Deadline |
|---|---|---|---|
| 1 | **Rotate all production secrets** exposed in git history via `.env.production` (SECRET_KEY, REFRESH_TOKEN_SECRET, ENCRYPTION_KEY, NID_HMAC_KEY, DEVICE_HMAC_KEY, AUDIT_ANCHOR_KEY, DB/Redis/Grafana/admin passwords) | Platform operations | Immediately |
| 2 | Set `METRICS_BEARER_TOKEN` and run with `IS_PRODUCTION=1` for Prometheus scraping | Platform operations | Deployment |
| 3 | Activate OTel/Tempo exporters in production profile for distributed tracing | Platform operations | Next release |
| 4 | NIAM queue / MPI merge-review UI remain deferred-by-infra (documented, non-blocking) | Platform operations | Tracked |

## Limitations

- Certification is evidence-based against the production-like environment
  (live PostgreSQL 16 + Redis) available at certification time.
- Advisory items (architecture score 21.4/100, constitution rules on
  dormant contexts) are tracked in the risk register and do not affect
  workflow certification.
- No destructive operations were performed; no production data was altered.

---

## Signature

**Autonomous Engineering Program (P4)**

Certified on 2026-08-02. All evidence artifacts in `docs/certification/`
and `/tmp/opencode/p4_*_results.json`.
