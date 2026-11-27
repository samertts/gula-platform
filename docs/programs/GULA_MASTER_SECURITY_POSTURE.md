# GULA Master Security Posture

Status: **SECURITY NOT CERTIFIED**. Baseline: `a01352578c0df205b92e58444242e1fa6ae7d77b`. This register consolidates the security findings from the National Operational Readiness Gap Assessment and the fresh read-only repository audit. It does not claim a clean scan as proof of absence of vulnerabilities.

## 1. Verified implemented controls

| Control | Evidence | Classification |
|---|---|---|
| Bearer/cookie auth, blacklist, active user/lab, permission version | `backend/app/security/dependencies.py:36-112` | IMPLEMENTED, ROUTE_MOUNTED |
| Permission and service-account guards | `dependencies.py:115-144,147-167,183-202` | IMPLEMENTED |
| Consent dependency with owner bypass and break-glass logging | `backend/app/security/consent_dep.py:74-167` | IMPLEMENTED, ROUTE_MOUNTED at `app/services/mpi/api.py:316` |
| Canonical ADE evaluation | `backend/app/identity/services/authorization_decision.py:169,204-354`, PHI map `:311-323` | IMPLEMENTED, ROUTE_MOUNTED via clinical gateway `service.py:245-250` |
| Verified guardian guard | `authorization_decision.py:561-607`; `verified_guardian_guard.py:132-160,187-219,233-259`; tests `tests/unit/test_b3_verified_guardian.py:71-243` | IMPLEMENTED, TESTED |
| Identity access v2 with minimum-necessary fields and bounded break-glass construction | `app/national/services/identity_access.py:412-482` | IMPLEMENTED, TESTED (synthetic) |
| Canonical DB audit with hash chaining and permission-gated API | `app/identity/services/canonical_audit.py:90-180,182-260`; `app/identity/api/audit.py:54-162` | IMPLEMENTED, ROUTE_MOUNTED, PERSISTED(schema) |
| Fail-closed clinical gateway rollout | `app/clinical_gateway/rollout.py:17-34`, `routes.py:148-181` | IMPLEMENTED, TESTED |
| Secret/detect-secrets scan in Wave 05.3 evidence | `$W053/raw/wave05_3_nidp_secret_scan.txt`, `FINDINGS=0` | HISTORICAL SCAN ONLY |

## 2. Open security gaps

| ID | Finding | Evidence | Severity | Gate | Status |
|---|---|---|---|---|---|
| SEC-01 | Canonical ADE has no consent binding | `authorization_decision.py:81-105,219-354`; `tests/test_wave05_1_authorization_closure.py:533-536` | Critical | G2 | OPEN |
| SEC-02 | Consent service lacks patient/resource/scope binding | `consent_service_v2.py:58-81,167-191` | High | G2 | OPEN |
| SEC-03 | Guardian purposes not policy-approved | S-02 in `$NCI/05_discovery_governance_security.md` | High | G2,G11 | OPEN |
| SEC-04 | Legacy audit remains inside canonical ADE | S-05 in same discovery; `audit_service.py:215-227` | High | G2,G12 | OPEN |
| SEC-05 | Audit chain unkeyed; retention/immutability unproven | `canonical_audit.py:96-131,143-180,223-260`; `identity/api/audit.py:146` | Critical | G2,G5,G6 | OPEN |
| SEC-06 | Governorate scope absent from canonical ADE | `authorization_decision.py:81-105`; `models/organization.py:21`, `models/user.py:25` | Critical | G2,G11 | OPEN |
| SEC-07 | Blank/whitespace and explicitly unresolved scope values could bypass comparison; organization-wide omitted membership scope unchanged | `authorization_decision.py:520-535,537-550`; Phase 4 `phase4/00_PHASE4_SAFE_REMEDIATION.md` | Critical | G2 | OPEN — narrow Category A fix applied; independent/security-owner acceptance pending |
| SEC-08 | Two audit surfaces and unpersisted Wave 05.3 audit builders | `audit_service.py:224-227`; `canonical_audit.py:176`; `identity_access.py:333-409` | High | G2,G12 | OPEN |
| SEC-09 | Unguarded FHIR metadata/update endpoints | `capabilities/fhir_interoperability/routes.py:42,47`; `app/routes/app_updates.py:109` | Medium | G2,G4 | OPEN |
| SEC-10 | Production secret/key/cert custody not approved or inventoried | `app/config.py:151-215`; crypto report; no rotation record | High | G2,G10 | OPEN |
| ID-06 | Caller-supplied break-glass fields in canonical ADE | `authorization_decision.py:244-260` | High | G2 | OPEN |
| CLIN-08 | FHIR routes/connector lack ADE/consent/retry | `ehr_fhir.py:114-132,181-182,246-247`; `fhir_gateway.py:34-43`; `fhir_connector.py:55-98,132-170` | High | G2,G3 | OPEN |
| INF-06 | 381 open Dependabot alerts: 20 critical, 191 high, 142 medium, 28 low | `raw/10_dependency_infra_commands.txt` in readiness evidence | Critical | G2 | OPEN |
| INF-07 | npm audit 18 findings: 5 high, 12 moderate, 1 low | same | High | G2 | OPEN |
| INF-11 | Repository-wide ruff 1252 errors; mypy targetless invocation exit 2 | same | Medium | G1 | OPEN |

## 3. Isolation posture

- Real organization/facility scope exists in canonical models and some ADE checks, but `authorization_decision.py:520-550` can pass on null values.
- Governorate scope exists as data (`app/models/organization.py:21`, `app/models/user.py:25`) but not in `AuthorizationRequest` (`authorization_decision.py:81-105`).
- Cross-organization denial is demonstrated in the synthetic NCI E2E only; it is not proof of canonical runtime isolation.
- Cross-governorate denial is not implemented in the canonical authorization contract.

## 4. Audit posture

- Canonical audit API is mounted and DB-backed, but the chain is unkeyed and no retention/purge mechanism was found under `app/identity`.
- Legacy audit remains in `app/services/audit_service.py:224-227`; PG-specific sequence code at `:215-219` creates compatibility concerns.
- Wave 05.3 modules build `AuditEventInput` objects (`identity_access.py:333-409`, `identity_governance.py:760-791`, `government_verification.py:689-731`) but do not persist them from those modules.
- Single-audit-authority decision and retention policy require audit authority + schema owner approval.

## 5. Secrets and cryptography posture

- `app/config.py:151-215` has generated/fallback secrets with warnings; production validation occurs only when production mode is active.
- Government adapter credentials are empty by default (`config.py:333-347`), and `app/gateways/mode.py:45-77` downgrades live/shadow to stub when credentials are absent.
- `SyntheticInMemoryKeyProvider` at `app/national/services/identity_crypto.py:183` is not a production KMS.
- No approved key hierarchy, rotation drill, certificate-expiry drill, or secret inventory was found.

## 6. Supply-chain posture

- No dependency was added by this execution baseline.
- Free-first shortlist remains `PROPOSED`; no license/source review artifact was found for D-006a.
- Dependabot open alerts and npm audit findings remain unresolved; no clean-scan claim is made.
- Open PR inventory includes 53 PRs, mostly dependency updates and earlier execution branches; none were merged as part of this execution.

## 7. Security conclusion

The platform has meaningful implemented security primitives but cannot be classified `SECURITY VERIFIED`. Critical gaps remain in consent/scope binding, audit integrity, dependency exposure, and external trust. G2 remains `BLOCKED / NOT PASSED`. Engineering applied only a narrow null-scope fail-closed fix in Phase 4; it is not owner-accepted. All other items require named owner decisions or approvals.
