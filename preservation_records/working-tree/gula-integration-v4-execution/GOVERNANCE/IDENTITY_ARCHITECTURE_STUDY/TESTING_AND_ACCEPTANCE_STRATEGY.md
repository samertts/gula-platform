# GULA National Identity Architecture Study — Testing & Acceptance Strategy

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain `PENDING_APPROVAL`.

---

## 0. Evidence convention & honesty rule

See `MASTER_ARCHITECTURE.md` §0. Labels: `VERIFIED_IN_SOURCE`, `TEST_VERIFIED` (test **source exists** — **not executed here**), `PARTIAL`, `SOURCE_PRESENT`, `DORMANT`, `NOT_IMPLEMENTED`, `BLOCKED`, `UNVERIFIABLE`.

**No test was executed in this study.** Every "test count" below is `TEST_VERIFIED` meaning *test source exists*, never a pass/execution claim. All runtime outcomes are `UNVERIFIABLE`.

**Completion-baseline honesty (`GOVERNANCE/NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md`):** **0 services E2E/RUNTIME/PRODUCTION verified**; 7 journeys are **contract-envelope only**; RPO/RTO **UNMEASURED**; no production-like snapshot. **No E2E claim is made from contract-envelope tests.** This study does not improve that baseline.

**Data rule:** synthetic or legally authorized de-identified data only. No live operational DB, no real citizen data, no government API.

---

## 1. Existing test source inventory (not executed)

| Capability | Test source (file / count) | What it covers (source-level) |
|---|---|---|
| MPI matching / merge | `test_mpi_matcher.py` (35); `test_security_merge_regression_synthetic.py` (8) | matcher weights, synthetic merge security |
| NIAM identity | `test_niam.py` (44); `test_niam_v2.py` (45); `test_niam_professional_registry.py` (12); `test_niam_registry_authorization.py` (14); `test_niam_workspaces.py` (16); `test_niam_citizen_registry.py` (10); `test_niam_session_security.py` (9); `test_niam_org_guard.py` (8) | identity, registry auth, workspace, professional, citizen, session, org guard |
| Identity governance | `test_persisted_identity_governance.py` (35); `test_identity_governance.py` (9) | NID/health-number governance |
| Citizen platform | `test_citizen_platform_security.py` (8) | token/QR/recovery security |
| National ID verify guard | `test_national_identity_production_guard.py` (3) | stub-gateway production guard |
| Auth / WebAuthn / reset | various auth test modules | login/MFA/webauthn/reset (defects documented in `AUTHENTICATION_AND_RECOVERY_DESIGN.md`) |

Coverage is substantial in source but concentrated in NIAM/MPI; several high-risk paths (doc-intelligence orchestrator startup, lifecycle route↔service wiring, NID hash parity, claim repointing on merge) lack a regression test that would catch the verified defects.

---

## 2. Required test levels (target)

### 2.1 Unit
- One digit-normalized NID HMAC contract — equality across `identity.py`, `register.py`, `id_scan.py`.
- NHID format/checksum/uniqueness; never-reused invariant.
- IdentityType canonical↔legacy alias map (NIAM ↔ national).
- Matcher weight/threshold boundaries; blocking recall; `canonical()` chain limit.
- WebAuthn origin/RP config and challenge type (regression for `default=str`).
- `bump_perm_version` call signature parity.
- QR expiry boundary; age-18 transition boundary.
- VerificationPolicy mapping — OCR/NFC = L0.

### 2.2 Integration (synthetic data)
- Registration → MPI resolve → NHID issue/link.
- **Regression: claim repointing on merge** (defect `mpi/resolver.py:367-369`) and unmerge/split.
- Provisional → verified reconciliation; child + guardian; twin non-merge.
- Assisted registration — staff cannot set citizen credentials.
- Document-intelligence orchestrator initialization (regression for missing startup wiring).
- National router mount decision and lifecycle route↔service signature.
- Death notification/confirmation/civil separation and reversal.

### 2.3 Security
- No raw NID at rest / in URLs / in logs; no NID in query strings.
- Admin-only merge; lab ABAC; consent-gated cross-lab read; per-operation scopes.
- Rate limits (id-scan 5/min); MIME/size validation; no image retention.
- WebAuthn/passkey flow correctness; device revocation terminates sessions.
- Dormant plaintext-NID engine remains unactivated; stub `confidence:1.0` connectors gated.
- OCR cannot raise assurance above L0; photo of a card not accepted as proof.

