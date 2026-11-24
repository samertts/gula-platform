# GULA National Identity Architecture Study — Security & Privacy Threat Model

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 (human security review + Program Director sign-off) and D-021 (Clinical Safety Owner) remain `PENDING_APPROVAL`. This threat model **does not** satisfy D-020.
**Workstream:** J (Security, Privacy and Data Governance), inputs from all other workstreams.

---

## 0. Evidence convention and scope

See `MASTER_ARCHITECTURE.md` §0. Labels: `VERIFIED_IN_SOURCE`, `TEST_VERIFIED` (test source exists — **not executed here**), `PARTIAL`, `SOURCE_PRESENT`, `DORMANT`, `NOT_IMPLEMENTED`, `BLOCKED`, `UNVERIFIABLE`. Source presence is never runtime verification. No tests were run, no database contacted, no application file modified.

This model uses **STRIDE** categories and maps them to the identity architecture. It is a design artifact, not a certification. Existing controls are reported as found; gaps are recommendations, not accepted risks.

---

## 1. Trust boundaries and assets

### 1.1 Trust boundaries

| Boundary | Crossing | Controls expected |
|---|---|---|
| Internet → GULA edge | Login, registration, public endpoints | TLS, rate limiting, WAF, anti-enumeration |
| Citizen device → GULA | WebAuthn/TOTP credentials, document images | Origin binding, local encryption, minimal capture |
| Facility (offline/low-connectivity) → GULA | Assisted registration, document capture, event notification | Device enrollment, encrypted queue, idempotent sync, no final verification offline |
| GULA services → security store (Redis) | JTI blacklist, verification codes, sessions | Fail-closed on unavailability, authn/authz to store |
| GULA services → databases | Identity, MPI, documents, audit | Least-privilege DB roles, tenant/facility scoping, audit |
| GULA → external government systems | Civil registry / document verification (not assumed) | Legal agreement, verified interface, data minimization, audit |
| Staff/facility → patient data | Clinical access | RBAC/ABAC, purpose, relationship, consent, break-glass, audit |
| GULA → backup/DR | Backups, forensic snapshots | Encryption, integrity, access control, legal hold |

### 1.2 Protected assets

- Iraqi National Identity Card number (protected matching attribute — D-IDENTITY-01).
- NHID and person identity linkage (D-IDENTITY-02).
- Provisional identities and child identities (D-IDENTITY-03/05).
- Credentials: password hashes, TOTP seeds, WebAuthn private keys (held by authenticator), recovery codes, JWT signing secrets, refresh secret.
- Document images and OCR extractions (D-IDENTITY-10).
- Guardian relationships and permission delegations.
- Vital-event states (birth/death) and death status.
- Consent records, audit hash chains, forensic snapshots.
- Availability of authentication (revocation store) and care-critical identity lookup.

---

## 2. STRIDE threat analysis

### 2.1 Spoofing (identity theft, ATO, document forgery, biometric replay)

| Threat | Source evidence | Current controls | Gaps / recommendations | Status |
|---|---|---|---|---|
| Account takeover via credential theft | `shared/auth/passwords.py`; `routes/login.py:50-118`; JWT `config.py:178-202` | bcrypt, dummy hash, rate limit, lockout, MFA gate for privileged roles | MFA FK only to `lab_users.id` (`models/mfa_device.py:11-40`) so non-lab accounts cannot enroll WebAuthn; risk engines inert (`adaptive_auth`, `risk_based_auth_service`, `zero_trust`) | `PARTIAL` — `SECURITY_REVIEW_REQUIRED` |
| WebAuthn challenge forgery / broken verification | `shared/auth/webauthn.py:22-24,50,61,86,99`; `mfa_service.py:93-106,133-153` | Real WebAuthn library usage | Hardcoded RP ID/origin; `default=str` challenge serialization; empty-challenge fallback on cache failure; no full round-trip test | `PARTIAL` — `SECURITY_REVIEW_REQUIRED` |
| OIDC ID-token forgery / validation failure | `oauth2_provider.py:172-178` | HS256 ID tokens, PKCE S256 | Empty JWKS → conforming RPs cannot validate; no asymmetric keys | `PARTIAL` — `SECURITY_REVIEW_REQUIRED` |
| SAML assertion replay / forged SSO session | `saml.py:47-82`; `saml_service.py:37-71` | Safe algorithms, pinned cert, issuer/audience checks | ACS returns booleans only, no session/token; config-gated 503; not a login | `PARTIAL` / `BLOCKED` |
| Document forgery accepted as verification | OCR/document-intelligence surfaces (see `DOCUMENT_VERIFICATION_DESIGN.md`); `connector_service.py:85-123` stubs | Consent/service auth on some routes | Civil-registry stubs return `confidence: 1.0`, `match: True` — **must never be treated as verification**; OCR extraction is not proof (D-IDENTITY-10) | `PARTIAL` — `SECURITY_REVIEW_REQUIRED` |
| Biometric/face spoofing and replay | No verified biometric verification implementation found (see `DOCUMENT_VERIFICATION_DESIGN.md`) | None found | Biometrics must never be the only path; liveness/replay controls required if ever introduced | `NOT_IMPLEMENTED` — `SECURITY_REVIEW_REQUIRED` |
| Identity theft via national ID exposure | `routes/identity.py:22 POST /identity/link`, `:67 GET /identity/lookup`; frontend `identityApi` `/identity/lookup?national_id=` | HMAC family hashing in `patient.py:30-32` | National ID used in lookup query string; must be encrypted/HMAC-matched and minimized (D-IDENTITY-01) | `PARTIAL` — `RECOMMENDED` |

