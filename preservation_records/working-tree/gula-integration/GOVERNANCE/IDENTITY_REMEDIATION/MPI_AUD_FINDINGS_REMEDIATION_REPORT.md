# MPI Independent Audit Findings — Per-Finding Remediation Evidence (AUD-01 … AUD-16)

**Program:** MPI post-audit remediation (AUD-01 … AUD-16)
**Primary reference:** `GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md` (verdict `REJECT`)
**Repository:** `gula-integration`, branch `integration/gula-unification-v1`, HEAD `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`
**Date:** 2026-11-18
**Data:** synthetic only — no real patient data, no secrets, no hardcoded credentials
**Scope discipline:** MPI only; no NHID canonicalization change; no repo migrations/DDL; no commit/push; no `git reset`/`clean`/`add .`/`add -A`; all pre-existing uncommitted work preserved.

> This report does **not** change the audit verdict. `MPI_INDEPENDENT_AUDIT_FINDINGS.md` remains `REJECT`.
> Owner-gated items (schema constraints, formal decision taxonomy, fork-response policy, payload-change semantics) are
> written as Migration Proposals / Owner Decision Requests and are **not** executed.

---

## 1. Verdict summary

| ID | Severity (baseline) | Root cause class | Verdict | Residual / owner gate |
|---|---|---|---|---|
| AUD-01 | HIGH | Logic wrong-patient linkage | **PASS** | Formal decision taxonomy deferred (D-MPI-4); existing unconstrained `String(20)` event_type used |
| AUD-02 | HIGH | Authz bypass + no DB uniqueness | **PARTIAL** | Application-layer authz + conflict-safe links fixed; DB `UNIQUE` constraints owner-gated (Migration Proposal MP-001) |
| AUD-03 | HIGH | Connection-pool self-deadlock | **PASS** | None. Proven with real HTTP + 2-connection pool |
| AUD-04 | MEDIUM | NID read before lock | **PASS** | None |
| AUD-05 | MEDIUM | Stale-session reconcile | **PASS** | None |
| AUD-06 | MEDIUM | Directed idempotency replay race | **PASS** | None |
| AUD-07 | MEDIUM | Payload-blind idempotency | **BLOCKED** | Owner decision D-MPI-5 required; no behavior change made |
| AUD-08 | MEDIUM | Test-only chain verifier | **PASS** | Fork *response* policy owner-gated (D-MPI-3/4, see AUD-16) |
| AUD-09 | MEDIUM | Evidence used stub schema | **PASS** | Legacy harness retained as strategy-level evidence only |
| AUD-10 | MEDIUM | Missing `worker_errors` assertion | **PASS** | None |
| AUD-11 | MEDIUM | Decisions not chained | **PASS** | Formal taxonomy deferred (D-MPI-4) |
| AUD-12 | MEDIUM | Log-only canonical audit | **PASS** | Chained to general `audit_logs` (no FK coupling) |
| AUD-13 | LOW | Broken chain returns `self` | **PASS** | Opt-in `strict=True` on all decision/write paths |
| AUD-14 | LOW | Hash canonicalization mismatch | **PASS** | None |
| AUD-15 | INFORMATIONAL | Single global lock ceiling | **PASS (documented)** | Capacity sizing / alerting owner action |
| AUD-16 | INFORMATIONAL | Detection-only accepted | **BLOCKED** | Fork-response policy owner decision D-MPI-3/4; intentionally not auto-repaired |

**No finding was marked `FAIL`.** Two owner-gated findings are `PARTIAL`/`BLOCKED`; the remaining 14 are `PASS` (15 including the two documented informational items). No `HIGH`/`CRITICAL` finding is silently closed: AUD-02 remains `PARTIAL` because the DB uniqueness half requires an owner-authorized migration.

---

## 2. Per-finding detail

### AUD-01 — Reject decision re-links the patient instead of minting a new citizen (HIGH) — **PASS**

