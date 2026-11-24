# GULA National Identity Architecture Study — API & Integration Contracts

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain `PENDING_APPROVAL`.

---

## 0. Evidence convention

See `MASTER_ARCHITECTURE.md` §0. Labels: `VERIFIED_IN_SOURCE`, `TEST_VERIFIED` (test **source exists** — **not executed here**), `PARTIAL`, `SOURCE_PRESENT`, `DORMANT`, `NOT_IMPLEMENTED`, `BLOCKED`, `UNVERIFIABLE`. Source presence is never runtime verification. **No E2E claim is made from contract-envelope tests**; the completion baseline records 7 journeys as contract-envelope only and 0 E2E/RUNTIME/PRODUCTION-verified services. No tests were run.

---

## 1. Current API surface inventory (verified in source)

| Surface | Prefix / routes | Wiring | Status | Evidence |
|---|---|---|---|---|
| Master Patient Index | `/mpi/resolve`, `/mpi/citizens/{ulid}`, `/mpi/merge`, `/mpi/review*`, `/mpi/citizens/{ulid}/access` | `factory.py:617` | `VERIFIED_IN_SOURCE` / `PARTIAL` | `mpi/api.py:35,41,101,142,182,226,313` |
| NIAM identity | `/niam/*` (24 subrouters incl. lifecycle) | `factory.py:819-820` | `VERIFIED_IN_SOURCE` / `PARTIAL` | `identity/api/router.py:32,41-64` |
| Document intelligence | `/document-intelligence/*` (+ government/collaboration/governance/archive/kg/webhooks/observability/access/semantic/lifecycle) | `factory.py:792-793` | `BLOCKED` (orchestrator never initialized) | `document_intelligence/api/routes.py:39-43` |
| ID card scan | `POST /id-scan/scan` | `factory.py:539,570` | `PARTIAL` | `routes/id_scan.py:25,136-192` |
| National ID verify | `POST /national-id/verify` | `factory.py:604` | `PARTIAL` / `BLOCKED` | `routes/national_identity.py:17-34` |
| Identity lookup | `GET /identity/lookup?national_id=` | routed | `PARTIAL` | `routes/identity.py:67` |
| National citizen/identity/vital | `/national/*` (citizen, family, identity, vital-signs, consent) | **unmounted** | `DORMANT` | `national/api/routes/__init__.py:20-36` |
| Frontend generated client | `client.ts` (incl. `/niam/lifecycle/*`) | build-time | `SOURCE_PRESENT` | `frontend-v3/src/api/generated/client.ts:182-195`; `endpoints.ts` `identityApi` |

---

## 2. Verified contract-level defects

1. **NID in query string** — `GET /identity/lookup?national_id=` (`routes/identity.py:67`) places a protected identifier in URL/query, where it can leak via logs, proxies and browser history. Violates D-IDENTITY-01. → `SECURITY_REVIEW_REQUIRED`.
2. **National ID verify is a stub** — `POST /national-id/verify` refuses stub gateway in production unless demo mode (`routes/national_identity.py:17-34`); no external authority assumed.
3. **Document-intelligence routes unreachable** — all orchestrator-dependent endpoints raise `RuntimeError` at runtime in source (`wiring.py:1039-1042`); contract shapes exist but are non-functional.
4. **National router unmounted** — all `/national/*` citizen/identity/vital-sign contracts are defined but never registered in the app.
5. **Lifecycle route↔service mismatch** — routes `await` a synchronous service function without `db` (`identity/lifecycle/routes.py:460-469` vs `services.py:494-504`).
6. **Generated client drift risk** — client includes `/niam/lifecycle/*` endpoints whose backing OTP is a status stub; contract presence overstates function.

---

## 3. Target contract principles (recommendations)