### 2.2 Tampering (merge abuse, death-status abuse, audit tampering, offline sync)

| Threat | Source evidence | Current controls | Gaps / recommendations | Status |
|---|---|---|---|---|
| Unauthorized patient-record merge | MPI routes `services/mpi/api.py:142 /merge`, `:182 /review`, `:226 /review/{claim}/decide`; consent dependency at `:316` | Consent `require_consent("read:citizen")` on one route; audit | Hybrid merge policy requires explicit automatic-merge eligibility + human review + auditable unmerge (D-IDENTITY-07, `MASTER_PATIENT_INDEX_DESIGN.md`); merge abuse must be dual-controlled | `PARTIAL` — `SECURITY_REVIEW_REQUIRED` |
| Wrongful death status (care/benefit denial) | `identity/lifecycle/services.py:494-504`; `routes.py:460-469`; `national/domain/death_record.py` | `record_death()` writes status + certificate | Distinct notification/confirmation/civil states not enforced; no two-person approval found; route/service mismatch; requires legal + security gate (VIT-01/VIT-07) | `PARTIAL` — `SECURITY_REVIEW_REQUIRED` |
| Audit log tampering | `models/audit_log.py:10-27` (`chain_hash`); `services/audit_service.py:31-45,77-112,184-270`; PG triggers `20250322_0002_perf_indexes_audit_protection.py:73-104`; NIAM `niam_audit_entries` `entry_hash`/`previous_hash` | HMAC anchor, rotation, SHA-256 chain, append-only triggers | Two chains (canonical + NIAM) with attribution questions (ADR-D pending); lifecycle events may not be emitted (`UNVERIFIABLE`) | `PARTIAL` |
| Tampered offline-sync payload / duplicate submission | Offline design (see `OFFLINE_AND_LOW_CONNECTIVITY_DESIGN.md`) | Retry queue assumed | Must enforce signed payloads, idempotency keys, conflict detection; no offline device may finalize identity verification | `RECOMMENDED` |
| Workflow-step "SUCCEEDED" without work | `national/workflows/patient_registration.py:41-69`; `death_registration_workflow.py:12-24` | None — steps marked succeeded unconditionally | Security/identity-safety hazard if mounted; national router currently unmounted | `PARTIAL` — `SECURITY_REVIEW_REQUIRED` |

### 2.3 Repudiation (audit, non-repudiation)

| Threat | Evidence | Assessment |
|---|---|---|
| Actor denies identity event / access | Hash-chain audit (above); NIAM audit vocabulary (`identity/models/audit.py:177-181,218-219`); medico-legal forensic snapshot model (`phase24-legal-governance/04-medico-legal-analysis.md`) | Strong primitives exist, but coverage is partial: consent enforcement wired into only one route (`security/consent_dep.py` used at `mpi/api.py:316`); fail-open stub `national/security/consent_enforcement.py:16-44` returns `granted=True` with no logging; lifecycle services not observed emitting audit actions (`UNVERIFIABLE`). Recommendation: single enforcement authority + complete event emission + legal hold integration (LAW-04). |

