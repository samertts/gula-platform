# MPI & Health Core — Final Program Status

**Report ID:** MPHC-FS-001
**Date:** 2026-11-18
**Repository:** `gula-integration` · branch `integration/gula-unification-v1` · HEAD `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`
**Scope:** MPI remediation finalization + independent audit + Health Core readiness + acceleration plan. No implementation of Health Core.
**Data:** synthetic only; no real patient data; no secrets.

**Overall status: `PARTIAL / REJECT`** — MPI remediation substantially verified, but the MPI verdict remains `REJECT`, `FINAL_DECISION` remains `HOLD`, three HIGH/owner-gated items are open, and Health Core implementation is authorized only in isolation.

---

## 1. Actual repository state

| Item | Value |
|---|---|
| Branch / HEAD | `integration/gula-unification-v1` @ `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` — matches saved baseline |
| Working-tree entries | **256** at Phase 1 restore (baseline 249 + 7 MPI files); **258** after the 4 new reports below were written (+2 visible in default `git status --porcelain` because `GOVERNANCE/HEALTH_CORE/` and `GOVERNANCE/PROGRAM_STATUS/` are new untracked directories collapsed to single entries; `-uall` shows **463** files). **Zero deletions** in every mode — all prior user work preserved |
| `FINAL_DECISION.md` | md5 `effdfeaf10234678d83b2668c4489552`, verdict **`HOLD — do not release to production`** — unchanged |
| MPI findings reference | `MPI_INDEPENDENT_AUDIT_FINDINGS.md` — verdict **`REJECT`** — unmodified |
| Protected repo `gula-platform` | branch `remediate-security-001`, HEAD `f478676b…`, `git status` **0 entries — UNTOUCHED** |
| New reports this phase | `MPI_FINAL_VERIFICATION_REPORT.md`, `MPI_FINAL_INDEPENDENT_AUDIT.md`, `GOVERNANCE/HEALTH_CORE/HEALTH_CORE_READINESS_ASSESSMENT.md`, this file; §6 appended to `MPI_POST_REMEDIATION_AUDIT.md` |
| Git operations | read-only only; **no commit/push/merge/rebase/PR/deploy**; no `git reset`/`clean`/`add .`/`add -A` |
| Schema | no migration/DDL/schema change; real Alembic schema built only in dedicated `mpi_test` DB for proof; no NHID canonicalization change; no unmerge |

Start-state evidence: `/tmp/opencode/mpi-remediation/START_STATE_REPORT.md`.

---

## 2. What was completed and verified

| Phase | Deliverable | Status |
|---|---|---|
| 1 — State restore | `START_STATE_REPORT.md` (out of repo) | **Done** — branch/HEAD/status/baseline/protected repo/protected artifacts verified |
| 2 — Finish tests | §6 appended to `MPI_POST_REMEDIATION_AUDIT.md` | **Done** — full suite result extracted; single failure classified as pre-existing order-dependent baseline |
| 3 — Independent MPI audit | `MPI_FINAL_VERIFICATION_REPORT.md`, `MPI_FINAL_INDEPENDENT_AUDIT.md` | **Done** — all 16 findings re-inspected against actual source; fresh evidence regenerated |
| 4 — Owner decision review | §6 of this report | **Done** — MP-001 + ODR-001…004 reviewed field by field; **none executed** |
| 5 — Health Core gate | `HEALTH_CORE_READINESS_ASSESSMENT.md` | **Done** — 12 domains classified |
| 6 — Acceleration plan | §9–§10 of this report | **Done** — P0–P5 plan; **no implementation started** |
| 8 — Final status | this file | **Done** |

Fresh evidence regenerated in this session:

- **MPI + AUD regression re-run:** 127 passed, 0 failed (79 s) — `independent_mpi_rerun.log`.
- **Real PostgreSQL HTTP proof artifacts re-opened:** tight + production, 28/28 checks each, real Alembic schema, 5 FKs, 6 scenarios.
- **Source re-read:** all 16 findings (see verification report §2).

---

## 3. Comprehensive test results