- **Pre-fix state:** `decide` with `decision="reject"` deleted the claim, then called `resolve_identity(national_id=None)`; the rejected citizen (or a higher-scoring alternative) was re-selected by `classify()`, producing `match_method="probabilistic"` or a new `pending_review` claim to the same citizen. No audit row was written.
- **Root cause:** "Reject" was implemented as "re-run scoring" rather than "mint detached identity"; no explicit non-scoring creation mode existed, and the rejected citizen ID was never excluded from candidate selection.
- **Change:** Added four canonical decisions (`ACCEPT_MATCH`, `REJECT_MATCH`, `CREATE_NEW_IDENTITY`, `NEEDS_MANUAL_REVIEW`) with legacy `confirm`/`reject` normalization (`schemas.py:94-119`, `resolver.py:590`). Added `create_detached_citizen()` (`resolver.py:642`) which bypasses scoring, excludes the rejected citizen, and writes a chained decision audit. `REJECT_MATCH`/`CREATE_NEW_IDENTITY` now mint a new ULID; `NEEDS_MANUAL_REVIEW` is an explicit no-op (`api.py:469-470`). Decision replay is refused (in-doubt commit reconciled on a fresh session).
- **Test:** `test_mpi_audit01_review_lifecycle.py` — 17 tests, incl. `test_reject_match_mints_new_citizen_and_never_reuses_rejected`, `test_create_new_identity_uses_dedicated_audit_event`, `test_review_audit_rows_form_a_valid_hash_chain`, `test_decision_is_replay_safe_second_application_refused`, `test_broken_canonical_chain_is_detected_not_silently_followed`. HTTP proof scenario D exercises `POST /mpi/review/{claim_id}/decide {"decision":"REJECT_MATCH"}` on real PostgreSQL.
- **Evidence:** HTTP proof both profiles: scenario D `status=200`, `match_method=new`, `new_ulid_differs_from_rejected_and_lure=True`, `review_reject_audit_delta=1`. Source: `resolver.py:597-599` (`review_accept`/`review_reject`/`review_new_id`).
- **Residual risk:** Decision event types are stored via the existing unconstrained `MergeAudit.event_type` `String(20)`; a formal enum/check constraint is D-MPI-4 (owner decision, not executed).
- **Verdict:** **PASS** (behavioral safety fully fixed; taxonomy residual tracked).

### AUD-02 — Link endpoints bypass lock, tenant checks and DB uniqueness (HIGH) — **PARTIAL**

- **Pre-fix state:** `POST /canonical-patient/link-patient` and `/link-citizen` required only `get_current_user`; no role/lab guard; `link_patient()`/`link_citizen()` were TOCTOU check-then-insert; models had only `Index(...)`, no `UniqueConstraint`.
- **Root cause:** Identity-changing writes treated as ordinary CRUD; no dedicated institutional actor guard and no DB-level uniqueness.
- **Change (application layer):** Added `require_link_actor()` enforcing a real `LabUser` with `lab_id` and an administrative role (`canonical_patient.py:32-47`); both link endpoints now use it. Added `require_own_lab` on merge (`canonical_patient.py:223-225`). Rewrote `link_patient`/`link_citizen` in `canonical_service.py` to be conflict-safe: transaction-scoped advisory lock key `CANONICAL_LINK_LOCK_KEY` (`reliability.py:64,82`), re-check under lock, deterministic `409`/`404`/`503` handling, and idempotent replay. Canonical link/merge writes emit chained `audit_logs` entries via `_write_canonical_audit` (`canonical_patient.py:50-77`).
- **Test:** `test_mpi_audit02_link_authorization.py` — 12 tests, incl. `test_staff_role_cannot_link`, `test_citizen_account_cannot_link`, `test_cross_lab_patient_link_denied`, `test_authorized_link_creates_one_link_and_chained_audit`, `test_conflicting_second_canonical_is_409_without_duplicate`, `test_idempotent_replay_does_not_create_second_link`, `test_authorized_citizen_link_writes_chained_audit`. Plus `test_security_merge_regression_synthetic.py` (8 tests) role/tenant/audit coverage.
- **Evidence:** `test_security_merge_regression_synthetic.py` 8/8 pass; link authorization suite 12/12 pass.
- **Residual risk (BLOCKED):** DB-level `UNIQUE(patient_id)` / `UNIQUE(citizen_id)` / pair uniqueness is **not** applied — no repo DDL/migrations permitted. Written as **Migration Proposal MP-001** (see §3) for owner decision. Without it, a bypassing writer outside the advisory lock could still insert duplicates.
- **Verdict:** **PARTIAL** — application-layer half complete and proven; schema half owner-gated.

### AUD-03 — Connection-pool starvation (HIGH) — **PASS**