### 3.1 Shape & safety
- **Versioned APIs** with stable contracts; additive changes preferred; breaking changes versioned.
- **Structured errors** with stable codes (no raw exception text leaked — cf. `_safe_processing_error` pattern in `document_intelligence/api/routes.py:45-46`).
- **Idempotency** for state-changing operations (register, merge, submit verification): idempotency keys or natural keys (MPI already uses `(lab_id, local_patient_id)` at `resolver.py:183-200`).
- **No protected identifiers in URLs/query strings** (NID, raw tokens); use POST bodies or opaque references.
- **Least-privilege dependencies** at router level (current doc-intelligence uses blanket `system:admin` — `routes.py:39-43`; move to per-operation scopes).
- **Pagination limits** already present in places (`limit ≤ 500`, `document_intelligence/api/routes.py:188`); standardize.

### 3.2 Integration boundaries
- External identity/government verification, civil-registry connectors, and NFC are `BLOCKED_BY_EXTERNAL_DEPENDENCY`; define contracts but do not assume availability or sign agreements without owner/legal approval.
- OCR is advisory in contracts: include `needs_confirmation` and per-field confidence; never a "verified" flag from extraction.
- No new orchestration engine; reuse existing queue/outbox and canonical audit.

### 3.3 Contract-vs-runtime honesty
- Test suites that only validate contract envelopes must be labeled as such; they are **not** E2E proof. Acceptance requirements are in `TESTING_AND_ACCEPTANCE_STRATEGY.md`.
- OpenAPI generation must remain byte-stable across study (no changes made here); any future contract change requires regression baseline update (`reports/validation/baseline.json` in the platform repo — not modified here).

---

## 4. Test requirements (design-level; no tests run here)

| Level | Coverage |
|---|---|
| Contract | Schema validation for register/resolve/merge/scan/verify; no NID in query strings; structured error codes. |
| Integration | Wiring regression (doc-intelligence orchestrator initialization; national router mount decision); lifecycle route↔service signature. |
| Security | Authorization per operation; rate limits (id-scan 5/min); no protected data in URLs/logs. |
| Honesty | Mark contract-envelope tests distinctly from E2E; no E2E claim without runtime evidence. |

Synthetic / legally authorized de-identified data only.

---

## 5. Architecture decisions register

| ID | Decision | Problem | Alternatives | Advantages | Disadvantages | Legal | Security | Ops/cost | Dependencies | Failure | Reversibility | Evidence | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| API-01 | Remove NID from query strings | Leakage via URL/logs | Keep lookup | Privacy | Contract change | Data-protection law | Positive | Low | Owner decision | NID exposure | Reversible | §2.1 | `SECURITY_REVIEW_REQUIRED` |
| API-02 | Versioned, structured-error, idempotent contracts | Stability | Ad-hoc | Predictable | Discipline | None | Positive | Low | None | Client breakage | Reversible | §3.1 | `RECOMMENDED` |
| API-03 | Per-operation scopes instead of blanket admin | Over-privilege | Keep `system:admin` | Least privilege | Scope design | None | Positive | Moderate | Role design | Excessive access | Reversible | §2, §3.1 | `RECOMMENDED` |
| API-04 | No contract treated as E2E evidence | Completion-baseline honesty | Claim E2E | Truthful | — | None | Neutral | — | None | False readiness claim | N/A | §0, §3.3 | `RECOMMENDED` |
| API-05 | External verification contracts defined but not activated | No authority available | Assume API | Honest | Functional gap | Legal agreement | Positive | Low | External dependency | Unauthorized calls | Reversible | §3.2 | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |

---

## 6. Open questions

1. Which API surface becomes the canonical public identity contract?
2. Who approves the contract change to remove NID from query strings? (`SECURITY_REVIEW_REQUIRED`.)
3. Should `/national/*` ever be mounted, and under what governance? (`NEEDS_OWNER_DECISION`.)
4. Which operations require idempotency keys in the national rollout?

---

## 7. Cross-references

`MASTER_ARCHITECTURE.md` · `OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md` · `MASTER_PATIENT_INDEX_DESIGN.md` · `CITIZEN_REGISTRATION_DESIGN.md` · `TESTING_AND_ACCEPTANCE_STRATEGY.md` · `SECURITY_AND_PRIVACY_THREAT_MODEL.md` · `IMPLEMENTATION_ROADMAP.md` (Phases 2, 5, 11).