| Gate | Result | Evidence |
|---|---|---|
| Full backend suite | **3843 passed, 1 pre-existing order-dependent failure, 27 skipped** (583.82 s, exit 1) | `full_backend_suite.log` |
| MPI + AUD regression (fresh, this session) | **127 passed, 0 failed** | `independent_mpi_rerun.log` |
| New AUD regression files (4) | 43 passed | prior + re-run |
| Security merge regression | 8/8 passed | prior + re-run |
| Real PG HTTP proof — tight (2/0/3) | **28/28 PASS**, max 2 checked out, 0 pool-timeout 503s | `metrics_tight.json` |
| Real PG HTTP proof — production (5/10/10) | **28/28 PASS**, max 15 in use, 0 503s | `metrics_production.json` |
| Ruff (modified scope) | clean | prior run, re-confirmed |
| MyPy CI-style comparison | **47 → 37 diagnostics (−10)**, no per-file regression | prior comparison |
| Compile checks | `COMPILE_OK` | prior run |
| OpenAPI regression | 125 routes / 1805 paths; only additive MPI diffs | prior comparison |

### Full-suite failure classification (Phase 2)

`tests/unit/test_nr011_metadata_discovery.py::TestMetadataDiscovery::test_cross_metadata_foreign_keys_resolve` → `NoReferencedTableError` for `niam_adaptive_mfa_sessions.session_id → niam_user_sessions.id`. The FK is declared in **unchanged** `backend/app/identity/adaptive_auth/models.py:75`; no model defines `niam_user_sessions`; the test **passes alone (1 passed, 3.70 s)**. It is a **pre-existing, order-dependent baseline failure in Identity code**, not MPI-caused, **not skipped, not deleted, not fixed** (out of scope). It is also the same NR-011 named in `FINAL_DECISION.md` as blocking `alembic check`, confirming it predates this work.

**No test was skipped, deleted, had an assertion removed, or had coverage reduced to obtain a pass.**

---

## 4. Final MPI results

**Verdict: `REJECT` (unchanged).** Severity counts (baseline classifications): CRITICAL 0, HIGH 3, MEDIUM 9, LOW 2, INFORMATIONAL 2.

| State | Findings | Count |
|---|---|---|
| PASS / independently re-verified | AUD-01, 03, 04, 05, 06, 08, 09, 10, 11, 12, 13, 14 | 12 |
| PASS (documented constraint) | AUD-15 | 1 |
| PARTIAL (owner-gated) | **AUD-02 (HIGH)** | 1 |
| BLOCKED (owner decision) | AUD-07 (MEDIUM), AUD-16 (INFORMATIONAL) | 2 |
| FAIL | — | 0 |

Acceptance gate: `ACCEPT` is forbidden while any HIGH/CRITICAL finding is open. **AUD-02 (HIGH) is open** (DB `UNIQUE` not applied; MP-001 not authorized), so `REJECT` stands and `HOLD`/`FINAL_DECISION` are untouched. The genuinely fixed primitives are acknowledged: transaction-scoped advisory locks, ascending `FOR UPDATE`, atomic version increments, pre-commit response capture, hash-chain verification, fail-closed fork detection, detached-citizen mint, conflict-safe links, fresh-session reconcile.

---

## 5. Remaining risks

| Risk | Severity | Status |
|---|---|---|
| AUD-02 DB uniqueness absent — a writer bypassing the app advisory lock can still insert duplicate/cross-tenant links and strand a canonical reference (`get_canonical_by_patient().first()`) | **HIGH** | Open — MP-001 pending; app-layer guards proven, DB layer not |
| AUD-07 corrected identity cannot be re-resolved via `/mpi/resolve` — known-wrong link persists | MEDIUM | Open — ODR-002 (D-MPI-5) pending |
| AUD-16 fork detected but no agreed containment/response | INFORMATIONAL | Open — ODR-003 (D-MPI-3/4) pending |
| Formal audit-event taxonomy absent (existing unconstrained `String(20)`) | residual | ODR-001 (D-MPI-4) pending |
| Canonical hardening scope split (MPI ledger vs general `audit_logs`) | residual | ODR-004 (D-MPI-6) pending |
| Single global advisory lock throughput ceiling (production 15.5 → 0.92 ops/s at 2→20 workers, p95 74 → 1303 ms) | INFORMATIONAL | Measured and documented (AUD-15); capacity plan + alert owed by operations |
| `FINAL_DECISION` `HOLD`: security not certified, `MIG-EXISTING` not met (table ownership ADR-B, rollback decision, 51-row snapshot, NR-011) | program | Owner decision; outside MPI scope |
| Full suite has 1 order-dependent Identity failure (NR-011) | baseline | Documented; not MPI-caused; not fixed (out of scope) |

