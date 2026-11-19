# Production Readiness Delta

Phase 17 of the "P1/P2 INTEGRATED SECURITY, RELIABILITY & ARCHITECTURE
CLOSURE" workstream. Recalculates readiness from the evidence actually
produced across this session's three operations (certificate/TrustFramework
closure → P1 data-integrity/idempotency closure → this integrated
operation), against `docs/qa/GULA_PRODUCTION_READINESS_GAP_MATRIX.md`'s
prior 38-category baseline. No optimistic scoring: a category stays
`UNKNOWN`/`NOT STARTED` unless this session's own evidence moved it.

| Category | Status | Evidence / delta from baseline |
|---|---|---|
| Architecture | PARTIALLY VERIFIED | Unchanged conclusion from `ARCHITECTURE_REGRESSION_DELTA.md`, plus new evidence this session: the `issuer_ca_id` FK-target drift closed (real migration, UP/DOWN/re-UP proven); the sync/async mismatch fully classified (`NIAM_SYNC_ASYNC_MISMATCH_INVENTORY.md`) with 27 of 162 occurrences now closed |
| Security | PARTIALLY VERIFIED | Certificate cluster, TrustFramework, and now the full `trust.py` surface (26/26 endpoints) are VERIFIED with real HTTP proof; `governance`/`federation`/`workflows`/`notifications`/`adaptive_auth`/`admin`/`compliance` (94 occurrences) remain unaudited-for-authorization beyond the engine-crash finding — **not** claimed clean |
| Authorization | PARTIALLY VERIFIED | Platform Authority now covers certificates (6), TrustFramework (3), and all of `trust.py` (11 mutating operations) — 20 real operations with proven 401/403/200 matrices across three separate proof runs this session alone. The 7 other NIAM modules' authorization posture is unverified (not merely "the engine crashes" — once the engine bug is fixed there, capability checks would still need auditing, per the `trust.py` experience where the engine bug and the missing-capability bug were the same commit) |
| Identity | PARTIALLY VERIFIED | Unchanged from prior sessions' extensive NIAM identity work; this session added the idempotency mechanism (a genuine identity-adjacent reliability property) but did not re-audit identity model correctness broadly |
| Data integrity | VERIFIED (for the surfaces touched) | `issuer_ca_id` FK drift closed with a real data-safety check (0 existing rows, structurally impossible to have been populated); idempotency mechanism proven to prevent exactly the duplicate-effect class of data-integrity bug it targets, with real concurrency and failure-injection proof |
| Migrations | VERIFIED (for the two added this session) | `20260908_0004` (FK fix) and `20260908_0005` (idempotency table) both proven UP → DOWN → re-UP against a real, unmodified migration chain; single head confirmed after each; migration-graph-integrity tests pass. The one pre-existing, unrelated broken migration (`pharmacy_drug_substitution_rules`) remains open, unchanged, out of this session's scope |
| Concurrency | PARTIALLY VERIFIED | Two real, independent-connection proofs this session: `TrustFramework`'s row lock (prior operation) and the idempotency mechanism's unique-index-driven serialization (this operation, two real threads, exactly-once business effect proven). Concurrency elsewhere in the 7 unaudited modules is unverified |
| Reliability | PARTIALLY VERIFIED | Idempotency for the four highest-risk credential-issuing operations is now a real, proven property — a meaningful reliability improvement over "none of these were safe to retry" |
| Audit | PARTIALLY VERIFIED | Every operation fixed this session (idempotency's 4 operations' business mutations, `trust.py`'s 11, the one `lifecycle` representative) emits a real `CanonicalAuditService` event, proven present with correct `actor_id`/`uuid` from a fresh database session in every proof run |
| Observability | UNKNOWN | Not examined this session |
| Performance | PARTIALLY VERIFIED (one new data point) | The full backend suite still exceeds its own 300-second internal budget at real-environment runtime (~347s, confirmed again this session when a verification script's missing env vars caused a false failure it was important not to misattribute) — unchanged from the prior session's finding, re-confirmed rather than re-measured from scratch |
| Recovery | UNKNOWN | Not examined this session; downgrade paths for the two new migrations are proven, but broader backup/PITR/failover posture is untouched |
| Interoperability | UNKNOWN | Not examined this session |
| AI safety | NOT STARTED | Out of this session's scope entirely (session touched `app/identity/**` and a handful of unused-import fixes only) |
| Privacy | PARTIALLY VERIFIED (incidental) | The idempotency design explicitly never stores secrets/private-key material (checked and proven this session); no broader privacy audit performed |
| Frontend/backend contract | UNKNOWN | Not examined this session; the four idempotency-wired operations are backward-compatible by construction (new parameter defaults to `None`, unchanged response shape when absent) — a narrow, proven claim, not a general contract audit |
| CI/CD | UNKNOWN (per standing instruction) | Retained at the already-documented platform-level infra-failure signature (0ms runner duration on every check, every push this session) — not relabeled without new evidence, none found |
| Operations | UNKNOWN | Not examined this session |

## What changed since the last matrix (honest delta only)

- **Data integrity**: moved from "PARTIALLY VERIFIED" (certificate/FK
  work not yet done) to a fully evidenced, real-migration-proven state
  for the specific surfaces this session touched.
- **Reliability**: new category-level evidence where none existed
  before — the four idempotency operations went from "no protection" to
  "proven exactly-once under concurrency and failure injection."
- **Security/Authorization**: `trust.py`'s entire surface moved from
  "11 known-vulnerable, undocumented in detail" to "11 fixed, 26/26
  classified, real HTTP proof."
- **Migrations**: two new, real, additive, reversible migrations, both
  proven — no change to migration *risk posture* (still single-head,
  still guarded).

## What did NOT change (explicitly not claimed)

- CI remains UNKNOWN by standing instruction — not re-litigated.
- The 94 remaining category-A and 41 remaining category-F sync/async
  occurrences are unchanged in function (still broken, still
  non-functional-but-authenticated) — only their *classification*
  improved (from "counted" to "counted and 27 of them fixed with a
  proven repeatable pattern").
- No category was moved to `VERIFIED` at the whole-system level. Every
  `VERIFIED` entry above is scoped to "for the surfaces this session
  actually touched," stated explicitly, not implied as system-wide.

## A single unresolved P0/P1 prevents Production classification

Per this operation's own rule. Two real P1s remain open at the time of
this report: `niam-broad-sync-db-mismatch` (94 category-A + 41
category-F occurrences) and the unrelated pre-existing
`pharmacy_drug_substitution_rules` migration defect. **Overall
classification: NOT Production Ready — PARTIALLY VERIFIED, with a
precise, evidenced list of what remains.**

---

## Addendum — Authorization Coverage Batch 4 (Accelerated Security & Authorization Closure)

This addendum reflects **only** the evidence this specific batch
produced (Hospital + password_reset/oauth2/saml, 24 mutating routes
traced). It does not upgrade any category system-wide.

| Category | Delta from prior state |
|---|---|
| Authorization | Hospital's 19 previously-ungated mutating routes (including clinical patient-safety operations) now VERIFIED with role gates + real HTTP proof; OAuth2's platform-global client-registration route now VERIFIED with a role gate. Still PARTIALLY VERIFIED overall — ~64 of 89 mounted routers remain UNKNOWN. |
| Data integrity | One real, proven bug closed: `HospitalService._get_entity`'s `not`-vs-`~` typo (17 call sites unconditionally returned "not found"). 5 more confirmed instances of the identical bug remain open in other domains (radiology, pharmacy, admin) — NOT fixed this batch, registered for a future one. |
| Transaction integrity | One real, proven bug closed: 18 Hospital routes never called `db.commit()`, silently discarding every write. Proven with two genuinely independent DB sessions (the standard shared-session test client masks this class of bug entirely — worth checking in any future domain audit). Not verified as absent elsewhere; only Hospital was checked this batch. |
| Idempotency | Hospital's clinical bed/OT operations already use the proven `ClinicalCommandGuard` mechanism (If-Match version CAS + Idempotency-Key claim/complete/reject) — re-confirmed, not newly built. Facility-structure creates were assessed as not requiring idempotency (a duplicate POST creating a duplicate row is an acceptable retry outcome for non-clinical/non-financial master data, per this session's established heuristic) — not independently proven with a concurrency test this batch. |
| Concurrency | Not the primary focus this batch; Hospital's `update_hospital`/`deactivate_hospital` already use `.with_for_update()` (a prior pass's fix) — the missing-commit bug this batch fixed also means that row lock is now released promptly on commit rather than held until connection close, an incidental concurrency-hygiene improvement. |
| Schema / deployability | Hospital reconfirmed SCHEMA-BLOCKED on real Postgres (13/14 tables unmigrated; the 14th's own migration is itself chain-blocked) — unchanged blocker, re-verified with exact evidence (grep of every migration file), not newly discovered. |

**No category is claimed VERIFIED at the whole-system level.** Every
line above is scoped to what this batch actually traced and proved.
Overall classification unchanged: **NOT Production Ready** — the
schema-blocked domains, the ~64 UNKNOWN routers, and the carried-
forward `adaptive-auth-account-id-idor` P1 all remain open.