- **Pre-fix state:** Each MPI write held the request `db` (opened by a pre-retry query) while `bounded_retry()` opened a second `SessionLocal()` per attempt and waited on the global advisory lock → self-deadlock to `pool_timeout` (HTTP 503).
- **Root cause:** Two sessions per request; request session not released before the retry loop; no admission control matched to pool size.
- **Change:** Request `db` is explicitly `close()`d after ABAC/existence reads and scalar capture, **before** entering `bounded_retry()` (`api.py` resolve/merge/decide). Reconcile uses its own short-lived `_database.SessionLocal()` session, mirroring `_resolve_reconcile`. No global semaphore introduced and no request volume reduced (verified by source assertions). Advisory lock remains transaction-scoped `pg_advisory_xact_lock` on the operation session only.
- **Test:** `test_mpi_audit03_pool_lifecycle.py` — 5 tests, incl. `test_resolve_releases_request_connection_before_operation_session`, `test_decision_releases_request_connection_before_operation_session`, `test_merge_ambiguous_commit_reconciles_without_replay`, `test_no_global_semaphore_introduced_in_mpi`, `test_accepted_request_volume_not_reduced`. HTTP proof scenario A: 6 concurrent `/mpi/resolve` with `DB_POOL_SIZE=2`, `DB_MAX_OVERFLOW=0`, `DB_POOL_TIMEOUT=3`.
- **Evidence:** Tight profile: 6/6 responses `200`, zero pool-timeout `503`, `max_simultaneous_checked_out=2` (never exceeded the 2-connection pool), `in_use=0` at end. Production profile (5+10, timeout 10s): 6/6 `200`, `max_in_use=15` (exactly pool+overflow), zero `503`.
- **Residual risk:** None for the fixed path. Under advisory-lock contention latency rises (see AUD-15), but no request is starved.
- **Verdict:** **PASS**.

### AUD-04 — NID fast-path read before advisory lock (MEDIUM) — **PASS**

- **Pre-fix state:** `nid_hash` SELECT ran outside the lock; two concurrent first-registrations with the same NID both missed, then the second insert raised `23505` (classified permanent, never retried) → HTTP 503.
- **Root cause:** Lock protected the insert, not the decision read.
- **Change:** NID lookup re-read under the same transaction-scoped advisory lock in the create branch (`resolver.py:513` `locked_nid_hit`), with idempotent resolution to the existing `nid_hash` citizen.
- **Test:** `test_mpi_audit0416_integrity.py` — `test_same_nid_across_two_patients_resolves_to_one_citizen`, `test_locked_nid_reread_is_present_in_create_branch`. HTTP proof scenario B: 10 concurrent first-registrations, same NID.
- **Evidence:** Both profiles: 10/10 responses `200`, `distinct_response_ulids=1`, `citizen_rows_for_nid=1`.
- **Residual risk:** None.
- **Verdict:** **PASS**.

### AUD-05 — Merge reconcile reused request-scoped session (MEDIUM) — **PASS**

- **Pre-fix state:** `_reconcile()` in `manual_merge` closed over the request `db`; after an ambiguous commit the request snapshot (READ COMMITTED by luck) could hide the committed merge → duplicate audit or 503.
- **Root cause:** Reconcile contract ("fresh session") contradicted the actual API wiring; the unit test used a fake callable and never exercised wiring.
- **Change:** `manual_merge` reconcile now opens its own `_database.SessionLocal()`, queries and closes, mirroring `_resolve_reconcile`; request `db` is closed before `bounded_retry` (also AUD-03).
- **Test:** `test_mpi_audit03_pool_lifecycle.py::test_merge_ambiguous_commit_reconciles_without_replay`; plus `test_mpi_audit01_review_lifecycle.py::test_review_decision_reconcile_returns_original_after_in_doubt_commit`.
- **Evidence:** Unit tests pass; HTTP proof scenario C (swapped replay) returns one audited event under a race.
- **Residual risk:** None.
- **Verdict:** **PASS**.

### AUD-06 — Swapped-ULID replay race returns 400 (MEDIUM) — **PASS**