---

## 6. Owner decisions awaiting (Phase 4 — field-by-field review)

**None of the following was executed.** All are proposals/requests only.

### MP-001 — Migration Proposal: DB uniqueness for canonical identity links (AUD-02)

| Field | Review |
|---|---|
| Decision required | Approve / reject / defer a migration adding `UNIQUE(patient_id)` on `patient_links`, `UNIQUE(citizen_id)` on `citizen_links`, optional pair uniqueness; designate author + migration window; approve `NOT VALID → VALID` rollout. |
| Why needed | Close the remaining TOCTOU window for writers that bypass `CANONICAL_LINK_LOCK_KEY`; defense in depth for HIGH AUD-02. |
| Risk of inaction | AUD-02 stays `PARTIAL` → MPI cannot be accepted → Patient Master Record / real result links remain blocked; duplicate links can strand a canonical reference. |
| Legacy data impact | Existing duplicates would block the constraint → profile + dedupe under owner supervision first. `NOT VALID` rollout avoids immediate breakage. |
| Backward compatibility | Narrowing write behavior: reassigning a patient to a different canonical becomes a DB error (app already returns 409). Confirm no supported client performs canonical reassignment. |
| Tests required before approval | Duplicate-profile on production-like snapshot; dedupe rehearsal on disposable clone; `NOT VALID → VALID` transition; 10 concurrent identical links → exactly 1 row; rollback (drop constraint) rehearsal; full suite. |
| Decision owner | Data owner + migration authority (Program Director for the window). |

### ODR-001 — Owner Decision Request: formal review-decision audit taxonomy (D-MPI-4)

| Field | Review |
|---|---|
| Decision required | Approve a formal enum/check constraint for `MergeAudit.event_type`, canonical taxonomy for `review_accept`/`review_reject`/`review_new_id`, and whether canonical merges belong in the MPI ledger or general `audit_logs`. |
| Why needed | Remove residual risk of unconstrained `String(20)` decision events; make adjudication tamper-evident and gate-able. |
| Risk of inaction | AUD-01/11/12 residual taxonomy risk remains; decisions rely on strings with no DB enforcement. |
| Legacy data impact | Existing string-valued rows must stay readable; a CHECK constraint must allow legacy values or be added `NOT VALID`; backfill only under owner supervision. |
| Backward compatibility | No API change (strings unchanged); a DB check may reject new unknown values. |
| Tests required before approval | All existing event_type values fit taxonomy; chain verification across historical rows; new decision append under constraint; rollback rehearsal; full suite. |
| Decision owner | Identity / data governance owner (ADR authority). |

### ODR-002 — Owner Decision Request: resolve payload-change semantics (D-MPI-5, AUD-07)

| Field | Review |
|---|---|
| Decision required | Choose (a) payload fingerprint + re-resolve under lock on change, (b) explicit `409 "identity changed — use review endpoint"`, or (c) accept documented stale-return risk. |
| Why needed | A corrected NID/name/DOB cannot be re-resolved; a known-wrong link persists silently. |
| Risk of inaction | AUD-07 stays open; wrong-patient link correction unavailable through `/mpi/resolve`. |
| Legacy data impact | (a) needs a fingerprint column + backfill/null-safe handling of existing claims; (b) no schema change but new client behavior; (c) none. |
| Backward compatibility | (a) additive field; (b) new 409 clients must handle; (c) unchanged. **No NHID canonicalization change permitted under any option.** |
| Tests required before approval | Changed payload does not silently return stale citizen; concurrent corrected resolve under lock; unchanged-payload idempotency preserved; reconcile/replay; full suite. |
| Decision owner | Identity owner with NHID governance. |

### ODR-003 — Owner Decision Request: fork-response policy (D-MPI-3/4, AUD-16)