### 2.4 Information disclosure (patient records, national ID, child data, exfiltration)

| Threat | Source evidence | Current controls | Gaps / recommendations | Status |
|---|---|---|---|---|
| Unauthorized staff access | `routes/consent.py`, `security/consent_dep.py`, `authz` router `factory.py:834`; tenant scoping in care continuum (`_lab_id`) | RBAC/ABAC, purpose vocabulary `trust/enums.py:14-21`, break-glass `doctor` role | Consent enforcement on one route only; fail-open stub; `ConsentPurpose` not mapped to `read:*` scopes; F-073 tenant gaps residual (governance) | `PARTIAL` — `SECURITY_REVIEW_REQUIRED` |
| Guardian abuse / unauthorized child-data access | Guardian stores (see `GUARDIAN_AND_CHILD_IDENTITY_DESIGN.md`), permission matrix | `GuardianRulesService` deny-by-default (dormant), HMAC family ID | Four divergent stores; mounted NIAM guardian API likely broken; no dispute-suspension found | `PARTIAL` — `LEGAL_REVIEW_REQUIRED` + `SECURITY_REVIEW_REQUIRED` |
| National ID exposure | `identity/lookup?national_id=`; `national-id/verify` | HMAC for family ID; bcrypt for keys | Encrypt national ID at rest, HMAC for matching, minimize in logs/URLs, controlled access (D-IDENTITY-01) | `PARTIAL` — `RECOMMENDED` |
| Data exfiltration / ransomware | Document store + DB surface | Backups/DR documented in national completion report | Encryption at rest only "National ID only, not all PHI" (`LEGAL_MASTER_PLAN.md:202`); immutable/offline backups, least privilege, egress monitoring required | `PARTIAL` — `SECURITY_REVIEW_REQUIRED` |
| Cross-domain / cross-tenant leakage | `Organization.parent_org_id` no FK (`organization.py:19`); `national_facilities` dual owner; `facilities` ownership unresolved (ADR-B) | `require_own_lab` patterns (governance) | Hierarchy integrity not DB-enforced; orphaned/cyclic trees possible; verify facility scoping | `PARTIAL` |

### 2.5 Denial of service (auth store outage, API abuse, lockout abuse)

| Threat | Evidence | Assessment |
|---|---|---|
| Revocation store outage blocks all auth | `security/dependencies.py:52-69` fail-closed 503; `security_store` (`redis_client.py:200-213`) | Fail-closed is correct for security but creates availability dependency; must size Redis for HA/DR and define degraded policy explicitly (`CAPACITY_AND_COST_MODEL.md`) |
| Login brute force / lockout of legitimate users | `login_protection.py`, `rate_limit.py` | Controls present; exact backoff `UNVERIFIABLE`; tune to avoid caregiver lockout |
| API abuse on registration/MPI/OCR | `mpi` routes, `doc_intel` routes, `verification` rate limit 30/min on consent | Apply rate limits, quotas, payload limits, WAF to all identity surfaces |
| Ransomware on facility devices | Offline design | Encrypted local storage, short retention, remote wipe, re-enrollment (`OFFLINE_AND_LOW_CONNECTIVITY_DESIGN.md`) |

---

## 3. Required control baseline (target)