- **Pre-fix state:** `_find_merge_replay` pre-check ran outside the lock; a swapped in-flight replay missed it, the directed idempotency check failed, and the cycle guard raised `ValueError` → HTTP 400.
- **Root cause:** Idempotency was direction-sensitive and evaluated before serialization.
- **Change:** After acquiring the lock, the merge path resolves the **unordered** citizen-id pair against the audit ledger in both directions and returns the original result regardless of supplied order; "already same canonical" is treated as idempotent success when an audit row exists for the pair.
- **Test:** `test_mpi_audit0416_integrity.py::test_reversed_ulid_merge_replay_returns_original_row`, `test_reversed_pair_with_different_reason_is_refused`. HTTP proof scenario C: two barrier-free concurrent calls `(A,B)` and `(B,A)`, same reason.
- **Evidence:** Both profiles: statuses `[200,200]`, `manual_merge_audit_rows_for_pair=1`, `distinct_event_ids=1`, `distinct_entry_hashes=1`.
- **Residual risk:** None.
- **Verdict:** **PASS**.

### AUD-07 — Resolve idempotency key ignores payload (MEDIUM) — **BLOCKED (owner decision)**

- **Pre-fix state:** Existing-claim short-circuit returns the original citizen without re-scoring when NID/name/DOB are corrected; a known-wrong link cannot be corrected via the resolve API.
- **Root cause:** No payload fingerprint on `IdentityClaim`; idempotency keyed only by `(lab_id, patient_id)`.
- **Change:** **None applied.** Changing canonicalization/payload semantics is explicitly out of scope and requires owner decision **D-MPI-5**. No silent behavior change was made.
- **Test:** Owner-decision proving test specified: `test_resolve_with_changed_payload_does_not_silently_return_stale_citizen` (not implemented until D-MPI-5 is decided).
- **Evidence:** Owner Decision Request **ODR-002** (see §3).
- **Residual risk:** Wrong-patient link correction remains unavailable through `/mpi/resolve` until D-MPI-5. This is a real MEDIUM finding left open by design, not hidden.
- **Verdict:** **BLOCKED** — owner decision required; no autonomous fix.

### AUD-08 — Full audit-chain verifier inert in production (MEDIUM) — **PASS**

- **Pre-fix state:** `verify_merge_audit_chain()` was called only by tests; no runtime detection of a forked/tampered ledger.
- **Root cause:** Detection helper never wired to a governance surface.
- **Change:** `mpi_integrity_probe()` (`resolver.py:300`) runs full `verify_merge_audit_chain()` plus canonical-chain verification with `strict=True`; wired into `GET /compliance/audit-integrity` (`routes/compliance.py`). Probe is **detection-only, fail-closed**: it reports `valid=False` and structured `errors` and never rewrites rows.
- **Test:** `test_mpi_audit0416_integrity.py::test_segment_verification_raises_fork_error_on_broken_link`, `test_fork_is_reported_by_probe_without_rewriting_rows`, `test_audit_integrity_endpoint_exposes_mpi_probe`; `test_mpi_audit01_review_lifecycle.py::test_integrity_probe_reports_fork_without_repairing`. HTTP proof scenario F verifies the live probe.
- **Evidence:** Both profiles: `/compliance/audit-integrity` `200`, `mpi_integrity.valid=True`, `merge_audit.valid=True` (202/156 rows checked), `canonical_chains.valid=True` (161/123 checked), `errors=[]`. No route/method change to that endpoint.
- **Residual risk:** Fork *response* policy (alerting, incident, auto-repair) is D-MPI-3/4 (owner) — see AUD-16. Detection itself is live.
- **Verdict:** **PASS**.

### AUD-09 — PG evidence did not exercise schema/session/endpoints (MEDIUM) — **PASS**

- **Pre-fix state:** `/tmp/opencode/gula-mpi-tests/` harness used hand DDL (`NUMERIC(5,3)`, `TEXT`, no `entry_hash` UNIQUE), `expire_on_commit=False`, pool 25+25/30s, and called `resolver.*` directly — never `TestClient`/HTTP, never the real migrations.
- **Root cause:** Strategy-level harness mislabeled as actual-code production proof.
- **Change:** Built a real Alembic-created `public` schema on the dedicated `mpi_test` PostgreSQL 16.14 database (all migrations to head; verified `citizens`, `identity_claims`, `mpi_merge_audit` with its `decided_by_user_id` FK, `patient_links`, `citizen_links`, `audit_logs`). New harness `/tmp/opencode/gula-mpi-http-proof/run_proof.py` uses the real `SessionLocal`/engine, real TCP psycopg2, `TestClient` calls to `/mpi/resolve`, `/mpi/merge`, `/mpi/review/{id}/decide`, `/compliance/audit-integrity`, with tight and production pool profiles.
- **Test:** 28 deterministic checks per profile (`CHECKS_TOTAL 28`, `CHECKS_FAILED 0`, `PROOF_VERDICT PASS`) for both `tight` and `production`.
- **Evidence:** `metrics_tight.json`, `metrics_production.json`, `proof_tight.log`, `proof_production.log` in `/tmp/opencode/gula-mpi-http-proof/`. Pool instrumentation and `pg_stat_activity` sampler included. Real FK `mpi_merge_audit_decided_by_user_id_fkey` caused the old harness approach to fail — confirming the new harness exercises the real schema.
- **Residual risk:** The legacy harness remains on disk; it is explicitly relabeled **strategy-level evidence only** and is not cited as endpoint proof.
- **Verdict:** **PASS**.