| Field | Review |
|---|---|
| Decision required | Define detection-only (current), alert + freeze, or controlled repair with an auditable chain model. |
| Why needed | A detected fork currently yields a report but no containment; an incident-response policy is required. |
| Risk of inaction | AUD-16 stays blocked; no agreed response to ledger tampering; compliance gap. |
| Legacy data impact | Repair would rewrite chain rows — must be owner-authorized and auditable; detection-only has none. |
| Backward compatibility | Detection-only is zero-change; alert+freeze adds operational behavior; repair changes ledger semantics. |
| Tests required before approval | Tampered chain reported by probe; no rewrite under detection-only; (if chosen) repair model on disposable clone; alert delivery; full suite. |
| Decision owner | Security / governance owner (with compliance). |

### ODR-004 — Owner Decision Request: canonical hardening scope (D-MPI-6)

| Field | Review |
|---|---|
| Decision required | Decide whether canonical link/merge tables formally join MPI serialization + ledger model, or remain on general `audit_logs` with application-level advisory locking (current). |
| Why needed | Resolve overlap between AUD-02 DB uniqueness, ODR-001 taxonomy, and the canonical write path. |
| Risk of inaction | AUD-02 residual and taxonomy split remain; two audit models with different guarantees. |
| Legacy data impact | Joining MPI ledger would require FK/backfill (schema change); staying on `audit_logs` keeps current rows valid. |
| Backward compatibility | Staying = no change; joining = new ledger membership semantics requiring migration. |
| Tests required before approval | Chained audit on link/merge; tamper-evidence equivalent to MPI ledger; no duplicate rows under concurrency; full suite. |
| Decision owner | Architecture owner. |

---

## 7. Modules allowed for development (with guardrails)

From `HEALTH_CORE_READINESS_ASSESSMENT.md` — every item below requires §3 guardrails of that report: synthetic fixtures only, no real patient links, no NHID/MPI bypass, clear interfaces, no migrations/DDL, no production activation, no clinical-readiness claim.

- **`SAFE TO DEVELOP` (2):** Practitioner; Organization / Facility.
- **`SAFE WITH ISOLATION` (8):** Medical Record; Encounter; Diagnosis; Clinical Observations; Lab Orders; Specimens; Lab Results; Result Verification.

---

## 8. Modules blocked

- **`BLOCKED BY OWNER DECISION` (1):** Patient Master Record — needs MP-001 + ODR-002 + ODR-004 (+ MPI REJECT as underlying).
- **`BLOCKED BY MPI` (1):** Patient Timeline — cross-service/cross-lab grouping of one patient requires canonical identity; MPI `REJECT` creates wrong-patient grouping risk; AUD-07 blocks corrected-identity re-resolution.
- **All domains:** production activation blocked by `FINAL_DECISION` `HOLD` (security not certified, `MIG-EXISTING` not met).

---

## 9. Fastest safe path to the first integrated patient journey

A **synthetic-only vertical slice**, no canonical identity creation and no MPI writes:

1. Synthetic **Practitioner** + **Organization/Facility** reference data (`SAFE TO DEVELOP`).
2. Synthetic **Encounter** against a patient-reference interface stub (in-memory synthetic patient only) (`SAFE WITH ISOLATION`).
3. Synthetic **Diagnosis** + **Clinical Observations** attached to that encounter.
4. Synthetic **Lab Order** → synthetic **Specimen** (barcode) → synthetic **Lab Result** → synthetic **Result Verification** with reviewer provenance.
5. **Patient Timeline** rendered **only within the single synthetic patient** from the in-memory event stream — this avoids cross-patient/cross-lab canonical grouping, so it does not depend on MPI. (The cross-lab/canonical timeline remains `BLOCKED BY MPI`.)

This demonstrates workflow shape and interface contracts — **not clinical validity**. It cannot be promoted to production until: owner decisions executed → MPI re-audited to at least `CONDITIONAL ACCEPT` → `FINAL_DECISION` `HOLD` lifted by the Program Director.

---

## 10. Phase 6 — acceleration plan P0–P5 (planning only, no implementation started)

Effort estimates are in developer-days for one engineer; "parallel" indicates tasks within a priority that can run concurrently given separate files. All tasks inherit the §7 guardrails.

### P0 — Patient safety, identity and data (owner-gated; engineering support only)

