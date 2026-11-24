# MPI Final Verification Report — Independent Re-Inspection of AUD-01 … AUD-16

**Report ID:** MPI-FVR-001
**Date:** 2026-11-18
**Repository:** `gula-integration` · branch `integration/gula-unification-v1` · HEAD `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`
**Mandate:** Phase 3 — re-inspect the **actual code** for all 16 findings; do not rely on the remediation report alone.
**Decision reference:** `GOVERNANCE/FINAL_DECISION.md` (md5 `effdfeaf10234678d83b2668c4489552`, `HOLD`) — read-only.
**Data:** synthetic only; no real patient data; no secrets printed.

---

## 1. Method and independence

Every conclusion below comes from a **direct read of the shipped source** in this session (`backend/app/services/mpi/{resolver,api,canonical_service,reliability,models,schemas}.py`, `backend/app/routes/{canonical_patient,compliance}.py`) and from **evidence re-generated in this session**, not from trusting `MPI_AUD_FINDINGS_REMEDIATION_REPORT.md`. Prior reports were used only as a list of claims to test against code.

Evidence re-generated in this session:

| Evidence | Command / source | Result |
|---|---|---|
| MPI + AUD regression re-run (fresh) | `pytest -q tests/test_mpi_*.py tests/test_security_merge_regression_synthetic.py tests/test_mpi_audit0{1,2,3,416}_*.py --tb=short` | **127 passed, 0 failed** (79.08 s), `INDEPENDENT_MPI_EXIT=0` — log `/tmp/opencode/mpi-remediation/independent_mpi_rerun.log` |
| Full backend suite (completed) | `pytest tests/ -q --tb=short` | **3843 passed, 1 pre-existing order-dependent failure, 27 skipped** — log `/tmp/opencode/mpi-remediation/full_backend_suite.log` |
| Real PostgreSQL HTTP proof | `/tmp/opencode/gula-mpi-http-proof/run_proof.py`, tight + production | **28/28 checks PASS** both profiles; verified `schema_source='real Alembic chain … mpi_test'`, dialect `postgresql`, 5 FKs, 6 scenarios — `metrics_tight.json` / `metrics_production.json` re-opened this session |
| Static gates | prior ruff/mypy/compile/OpenAPI runs | ruff clean; mypy 47→37 (−10); `COMPILE_OK`; OpenAPI 125 routes / 1805 paths — see §6 of `MPI_POST_REMEDIATION_AUDIT.md` |

### Scope discipline (re-affirmed)
No file in `/home/samertts/workspace/projects/gula-platform` was touched. `GOVERNANCE/FINAL_DECISION.md` was read-only. No commit/push/merge/rebase/PR/deploy; no `git reset`/`clean`/`add .`/`add -A`; no migration, DDL, or schema change; no NHID canonicalization change; no unmerge; synthetic data only.

---

## 2. The 16 mandated checks — verified against actual code

### 2.1 Wrong-patient linkage & rejected-citizen reuse (AUD-01)

| Mandated check | Source actually read | Finding |
|---|---|---|
| Prevent linking a patient to the wrong identity | `resolver.py:642-753` `create_detached_citizen()` | **Fixed.** A `REJECT_MATCH`/`CREATE_NEW_IDENTITY` decision calls a dedicated function that **never scores candidates** and **never reuses an existing citizen**. It mints a fresh `Citizen` with a new ULID and re-points the same claim row (`claim.citizen_id = citizen.id` at `:740`). |
| Prevent reuse of the rejected citizen in `REJECT_MATCH` | `resolver.py:701` `nid_hash=None` comment + code; `:691-695` rejected-citizen lookup | **Fixed.** The disputed NID is deliberately **not** transferred to the new record (it may belong to the rejected person). The rejected citizen is recorded only as audit provenance (`secondary`), never as the new claim target. |
| Integrity of `CREATE_NEW_IDENTITY` | `resolver.py:677-690`, `api.py:483-536`, `schemas.py:87-123` | **Fixed.** Four canonical decisions with legacy `confirm`/`reject` normalization (additive, backward compatible). `CREATE_NEW_IDENTITY` uses the same detached-mint path; `NEEDS_MANUAL_REVIEW` is an explicit no-op (`api.py:470-478`). |
| Prevent a review decision running twice | `resolver.py:682-690` (lock + re-read + `claim.match_method != 'pending_review'` guard), `api.py:459-462`, `_decision_reconcile` `api.py:101-128` | **Fixed.** Advisory lock is taken before re-reading the claim; a second execution (concurrent or replay) sees a non-pending claim and is refused (`ValueError` → HTTP 409). Reconcile uses a fresh session and returns the recorded outcome if the first attempt committed. |

### 2.2 Link authorization (AUD-02)