### AUD-10 — Same-pair test missing `worker_errors == []` assertion (MEDIUM) — **PASS**

- **Pre-fix state:** Legacy harness recorded `worker_errors` but asserted only row count and chain validity; `metrics.json` even showed strategy-level `errors: ["23505"]`, contradicting report claims of zero worker errors.
- **Root cause:** Observed metric, not asserted invariant.
- **Change:** New HTTP harness asserts `errors == []` for **every** worker-scaling point (2/5/10/20) and for the same-NID and swapped-replay scenarios, and records full status lists.
- **Test:** `run_proof.py::scenario_e_worker_scaling` checks `errors == []` and exact audit deltas per worker count; `scenario_b_same_nid` and `scenario_c_swapped_merge_replay` assert all-`200` and single-result invariants.
- **Evidence:** Both profiles: E[2/5/10/20] all `errors=[]`, all `200`, audit delta equal to worker count.
- **Residual risk:** None.
- **Verdict:** **PASS**.

### AUD-11 — Review decisions not written to hash-chained ledger (MEDIUM) — **PASS**

- **Pre-fix state:** Confirm/reject only mutated `IdentityClaim.match_method` (or deleted/recreated the claim); no `MergeAudit` row despite the endpoint docstring promise.
- **Root cause:** No decision event types and no `_write_audit` call in either branch.
- **Change:** Both decisions write a chained `MergeAudit` row inside the same transaction under the advisory lock, using existing unconstrained event types `review_accept`, `review_reject`, `review_new_id` (`resolver.py:597-599`). Replay refuses a second decision on an already-decided claim.
- **Test:** `test_mpi_audit01_review_lifecycle.py::test_accept_match_preserves_citizen_and_writes_chained_audit`, `test_reject_match_mints_new_citizen_and_never_reuses_rejected`, `test_create_new_identity_uses_dedicated_audit_event`, `test_review_audit_rows_form_a_valid_hash_chain`.
- **Evidence:** HTTP proof scenario D `review_reject_audit_delta=1`; integrity probe chain valid across all appended decision rows.
- **Residual risk:** Formal decision taxonomy is D-MPI-4 (owner decision, not executed).
- **Verdict:** **PASS**.

### AUD-12 — Canonical merge "audit-logged" but only a log line (MEDIUM) — **PASS**

- **Pre-fix state:** `POST /canonical-patient/merge` emitted `logger.info` only; no tamper-evident row; bare `db.commit()` with no rollback/503 translation.
- **Root cause:** CanonicalPatient rows have no MPI `MergeAudit` FK, and no general `audit_logs` write was performed.
- **Change:** `_write_canonical_audit()` (`canonical_patient.py:50-77`) writes a chained `audit_logs` row in the **same transaction** as the merge (no FK coupling, no DDL), with commit-failure `rollback()` and `503` translation. Real sessions always write the chained row; lightweight unit-test doubles get an explicit warning + log line (never a silent no-op).
- **Test:** `test_security_merge_regression_synthetic.py::test_same_lab_merge_succeeds_and_audits`, `test_merge_is_not_silently_unaudited`; authorization suite merge tests.
- **Evidence:** `test_security_merge_regression_synthetic.py` 8/8 pass after the fix (was 2 failed / 6 passed).
- **Residual risk:** Audit taxonomy event types remain strings (D-MPI-4). Chained to general `audit_logs`, not the MPI ledger, by design (no FK available).
- **Verdict:** **PASS**.