| Task | Affected files (target) | Dependencies | Tests | Acceptance criteria | Risks | Parallel | Effort |
|---|---|---|---|---|---|---|---|
| P0-1 Execute/reject MP-001 after owner decision | migration file (owner-authorized), `canonical_service.py` link paths | Data owner approval; dedupe preflight | duplicate profile; 10-writer concurrency; rollback rehearsal; full suite | `UNIQUE` constraints live or formally deferred with signed risk acceptance; AUD-02 re-audited | legacy duplicates; re-link semantics | No (owner-gated) | 1–2 d after approval |
| P0-2 Execute ODR-001 taxonomy | `mpi/models.py`, `resolver.py`, migration (if check constraint) | ODR-001 decision | historical-row fit; chain verify; full suite | formal taxonomy enforced; AUD-01/11/12 residual closed | legacy event values | No | 1 d after approval |
| P0-3 Execute ODR-002 payload semantics | `resolver.py`, `api.py`, `schemas.py`, optional fingerprint column | ODR-002 decision; no NHID change | AUD-07 proving test; concurrency; full suite | corrected payload no longer silently stale | client 409 handling | No | 1–2 d after approval |
| P0-4 Execute ODR-003/ODR-004 policies | `resolver.py` probe, canonical write path, ops runbook | ODR-003/004 decisions | fork-report/no-rewrite; alert delivery; chain equivalence | agreed fork response + canonical scope documented and tested | ledger rewrite risk | Partial | 1–2 d after approval |
| P0-5 MPI re-audit | governance reports | P0-1…4 executed | full independent audit | verdict reconsidered only with explicit owner authorization | premature ACCEPT | No | 1 d |

### P1 — Patient Master Record + Medical Record

| Task | Affected files (target) | Dependencies | Tests | Acceptance criteria | Risks | Parallel | Effort |
|---|---|---|---|---|---|---|---|
| P1-1 Medical Record synthetic core | new module under `backend/app/capabilities/medical_record/` (scaffolding pattern of `clinical_foundation`) | `PatientIdentityPort` interface stub | synthetic fixture tests; contract tests | record CRUD against synthetic patient; no real links; not routed live | interface drift | Yes (with P1-2) | 3–4 d |
| P1-2 Patient Master Record — design only | interface/contract doc + synthetic adapter; **no schema writes** | P0 complete before any real implementation | contract tests for port | design approved; no MPI bypass; no migration | premature real link | Yes | 2 d (design) |

### P2 — Encounter, Diagnosis, Observations

| Task | Affected files (target) | Dependencies | Tests | Acceptance criteria | Risks | Parallel | Effort |
|---|---|---|---|---|---|---|---|
| P2-1 Encounter capability fill-out | `capabilities/encounter_management/` commands/queries/domain | P1 port stub | existing unit/integration scaffold tests extended | synthetic encounter lifecycle (create/admit/discharge) | dormant scaffold assumptions | Yes (with P2-2/3) | 3–4 d |
| P2-2 Diagnosis coding | `capabilities/clinical_foundation/commands/add_diagnosis.py` + queries | P2-1 encounter contract | unit tests for add/list problems | synthetic ICD coding on synthetic encounter | terminology source | Yes | 2–3 d |
| P2-3 Clinical Observations | `health_data/canonical/models.py`-backed adapter; `clinical_foundation/commands/record_vitals.py` | P2-1 encounter contract | unit tests for vitals/observation | synthetic observation recorded and queryable | unit normalization | Yes | 2–3 d |

### P3 — Laboratory workflow (order → specimen → result → verification)

| Task | Affected files (target) | Dependencies | Tests | Acceptance criteria | Risks | Parallel | Effort |
|---|---|---|---|---|---|---|---|
| P3-1 Lab Order (synthetic) | `models/lab_order.py`-backed synthetic repository | P1 port stub | synthetic order tests | lab-scoped order with synthetic patient | real patient leakage | Yes (with P3-2) | 2–3 d |
| P3-2 Specimen tracking | `sample_tracking/` modules | P3-1 order contract (synthetic) | barcode/state tests | synthetic specimen lifecycle keyed to synthetic order | real barcode data | Yes | 2–3 d |
| P3-3 Lab Result (synthetic) | `models/test_result.py` synthetic adapter only — **no real `citizen_id` FK writes** | P3-2; MPI still REJECT | synthetic result tests | result linked to synthetic citizen fixture; no durable MPI row | direct MPI FK coupling | Partially (after P3-2) | 3–4 d |
| P3-4 Result Verification | new verification module + reviewer provenance | P3-3; ODR-001 for ledger event type | verification/replay tests | synthetic verification with reviewer; chained audit via `audit_logs` | taxonomy pending | No (after P3-3) | 2–3 d |