### 2.4 Data & migration
- No raw NID in any identity store; NHID never reused; history preserved after death.
- F-085 unregistered bases (`DocIntelBase` 21, `InsBase` 30) resolved or archived; NR-011 `env.py` delta `+49/-0` preserved.
- Migration chain regression (no destructive migration; backwards compatible).

### 2.5 Accessibility / i18n / low-connectivity
- Arabic-first RTL flows (`frontend-v3/index.html:2`); all identity screens translated.
- Offline modes do not make final verification, merge or death decisions.
- Low-bandwidth behavior with synthetic payloads.

### 2.6 Calibration (blocked pending authorized data)
- OCR Arabic/Iraqi accuracy and confidence distributions measured on representative legally authorized de-identified/synthetic Iraqi data; thresholds set from evidence; engine version + data provenance recorded. → `BLOCKED_BY_EXTERNAL_DEPENDENCY`.

### 2.7 Runtime / E2E (target — currently absent)
- Real app boot + DB + Redis integration journeys with synthetic data; **distinct from contract-envelope tests**.
- Measure and record RPO/RTO (currently `UNMEASURED`); disaster-recovery round trip.
- Only after these pass may any service be labeled E2E/RUNTIME/PRODUCTION verified — changing the completion baseline requires owner approval.

---

## 3. Acceptance gates (map to roadmap phases)

| Gate | Exit criteria | Blocking status |
|---|---|---|
| G1 Identity spine | NID hash parity, NHID uniqueness, type alias map — all unit + integration tests pass with synthetic data | Required before Phase 3 exit |
| G2 MPI correctness | Claim repointing + unmerge regression tests pass; merge authorization/audit verified | Required before Phase 5/6 |
| G3 Auth safety | WebAuthn/reset/revocation defects fixed with regression tests; zero mandatory external cost demonstrated | Required before Phase 4 |
| G4 OCR honesty | Confidence/quality gates; OCR stays L0; calibration plan approved (data access gate) | Required before Phase 4/9 |
| G5 Data integrity | F-085 resolved or formally archived; migration chain green; no raw NID at rest | Required before Phase 2 |
| G6 Runtime E2E | Synthetic-data E2E journeys pass; RPO/RTO measured; completion baseline updated with owner approval | Required before any release-status change |
| G7 Legal/security | Each method's lawful basis + assurance recorded; final safety check green | Required before any rollout |

**Release gate:** all acceptance criteria pass AND owner approves change to `FINAL_DECISION.md` (currently HOLD). This study never flips HOLD.

---

## 4. Architecture decisions register

| ID | Decision | Problem | Alternatives | Advantages | Disadvantages | Legal | Security | Ops/cost | Dependencies | Failure | Reversibility | Evidence | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TST-01 | Contract-envelope tests are not E2E evidence | Completion baseline overstatement | Claim E2E | Honesty | None | None | Neutral | — | None | False readiness | N/A | §0 | `RECOMMENDED` |
| TST-02 | Regression tests for each verified defect | Defects lack catch tests | Rely on existing tests | Prevents recurrence | Test effort | None | Positive | Low | Implementation approval | Defect returns | Reversible | §1, §2.2 | `RECOMMENDED` |
| TST-03 | Synthetic/authorized de-identified data only | Real-data risk | Use production data | Privacy | Data prep effort | Data-protection law | Positive | Low | Data governance | Data breach | Reversible | §0, §2.6 | `RECOMMENDED` |
| TST-04 | Runtime E2E + RPO/RTO measurement before release claim | 0 E2E verified, RPO/RTO unmeasured | Release on contracts | Evidence-based | Infra effort | None | Positive | Moderate | Owner approval | Unproven release | Reversible | §0, §2.7 | `NEEDS_OWNER_DECISION` |
| TST-05 | Calibrate OCR thresholds on authorized data | No benchmarks | Assume numbers | Defensible | Data access | Data-sharing law | Neutral | Moderate | External data | Unsafe thresholds | Reversible | §2.6 | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |

---

## 5. Cross-references

`MASTER_ARCHITECTURE.md` · `EXISTING_CAPABILITY_INVENTORY.md` · `OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md` · `MASTER_PATIENT_INDEX_DESIGN.md` · `SECURITY_AND_PRIVACY_THREAT_MODEL.md` · `IMPLEMENTATION_ROADMAP.md` · `GOVERNANCE/NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md` (read-only baseline).