| Control | Requirement | Source alignment / gap |
|---|---|---|
| Encryption in transit | TLS 1.2+ everywhere, including facility sync and internal service calls | Assumed; verify configuration (runtime `UNVERIFIABLE`) |
| Encryption at rest | All PHI and identity data, not only National ID | `LEGAL_MASTER_PLAN.md:202` gap — `SECURITY_REVIEW_REQUIRED` |
| Key management | HMAC anchor key rotation (`audit_service.py:33-45`), separate refresh secret (`config.py:188-200`), document/key rotation policy; self-hosted KMS preferred | Partial; OIDC asymmetric keys absent (AUTH-04) |
| HMAC-based matching | National ID and family identifiers HMAC-matchable, raw values not persisted | `patient.py:30-32` HMAC family ID; extend to national ID (D-IDENTITY-01) |
| Secrets management | No hardcoded secrets; env-validated production secrets (`config.py:190-191`) | Positive; hardcoded WebAuthn RP is not a secret but is a config defect |
| Least privilege | Role-based DB/service accounts, facility scoping, `require_own_lab` | Partial (F-073 residual, org hierarchy gaps) |
| Separation of duties | Two-person approval for merge, death final status, guardian changes, credential recovery | Not found — `RECOMMENDED` |
| Purpose-based access | Every patient-data access carries purpose + legal basis + audit | Partial (purpose vocabulary exists, mapping missing) |
| Consent | One enforcement authority; deny-by-default; no fail-open stub in enforcement path | Partial (§2.4) |
| Audit | Hash-chain, append-only, complete event emission, legal hold | Strong primitives, incomplete wiring |
| Data retention / deletion restrictions | No deletion of medical history after death; provisional records not auto-deleted; retention policy per legal review | Owner decisions D-IDENTITY-03/06; legal `UNVERIFIABLE` |
| Breach response | Detection, containment (mass token revocation), notification process, forensics | Notification process missing (`LEGAL_MASTER_PLAN.md:191`); implement with legal counsel |
| Backup and recovery | Encrypted, integrity-verified backups; DR drill evidence from national completion report; RPO/RTO currently UNMEASURED per completion baseline | Carry to `CAPACITY_AND_COST_MODEL.md` / `RISKS_AND_OPEN_QUESTIONS.md` |

---

## 4. Highest-priority security findings (ranked)

| Rank | Finding | Evidence | Classification |
|---|---|---|---|
| 1 | Fail-open consent stub could allow unauthorized access if used | `national/security/consent_enforcement.py:16-44` | `SECURITY_REVIEW_REQUIRED` |
| 2 | WebAuthn broken (hardcoded RP, challenge serialization, empty-challenge fallback) | `webauthn.py:22-24,50,61,86,99`; `mfa_service.py:93-106,133-153` | `SECURITY_REVIEW_REQUIRED` |
| 3 | OIDC JWKS empty — ID tokens not verifiable | `oauth2_provider.py:172-178` | `SECURITY_REVIEW_REQUIRED` |
| 4 | Device revocation does not kill tokens/sessions | `device_service.py:79-85` | `SECURITY_REVIEW_REQUIRED` |
| 5 | Death status lacks distinct state separation + two-person approval | `lifecycle/services.py:494-504`; VIT-01 | `SECURITY_REVIEW_REQUIRED` |
| 6 | Workflow stubs mark verification SUCCEEDED without work | `patient_registration.py:41-69`; `death_registration_workflow.py:12-24` | `SECURITY_REVIEW_REQUIRED` |
| 7 | Civil registry stubs return `confidence: 1.0` | `connector_service.py:85-123` | `SECURITY_REVIEW_REQUIRED` |
| 8 | National ID in lookup query string; encryption at rest incomplete | `identity/lookup?national_id=`; `LEGAL_MASTER_PLAN.md:202` | `RECOMMENDED` |
| 9 | Risk signals computed but not enforced at login | `adaptive_auth`, `risk_based_auth_service`, `zero_trust` | `RECOMMENDED` |
| 10 | Consent enforcement wired to one route; purpose/scope unmapped | `consent_dep.py` usage; `trust/enums.py:14-21` | `SECURITY_REVIEW_REQUIRED` |

**D-020 note:** these findings are inputs to the required human security review; they do not constitute it. D-020 remains `PENDING_APPROVAL`.

---

## 5. Test requirements (design-level; no tests run in this study)

| Level | Required coverage |
|---|---|
| Unit | Challenge serialization round-trip; RP configuration; HMAC matching; consent deny-by-default; permission matrix; death-state transitions. |
| Integration | Consent enforcement on every patient-data route; fail-open stub removed from enforcement; device revocation kills tokens; fail-closed store outage; MPI merge/unmerge with dual approval; audit event emission for all identity events. |
| Security | WebAuthn full round-trip + replay; OIDC ID-token validation via populated JWKS; SAML ACS (if ever made a login); anti-enumeration oracle; lockout bypass; ATO response drill; insider-access simulation; guardian-abuse scenarios; merge-abuse; death-status abuse; offline tamper/duplicate. |
| Privacy | National ID not in logs/URLs; encryption at rest coverage; data minimization; retention/deletion restrictions; legal-hold behavior. |
| Operational | Breach-response drill, mass token revocation, backup restore + forensic snapshot, RPO/RTO measurement (currently UNMEASURED). |