### P4 — Patient Timeline + service integration

| Task | Affected files (target) | Dependencies | Tests | Acceptance criteria | Risks | Parallel | Effort |
|---|---|---|---|---|---|---|---|
| P4-1 Synthetic single-patient timeline | `capabilities/encounter_management/queries/get_patient_timeline.py` (fill scaffold) | P2 + P3 complete | aggregation tests on synthetic event stream | one synthetic patient's encounters/obs/results in order | cross-patient grouping | No | 3–4 d |
| P4-2 Cross-lab timeline | canonical identity provider | **BLOCKED BY MPI** + owner decisions | — | not started | wrong-patient grouping | — | Blocked |
| P4-3 Service integration contracts | `GOVERNANCE/NATIONAL_SERVICE_CONTRACTS.md`, contract tests | P1–P3 ports stable | contract/governance verification scripts | interfaces documented; no live wiring | scope creep | Yes | 2 d |

### P5 — Web / Android / iOS / Desktop interfaces

| Task | Affected files (target) | Dependencies | Tests | Acceptance criteria | Risks | Parallel | Effort |
|---|---|---|---|---|---|---|---|
| P5-1 Web (frontend-v3) synthetic views | `frontend-v3/src/pages/` synthetic-only development pages | P4-1 synthetic API contracts | vitest + typecheck + lint | synthetic data only; no production API calls | accidental real data binding | Yes (with P5-2/3/4) | 4–6 d |
| P5-2 Android | `mobile-expo/` / `mobile/` | P4-1 contracts | existing mobile tests | synthetic-only screens |同上 | Yes | 4–6 d |
| P5-3 iOS | `mobile-expo/` shared screens | P5-2 | existing tests | synthetic-only screens | platform parity | Yes | 3–5 d |
| P5-4 Desktop | `hospital_desktop/` | P4-1 contracts | existing tests | synthetic-only screens | platform parity | Yes | 3–5 d |

**Sequencing rule:** P0 is a hard gate owned by the Program Director / data owners; P1–P3 can proceed in isolation **now** for the 10 allowed domains; P4-1 requires P2+P3; P4-2 remains blocked until MPI `ACCEPT` + `HOLD` lifted; P5 is interface work against synthetic contracts only and must not be presented as clinically ready.

---

## 11. Ordered next steps

1. **Do not change** `FINAL_DECISION.md` (`HOLD`) or `MPI_INDEPENDENT_AUDIT_FINDINGS.md` (`REJECT`); keep `gula-platform` untouched; keep all 256 uncommitted entries preserved.
2. Present **MP-001** and **ODR-001…004** (§6) to their named owners for a decision; execute nothing autonomously.
3. After owner decisions, re-run MP-001/ODR pre-approval tests (§6) and execute only the approved items; then commission a fresh MPI re-audit.
4. Only with explicit owner authorization may the MPI verdict be reconsidered; only the Program Director may lift `HOLD`.
5. In parallel (no MPI dependency), begin **P1/P2/P3 isolation work** for the 10 allowed domains under §7 guardrails, plus the synthetic P4-1 timeline and P5 interface shells — **development only**, no production activation, no real links, no NHID/MPI bypass, no migrations/DDL, no clinical-readiness claim.
6. Keep the **full-suite NR-011 failure** assigned to the Identity owner as a separate baseline item; do not fix it under MPI scope.
7. Re-verify integrity at the end of every subsequent cycle (FINAL_DECISION md5, verdicts, protected repo, uncommitted count, no commit/push).

---

## 12. Termination declaration

Per the mandate's termination condition: the comprehensive tests finished; the new independent audit was performed and every finding documented; owner decisions are documented (not executed); `HOLD`/`REJECT` remain unchanged; the protected repo is proven untouched; all prior user work is preserved. Because HIGH/owner-gated findings remain open, the correct declaration is:

# `PARTIAL / REJECT` — program not complete; MPI not acceptable; Health Core development permitted only in isolation; awaiting owner decisions.

**End of report.**