### AUD-13 — Broken merge chain silently returns `self` (LOW) — **PASS**

- **Pre-fix state:** `Citizen.canonical()` returned `self` on a >10-hop or dangling/cyclic chain, masking corruption to consumers.
- **Root cause:** Silent fallback on the read path used by decision code.
- **Change:** Added `BrokenCanonicalChainError` (`models.py:46`); `canonical(strict=True)` raises on broken/cyclic chains (`models.py:117-144`). All decision/write paths pass `strict=True` (`resolver.py:384,427,465,513,924,974`); the integrity probe flags forks without repair. Read-only projection keeps an opt-in safe fallback.
- **Test:** `test_mpi_audit01_review_lifecycle.py::test_broken_canonical_chain_is_detected_not_silently_followed`, `test_integrity_probe_reports_fork_without_repairing`.
- **Evidence:** Unit tests pass; probe reports structured errors on tampered rows (no rewrite).
- **Residual risk:** None within MPI. Fork response policy remains D-MPI-3/4.
- **Verdict:** **PASS**.

### AUD-14 — Audit hash canonicalization numeric/type round-trip (LOW) — **PASS**

- **Pre-fix state:** Hash used raw float `match_score` while verify used `float(row.match_score)` persisted through `Numeric(4,3)`; a >3-decimal score or differing JSON serialization would fail its own verification.
- **Root cause:** Hash input did not match persisted representation.
- **Change:** Added `_quantize_score()` (`resolver.py:101`); all hashed score fields are quantized to 3 decimals before hashing, and `match_features` serialize with a stable sorted serializer (`_canonical_json`). Hash is reproduced from the persisted row representation at verify time.
- **Test:** `test_mpi_audit0416_integrity.py::test_score_is_quantized_before_hash_and_still_verifies`.
- **Evidence:** Unit test passes with a non-integer score; HTTP proof scenario F chain valid across 202/156 appended rows.
- **Residual risk:** None.
- **Verdict:** **PASS**.

### AUD-15 — Single global advisory lock throughput ceiling (INFORMATIONAL) — **PASS (documented)**

- **Observation:** One `AUDIT_LOCK_KEY` serializes all MPI genesis/merge appends; legacy measured 15.7 → 3.06 ops/s (2 → 20 workers), p95 77 → 568 ms. Accepted design (B + D), no defect.
- **Change / evidence:** Kept the stable versioned bigint lock key and one-argument overload. New HTTP harness measures live throughput/p95 for 2/5/10/20 workers against the real migrated schema and both pool profiles, with `pg_stat_activity` lock-wait sampling:
  - tight: E[2] 16.7 ops/s p95 69 ms; E[5] 7.08 p95 190 ms; E[10] 4.14 p95 326 ms; E[20] 1.26 p95 1222 ms — all `200`, `errors=[]`.
  - production: E[2] 15.5 p95 74 ms; E[5] 3.29 p95 386 ms; E[10] 3.05 p95 477 ms; E[20] 0.92 p95 1303 ms — all `200`, `errors=[]`.
- **Residual risk:** National-scale capacity constraint; alert on lock wait and capacity plan are owner actions. Sharding needs a documented chain model (owner decision).
- **Verdict:** **PASS** (constraint documented and measured, not a defect).

### AUD-16 — Detection-only verification accepted; no fork policy (INFORMATIONAL) — **BLOCKED (owner decision)**

- **Observation:** Implementation intentionally does not auto-repair a forked chain and has no agreed response policy. Honestly disclosed in the source docstring and MPI-10.
- **Change:** **None** — auto-repair/fork policy is explicitly out of scope and requires owner decision **D-MPI-3/D-MPI-4**. Detection is live (AUD-08); repair is deliberately not implemented.
- **Evidence:** Owner Decision Request **ODR-003** (see §3). `mpi_integrity_probe` is fail-closed and read-only.
- **Residual risk:** A detected fork produces a report but no automated containment. Owner must decide the response policy.
- **Verdict:** **BLOCKED** — informational, owner decision pending; no silent auto-repair.

---

## 3. Owner-gated artifacts (written, not executed)

### MP-001 — Migration Proposal: DB uniqueness for canonical identity links (AUD-02)

