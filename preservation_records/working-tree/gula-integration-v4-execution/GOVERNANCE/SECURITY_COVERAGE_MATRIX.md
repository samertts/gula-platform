# Security Coverage Matrix

**Program:** GULA Stable v1.0.0 — Repository Unification
**Purpose:** Prove that retiring/reconciling the local standalone `security/` package (158 files, local-only) does not reduce runtime security coverage, and record where local hardening must be carried forward.
**Basis:** Static inspection only. **This document does not certify security.** Per `GOVERNANCE/AI_AGENT_RULES.md`, security certification requires human review.
**Date:** 2026-11-14

## 0. Key finding

The local `security/` package is **not imported by any backend code** (0 import hits across `backend/app` and `backend/tests`). It is a standalone toolkit/scaffold, not a wired runtime control. Runtime security on both lineages lives in `backend/app` (`backend/app/security`, `backend/app/identity`, `backend/app/audit`, `backend/app/clinical_gateway`) plus shared primitives in `shared/security/`.

Consequence: retiring the standalone package loses **no active runtime enforcement**. It may lose reusable helper code (crypto, compliance mappers, container-hardening rules) that is not currently loaded. Those are accounted by module below.

`shared/security/` (`encryption.py`, `hmac.py`) is **identical on both lineages** (absent from the tree diff) and is retained unchanged.

## 1. Local package inventory by module

Source: `security/modules/*` (19 substantive modules + duplicate stubs).

| Local module | Items | Remote runtime equivalent | Coverage | Disposition |
|---|---|---|---|---|
| `audit/` (immutable, service, models) | 4 | `backend/app/identity/models/audit.py`; `identity/services/canonical_audit.py`; `backend/app/audit/audit_log.py`; `backend/app/national/security/audit.py`; `backend/app/platform/audit.py`; migrations `20260813_0001_audit_log_tenant_context`, `20260814_0006_security_audit_governance` | **COVERED** | Retire local; adopt remote. Preserve hash-chain semantics (remote already has tenant-context audit). |
| `authentication/` | 2 | `identity/api/auth.py`; `identity/services/authentication_service.py`; `identity/adaptive_auth/*`; `backend/app/services/risk_based_auth_service.py`; `backend/app/security/login_protection.py` | **COVERED** | Retire local. |
| `authorization/` | 1 | `identity/policy_engine.py`; `identity/services/authorization_decision.py`; `authorization_service.py`; `authorization_service_v2.py`; `identity/models/authorization.py`; `identity/repositories/policy_repository.py`; `identity/services/clinical_policy_evaluator.py`; `identity/services/clinical_authorization_context_service.py`; `backend/app/security/policy.py`; `identity/services/abac` (`backend/app/security/abac.py`) | **COVERED (superset)** | Retire local. Remote is the sole authorization source of truth. |
| `identity/` (abac, jwt, mfa, oidc, passkeys, pkce, rbac, risk_engine, session) | 12 | `backend/app/security/{abac,auth,mfa_service,oauth2_provider,saml_service,session,zero_trust}.py`; `identity/api/{sessions,devices,security}.py`; `identity/federation/*`; `identity/models/{session,security}.py` | **COVERED** | Retire local; verify passkey/MFA parity in code review (remote has `mfa_service.py`, devices API). |
| `headers/` (cors, csp, csrf, middleware, sanitizer, security_headers) | 9 | `backend/app/security/csrf.py`; `backend/app/factory.py` CORS `allow_headers`; local `frontend-v3` nginx `security.conf` (CSP/HSTS/frame-ancestors); `backend/app/security/integrity.py` | **PARTIAL** | Retire local module; **carry forward** any header middleware constants not present in remote `factory.py` — verify CSP/HSTS/x-frame-options at the reverse-proxy + app layers. |
| `crypto/` (aes, argon, hashing, key_rotation, phi/field encryption, signing, random) | 12 | `shared/security/encryption.py` + `hmac.py` (identical); `backend/app/security/encryption.py`; `backend/app/security/quantum_shield.py` | **PARTIAL** | **PRESERVE-AS-REFERENCE**. Argon2 tuning, field/PHI encryption helpers and key-rotation utilities are not demonstrably wired remotely. Do not delete until a human confirms the encryption posture; `ENCRYPTION_KEY` rotation was an open local WARN. |
| `compliance/` (ASVS, GDPR, HIPAA, ISO27001, NIST, engine, mapper) | 10 | `identity/compliance/{models,routes,services}.py`; `docs/` compliance artefacts | **PARTIAL** | Preserve mappings as documentation/evidence; remote `identity/compliance` is the runtime module. |
| `container/` (compose, docker, nginx, postgresql, rabbitmq, redis) | 9 | `docker/`, `helm/`, `k8s/`, `config/`; hardened compose already adopted on both | **PARTIAL** | Preserve as reference hardening rules; runtime hardening lives in deployment manifests. |
| `database/` | 1 | `backend/migrations/`, `config/`, DB roles in deployment | **PARTIAL** | No unique runtime control; retire. |
| `fhir/` (audit, break_glass, consent, privacy, smart) | 8 | `backend/app/fhir/`; `backend/app/national/`; `identity/api/consents.py`; `identity/models/consent.py`; `identity/services/consent_service_v2.py`; `backend/app/core/privacy.py` | **PARTIAL** | Confirm FHIR break-glass/SMART scope coverage remotely during code review; preserve local `fhir/` as reference if gaps found. |
| `github/` | 1 | `.github/workflows/` (CodeQL/gitleaks/dependency-check/ai-governance) | **COVERED BY CI** | Retire local. |
| `integrity/` (verification) | 2 | `backend/app/security/integrity.py`; audit hash-chain | **COVERED** | Retire local. |
| `kubernetes/` (security, models) | 3 | `helm/`, `k8s/`, `config/quality-gates/` | **PARTIAL** | Preserve as reference; runtime in manifests. |
| `network/` | 1 | `config/`, `docker/`, reverse-proxy configs | **PARTIAL** | Retire local; network policy lives in deployment. |
| `privacy/` (enforcer) | 2 | `backend/app/core/privacy.py`; `identity/api/consents.py`; `identity/models/consent.py` | **COVERED** | Retire local. |
| `secrets/` | 1 | `config/`, gitleaks pre-commit, CI secret scanning, deployment secret wiring | **PARTIAL** | Retire local; no runtime import. |
| `supply_chain/` (scanner, code_scanning, dependency_review) | 5 | `.github/workflows/`, `config/security/dependency-check.yml`, Semgrep/CodeQL gates | **COVERED BY CI** | Retire local. |
| `terraform/` (security, models) | 3 | `terraform/` (remote root exists) | **PARTIAL / UNKNOWN** | Preserve local rules as reference; verify against remote `terraform/` in a later review. **Not verified.** |
| `threat_detection/` (engine, dashboard, risk_engine) | 5 | `backend/app/security/{login_protection,intrusion_detection,zero_trust}.py`; `backend/app/services/risk_based_auth_service.py`; `backend/app/routes/login.py` | **PARTIAL** | Retire local engine; confirm behavioural parity of login protection/risk scoring in review. |
| Duplicate stubs: `threat-detection/`, `supply-chain/`, `ci/` | 3 | — | **N/A** | Hyphen variants are empty/stub duplicates; retire. |