Use synthetic data only. Do not claim E2E from contract-envelope tests (`TESTING_AND_ACCEPTANCE_STRATEGY.md`).

---

## 6. Architecture decisions register

| ID | Decision | Problem | Alternatives | Advantages | Disadvantages / risks | Legal | Security | Ops / cost | Dependencies | Failure scenario | Reversibility | Evidence | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SEC-01 | Single consent/authorization enforcement authority; remove fail-open stub from any enforcement path | Fail-open stub + duplicate authorities | Keep all | Deny-by-default, consistent audit | Migration/integration effort | Legal basis required | Strong positive | Moderate | Owner decision; purpose↔scope mapping | Unauthorized disclosure | Reversible | §2.4, §4 | `SECURITY_REVIEW_REQUIRED` |
| SEC-02 | Asymmetric OIDC keys + populated JWKS before any OIDC reliance | Empty JWKS | Hide JWKS | Standards-conformant validation | Key management | None identified | Strong positive | Low–moderate | `oauth2_provider.py:172-178` | RP cannot verify tokens | Reversible | §2.1, §4 | `SECURITY_REVIEW_REQUIRED` |
| SEC-03 | Fix WebAuthn (configurable RP, challenge bytes, no empty fallback) | Broken primary credential | Keep broken | Phishing-resistant auth | Test + code change | None identified | Strong positive | Low | Full round-trip test | WebAuthn unusable | Reversible | §2.1, §4 | `SECURITY_REVIEW_REQUIRED` |
| SEC-04 | Device revocation invalidates sessions + tokens | Flag-only revocation | Keep flag | Prevents post-theft access | State coordination | None identified | Positive | Low | `device_service.py:79-85` | Revoked device retains access | Reversible | §2.1, §4 | `SECURITY_REVIEW_REQUIRED` |
| SEC-05 | Two-person approval for merge, death final status, guardian change, credential recovery | Abuse / unilateral action | Single actor | Separation of duties | Usability friction | Authority to be defined | Positive | Moderate | Legal + owner decisions | Abusive unilateral change | Reversible | §3, §4 | `SECURITY_REVIEW_REQUIRED` |
| SEC-06 | Encrypt all PHI at rest and keep national ID HMAC-only for matching | Partial encryption | Keep National-ID-only | Data protection | KMS/key rotation effort | Data-protection law (unverified) | Positive | Moderate | `LEGAL_MASTER_PLAN.md:202` | Breach exposure | Reversible | §2.4, §3 | `RECOMMENDED` |
| SEC-07 | Do not mount `national_router` until workflow stubs produce real evidence | Stubs mark SUCCEEDED | Mount as-is | Avoids false verification | Delayed capability | None identified | Positive | Low | Endpoint verification | False verification exposed | Reversible | §2.2, §4 | `SECURITY_REVIEW_REQUIRED` |

---

## 7. Open questions

1. Does the human security review (D-020) accept the fail-closed Redis availability trade-off, and what is the HA target?
2. Which consent authority is canonical, and how are `ConsentPurpose` values mapped to `read:*` scopes?
3. Are WebAuthn and OIDC defects confirmed by executed integration tests before any rollout?
4. What are the legal requirements for breach notification, retention and encryption (Workstream K)?
5. What two-person approval workflow is acceptable for merge/death/guardian/recovery actions?
6. How are the two audit chains reconciled, and who owns event attribution (ADR-D)?

---

## 8. Cross-references

`MASTER_ARCHITECTURE.md` · `AUTHENTICATION_AND_RECOVERY_DESIGN.md` · `GUARDIAN_AND_CHILD_IDENTITY_DESIGN.md` · `BIRTH_AND_DEATH_LIFECYCLE.md` · `MASTER_PATIENT_INDEX_DESIGN.md` · `DOCUMENT_VERIFICATION_DESIGN.md` · `IRAQI_LEGAL_AND_INSTITUTIONAL_ASSESSMENT.md` · `DATABASE_OWNERSHIP_AND_DATA_MODEL.md` · `OFFLINE_AND_LOW_CONNECTIVITY_DESIGN.md` · `CAPACITY_AND_COST_MODEL.md` · `TESTING_AND_ACCEPTANCE_STRATEGY.md` · `RISKS_AND_OPEN_QUESTIONS.md` · `IMPLEMENTATION_ROADMAP.md` (Phases 10–12).