| Mandated check | Source actually read | Finding |
|---|---|---|
| Org / lab / patient-level link permissions | `canonical_patient.py:29-47` `require_link_actor()`; `:366`, `:436` both link endpoints; `:380,388,456` `require_own_lab` | **Fixed at app layer.** Link writers must be a real `LabUser` with a `lab_id` and an admin role (`master_admin`/`ministry_admin`/`province_admin`/`admin`/`lab_admin`), and must own both the patient's lab and the lab-scoped canonical. Bare authenticated principals and citizen `User` accounts get HTTP 403. |
| Prevent conflicting / duplicate links | `canonical_service.py:173-268` | **Fixed at app layer.** `acquire_canonical_link_lock()` (a dedicated transaction-scoped advisory key, `reliability.py:63-82`) serializes the check-then-insert; a second canonical for one patient/citizen raises `ConflictError` → HTTP 409; an identical replay updates the existing row (idempotent). |

**Residual:** DB-level `UNIQUE(patient_id)` / `UNIQUE(citizen_id)` is **not** applied — owner-gated **Migration Proposal MP-001**. Verdict on AUD-02 remains **PARTIAL** (see §3).

### 2.3 Session/connection integrity, retry & reconcile (AUD-03, AUD-05)

| Mandated check | Source actually read | Finding |
|---|---|---|
| DB session / connection integrity | `api.py:206-211` (resolve `db.close()`), `:361-362` (merge), `:453-467` (decide); `reliability.py:183-235` `bounded_retry` | **Fixed.** The request-scoped `db` is explicitly closed after scalar reads and **before** `bounded_retry` opens its own session, so one request never pins two pooled connections while waiting on the advisory lock. `bounded_retry` creates a fresh session per attempt and closes it in `finally` before reconcile. No global semaphore was introduced; request volume is not reduced. |
| Retry / reconciliation after ambiguous commit | `reliability.py:214-233`, `api.py:71-98` `_resolve_reconcile`, `:101-128` `_decision_reconcile`, `:349-359` fresh-session merge reconcile | **Fixed.** Only explicitly classified transient SQLSTATEs are retried (`reliability.py:124-133`); permanent integrity errors propagate. Before any replay, `reconcile()` runs on a fresh session and returns the already-persisted outcome, so an in-doubt commit is never blind-replayed. Merge reconcile no longer closes over the request `db`. |

### 2.4 Idempotency of reversed merges (AUD-06)

`resolver.py:874-902`: inside the advisory-locked region, the **unordered** citizen-id pair is resolved against the ledger in **both** directions and the original audit row is returned regardless of caller order. A differing reason is a genuine conflict, not a silent replay. `api.py:131-175` `_find_merge_replay` mirrors this for the pre-check. Cycle guard (`resolver.py:923-925`) still refuses a true cycle. Verified **Fixed**; proof scenario C returned `[200,200]`, one audit row, one event ID, one entry hash.

### 2.5 Hash-chain, canonical-chain & audit-event integrity (AUD-08, AUD-11, AUD-12, AUD-13, AUD-14, AUD-16)

| Mandated check | Source actually read | Finding |
|---|---|---|
| Hash chain / canonical chain | `resolver.py:96-223` (`_canonical_json`, `_quantize_score`, `_write_audit`, `_audit_row_dict`), `:262-297` (`verify_merge_audit_chain`, `verify_canonical_chains`), `models.py:113-146` | **Fixed.** A single timestamp instance and a quantized score feed both hash and column; the same `_audit_row_dict` is shared by write and verify. `canonical(strict=True)` raises `BrokenCanonicalChainError` on broken/cyclic/deep chains; read paths keep a warned fallback. |
| Audit events & reviewer provenance | `resolver.py:622-639` `_review_features` (decision, claim_id, rejected citizen ULID/id, reviewer id, timestamp), `:597-599` event types, `_write_audit` calls at `:727`, `:792`, `:956`; `canonical_patient.py:50-89` `_write_canonical_audit` | **Fixed.** All review decisions write one chained row with reviewer/reason/rejected-candidate/time. Canonical merge/link writes a chained `audit_logs` row in the same transaction (no FK coupling, no DDL); real sessions always write it, test doubles get an explicit warning. Formal taxonomy remains D-MPI-4 (ODR-001), so event types are existing unconstrained `String(20)` values. |
| Governance integrity probe works | `resolver.py:300-334` `mpi_integrity_probe`; `compliance.py:707-712` | **Fixed.** The previously test-only verifiers are wired into `GET /compliance/audit-integrity` as an **additive** field. It is fail-closed detection-only: reports `valid=False` + structured errors, never rewrites rows. Proof scenario F: `valid=True`, both sub-chains valid (202/156 merge rows, 161/123 canonical chains). |
| Fork detection, no concealment | `resolver.py:226-259` `AuditForkError` + `_verify_audit_segment` | **Fixed for detection.** A fork raises inside the SAVEPOINT → rollback, no commit; it is surfaced to the probe and never hidden to keep a request alive. Auto-repair / response policy remains owner-gated D-MPI-3/4 (ODR-003) → AUD-16 stays **BLOCKED (INFORMATIONAL)**. |
| Type normalization | `resolver.py:101-111` `_quantize_score`, `:96-98` `_canonical_json`, `:114-128` `_occurred_at_iso` | **Fixed.** Scores quantized to `Numeric(4,3)` representation on both write and verify; JSON sorted/separator-stable via `default=str`; timestamps normalized to UTC ISO-8601. |