## 2. Remote-only security modules to ADOPT

`backend/app/security/`: `csrf.py`, `integrity.py`, `login_protection.py`, `policy.py`, `quantum_shield.py`, `zero_trust.py` (plus existing `abac.py`, `auth.py`, `consent_dep.py`, `encryption.py`, `intrusion_detection.py`, `mfa_service.py`, `oauth2_provider.py`, `rate_limit.py`, `rbac.py`, `saml_service.py`, `service_accounts.py`, `session.py`, `redis_client.py`).

New remote identity security surface: `identity/api/security.py`, `identity/api/audit.py`, `identity/api/consents.py`, `identity/models/{authorization,security,consent}.py`, `identity/repositories/policy_repository.py`, `identity/services/{authorization_decision,authorization_service_v2,clinical_authorization_context_service,clinical_policy_evaluator,consent_service_v2,canonical_audit}.py`.

These are adopted wholesale; local code adapts to them.

## 3. Controls that MUST be carried forward (do not silently drop)

1. **Audit immutability / hash-chain** — confirm remote `canonical_audit` + `audit_log` preserve append-only semantics and tenant context.
2. **PHI/field encryption + `ENCRYPTION_KEY` rotation** — local `security/modules/crypto` + `scripts/reencrypt_encryption_key.py` (with identifier guard) were hardened; verify remote equivalent before dropping.
3. **Reverse-proxy security headers (CSP/HSTS/frame-ancestors)** — local `frontend-v3` nginx change; ensure it survives the client reconciliation (CR-2).
4. **Authorization decision single-source** — remote `AuthorizationDecisionService` must be the only decision path; ensure no local `security.modules.identity.rbac` re-enforcement reappears.
5. **SQLi fix in `ai/knowledge_graph.py::create_node`** (local PROGRAM-BETA fix, bind params + `CAST(... AS jsonb)`) — verify the unified tree contains the fixed version and its regression test.
6. **CSRF + login protection + zero-trust + quantum-shield** — adopt remote; confirm they are registered in `factory.py` middleware stack.
7. **Secret scanning** — keep gitleaks/Semgrep/Dependabot gates from both lineages; no secret may enter the unified tree.

## 4. Disposition summary

| Disposition | Modules |
|---|---|
| Retire (fully covered remotely) | `audit`, `authentication`, `authorization`, `identity`, `integrity`, `privacy`, `github`, `supply_chain`, `secrets`, `database`, `network`, plus stubs |
| Preserve as reference until human review | `crypto`, `compliance`, `container`, `kubernetes`, `fhir`, `terraform`, `threat_detection`, `headers` |
| Adopt from remote | `backend/app/security/*` new files + identity security surface |

**Security verdict: NOT CERTIFIED.** Coverage appears preserved at the runtime layer, but items in §3 require human verification before the local `security/` package can be archived.

---
_Static coverage analysis. No security control was modified, and no certification is claimed._