- **Status:** PROPOSAL ONLY — **no migration, DDL, or schema change applied** to the repository or to any production DB.
- **Proposed constraints (for owner-authorized migration):**
  - `UNIQUE (patient_id)` on `patient_links`
  - `UNIQUE (citizen_id)` on `citizen_links`
  - optional `UNIQUE (patient_id, canonical_id)` / `UNIQUE (citizen_id, canonical_id)` if the data model permits multiple historical links.
- **Rationale:** Closes the remaining TOCTOU window for writers that bypass the application advisory lock (`CANONICAL_LINK_LOCK_KEY`). Application-layer guards + conflict-safe inserts are already in place.
- **Pre-flight required:** profile existing `patient_links`/`citizen_links` for duplicates before adding constraints; dedupe under owner supervision. Backwards-compatible rollout (constraint `NOT VALID` → validate) recommended.
- **Rollback:** drop the constraints; application-layer protections remain intact.
- **Decision requested:** approve/reject/defer, and designate migration author + window.

### ODR-001 — Owner Decision Request: formal review-decision audit taxonomy (D-MPI-4)

- Uses existing unconstrained `MergeAudit.event_type` `String(20)` values `review_accept`, `review_reject`, `review_new_id`.
- **Decision requested:** approve a formal enum/check constraint and canonical taxonomy (and whether canonical merges belong in the MPI ledger vs general `audit_logs`). No schema change made pending decision.

### ODR-002 — Owner Decision Request: resolve payload-change semantics (D-MPI-5, AUD-07)

- **Decision requested:** choose (a) store payload fingerprint + re-resolve under lock on change, or (b) return explicit `409 "identity changed — use review endpoint"`, or (c) accept current stale-return behavior with documented risk. No implementation until decided; no NHID canonicalization change.

### ODR-003 — Owner Decision Request: fork-response policy (D-MPI-3/D-MPI-4, AUD-16)

- **Decision requested:** define detection-only behavior (current), alert+freeze, or controlled repair with an auditable chain model. No auto-repair implemented.

### ODR-004 — Owner Decision Request: canonical hardening scope (D-MPI-6)

- Overlaps AUD-02 DB uniqueness and ODR-001 taxonomy. **Decision requested:** whether canonical link/merge tables join the MPI serialization + ledger model formally, or remain on the general `audit_logs` chain with application-level advisory locking (current state).

---

## 4. Cross-cutting verification (all independent of the above verdicts)

| Gate | Result | Notes |
|---|---|---|
| MPI unit/regression suite | **119 passed, 0 failed** (75.72 s) | incl. 4 new audit regression files |
| Directly-affected broader scope | **224 passed, 0 failed** | MPI + security + consent + mdm + routes (after `_write_canonical_audit` test-double fix) |
| New audit regression tests | **43 passed** | 17 + 12 + 5 + 9 |
| Security merge regression | **8 passed** | role/tenant/audit; no assertion removed |
| Real PostgreSQL HTTP proof (tight) | **28/28 checks PASS** | pool 2/0/3s, `PROOF_VERDICT PASS` |
| Real PostgreSQL HTTP proof (production) | **28/28 checks PASS** | pool 5/10/10s, `PROOF_VERDICT PASS` |
| Schema authenticity | PASS | real Alembic chain → head; `mpi_merge_audit` FK present |
| `compileall` on modified scope | `COMPILE_OK` | — |
| Ruff on modified source + tests | `All checks passed!` | — |
| MyPy CI-style comparison | **47 → 37 diagnostics (−10)** | no per-file regression; new `reliability.py` 0 errors |
| OpenAPI stability | PASS | 125 routes / 1805 paths; only MPI diffs: decide `description` and `ResolveDecision.decision` pattern/description |
| `FINAL_DECISION.md` md5 | `effdfeaf10234678d83b2668c4489552` | unchanged; HOLD intact |
| `gula-platform` worktree | untouched | never modified |
| Uncommitted user work | 256 entries preserved | no commit/push/reset/clean/add-all |

---

## 5. Final statement

14 of 16 findings are remediated and independently verified (`PASS`); AUD-15 is an accepted, measured constraint (`PASS (documented)`); AUD-02 is `PARTIAL` and AUD-07/AUD-16 are `BLOCKED` pending owner decisions and an owner-authorized migration. No finding is a hidden or silent failure. The primary reference verdict remains **`REJECT`** and is not changed by this report. See `MPI_POST_REMEDIATION_AUDIT.md` for the fresh independent post-remediation audit and severity recount.