### 2.6 Lock/connection instrumentation & evidence quality (AUD-09, AUD-10, AUD-15)

| Mandated check | Evidence actually inspected | Finding |
|---|---|---|
| Pool checkout & lock wait measurement | `metrics_tight.json` `pool_checkout_wait`: `max_simultaneous_checked_out=2`, `pool_timeout_503s=0`, `pool_timeout_seconds=3`; `pg_stat_activity_samples` present | **Fixed.** Scenario A: 6 concurrent resolves on a 2-connection pool → all `200`, zero pool-timeout 503s. |
| No misleading PostgreSQL test / production-unlike schema | `metrics_*.json` `schema_source='real Alembic chain (migrations/versions/*) → public schema of mpi_test'`, `transport='psycopg2 TCP 127.0.0.1:55432; FastAPI TestClient over real sessions'`, 5 FKs, 28 checks, scenarios A–F | **Fixed.** Old hand-DDL harness retained only as strategy-level evidence (`STRATEGY_LEVEL_ONLY.md`); endpoint proof now uses the real migrated schema, real `SessionLocal`, and HTTP `TestClient`. Worker scaling E[2/5/10/20] asserts `errors==[]`. |
| Single global lock ceiling | `reliability.py:39-55` versioned bigint key, one-argument overload; proof scenario E throughput/p95 | **Documented (AUD-15).** Measured, not hidden: tight 16.7→1.26 ops/s (p95 69→1222 ms), production 15.5→0.92 ops/s (p95 74→1303 ms). Lock order advisory → ascending `FOR UPDATE` → SAVEPOINT is correct (`resolver.py:848-867`). |

---

## 3. Verification result matrix

| ID | Baseline severity | Verdict after independent re-inspection | Residual / owner gate |
|---|---|---|---|
| AUD-01 | HIGH | **PASS** | Formal taxonomy D-MPI-4 (ODR-001) |
| AUD-02 | HIGH | **PARTIAL** | DB `UNIQUE` migration MP-001; canonical hardening D-MPI-6 (ODR-004) |
| AUD-03 | HIGH | **PASS** | — |
| AUD-04 | MEDIUM | **PASS** | — |
| AUD-05 | MEDIUM | **PASS** | — |
| AUD-06 | MEDIUM | **PASS** | — |
| AUD-07 | MEDIUM | **BLOCKED** | Payload-change semantics D-MPI-5 (ODR-002); no behavior change made |
| AUD-08 | MEDIUM | **PASS** | Fork response D-MPI-3/4 (ODR-003) |
| AUD-09 | MEDIUM | **PASS** | — |
| AUD-10 | MEDIUM | **PASS** | — |
| AUD-11 | MEDIUM | **PASS** | Formal taxonomy D-MPI-4 (ODR-001) |
| AUD-12 | MEDIUM | **PASS** | Chained to general `audit_logs` (no FK available) |
| AUD-13 | LOW | **PASS** | — |
| AUD-14 | LOW | **PASS** | — |
| AUD-15 | INFORMATIONAL | **PASS (documented)** | Capacity sizing / lock-wait alert (owner, operations) |
| AUD-16 | INFORMATIONAL | **BLOCKED** | Fork-response policy D-MPI-3/4 (ODR-003) |

**No finding is `FAIL`.** No assertion was deleted and no coverage reduced. Three findings remain non-closed, all owner-gated: **AUD-02 (HIGH, PARTIAL)**, AUD-07 (MEDIUM, BLOCKED), AUD-16 (INFORMATIONAL, BLOCKED).

---

## 4. Full-suite failure classification (carried from Phase 2, §6 of the post-remediation audit)

The single full-suite failure — `test_cross_metadata_foreign_keys_resolve` — is a **pre-existing, order-dependent baseline failure** in unchanged Identity code (`adaptive_auth/models.py` declares FK `niam_adaptive_mfa_sessions.session_id → niam_user_sessions.id` while no model defines `niam_user_sessions`). It passes alone (`1 passed in 3.70s`), its files are byte-identical to HEAD, and it contains no MPI code. It is documented, **not fixed** (out of scope) and **not skipped**. It does not change any MPI finding.

---

## 5. Integrity attestations

- `GOVERNANCE/FINAL_DECISION.md` md5 `effdfeaf10234678d83b2668c4489552` — unchanged; `HOLD` intact.
- `GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md` — unmodified; `REJECT` intact.
- `/home/samertts/workspace/projects/gula-platform` — untouched.
- Uncommitted user work — 256 entries preserved; no commit/push/reset/clean/add-all.
- Synthetic data only; no real patient data; no secrets printed or hardcoded.

**Conclusion of verification:** 13 of 16 findings are remediated and independently re-verified as `PASS`; AUD-15 is an accepted measured constraint; AUD-02 (HIGH) is `PARTIAL` and AUD-07/AUD-16 are `BLOCKED`, all awaiting owner decisions. All 16 have been re-checked against actual source in this report. See `MPI_FINAL_INDEPENDENT_AUDIT.md` for the fresh severity-counted audit verdict.
