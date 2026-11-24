# MPI POST-IMPLEMENTATION INDEPENDENT SECURITY & CORRECTNESS AUDIT — FINDINGS

**Date:** 2026-11-18
**Auditor role:** Independent reviewer (not the implementer)
**Subject:** MPI reliability implementation on `integration/gula-unification-v1` @ `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`
**Target file:** `GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md` (this file — the ONLY file written during this audit)

**Arabic summary:** المراجعة المستقلة وجدت ثغرات `HIGH` تؤدي إلى ربط مريض بهوية خاطئة وإلى إنشاء مرجع مكرر/مفقود. لا توجد ثغرة `CRITICAL`، لكن القرار **REJECT** للتنفيذ الحالي؛ يبقى HOLD كما هو.

---

## 0. Audit method, scope and boundaries (honesty statement)

| Rule from the mandate | How it was honoured |
|---|---|
| No file modification during discovery | Only this findings report was written. No source, test, report, config, governance or migration file was changed. |
| Inspect actual code, not prior reports | All conclusions derive from direct reads of `reliability.py`, `resolver.py`, `api.py`, `canonical_service.py`, `models.py`, `schemas.py`, `matcher.py`, `database.py`, `app/models/canonical_patient.py`, `app/routes/canonical_patient.py` and all MPI tests. Reports MPI-01…MPI-10 were read **only** to test their claims against evidence. |
| No Git operations | No `git` command was executed. Baseline/reference evidence was read from pre-existing files under `/tmp/opencode/mpi-impl/` and `/tmp/opencode/gula-mpi-tests/`. |
| No migrations / DDL / DML on any database | None. The isolated PostgreSQL harness files were **read**, not run. |
| Do not touch `gula-platform` | Not touched. Verified indirectly: HOLD/`FINAL_DECISION` md5 and D-020/D-021 status in the integration repo are unchanged (§4.8). |
| Preserve user work | Verified by mtime and saved numstat (§4.8). |
| No patient data / secrets printed | All examples are explicitly synthetic. |

**Independent verification performed (read-only):** application boot with `PYTHONDONTWRITEBYTECODE=1` and `python -B` produced `routes: 125`, `openapi paths: 1805`, MPI methods `{resolve: post, citizens/{ulid}: get, merge: post, review: get, review/{id}/decide: post, citizens/{ulid}/access: get}`. This matches MPI-04 §4 exactly — no API/OpenAPI change.

---

## 1. Finding counts by severity

| Severity | Count | IDs |
|---|---:|---|
| **CRITICAL** | 0 | — |
| **HIGH** | 3 | AUD-01, AUD-02, AUD-03 |
| **MEDIUM** | 9 | AUD-04 … AUD-12 |
| **LOW** | 2 | AUD-13, AUD-14 |
| **INFORMATIONAL** | 2 | AUD-15, AUD-16 |
| **Total** | **16** | |

"Introduced" means caused by the MPI-01…MPI-10 change set. "Pre-existing" means present in code that predates this change set but is inside the audit scope (notably every write path that can bypass the advisory lock). Each finding is labelled.

---

## 2. Top five risks (ranked)

1. **AUD-01 (HIGH) — `POST /mpi/review/{claim_id}/decide` with `decision="reject"` does not force a new citizen.** It re-scores the same patient; the rejected citizen (or another high-scoring citizen) is silently re-linked. This is a real **wrong-patient identity linkage** path and the "reject" decision is often a no-op. No hash-chained audit entry is written.
2. **AUD-02 (HIGH) — identity-link write endpoints bypass every MPI lock and have no DB uniqueness.** `POST /canonical-patient/link-patient` and `/link-citizen` require only *any authenticated user*, no lab/role check, and `PatientLink`/`CitizenLink` have no unique constraint. Concurrent or malicious calls create duplicate/cross-tenant canonical links → **lost reference / split identity** (pre-existing, but in scope as a lock-bypass write path).
3. **AUD-03 (HIGH) — two connections per MPI request.** The `get_db()` request session holds a connection and an open transaction while `bounded_retry()` opens a *second* `SessionLocal()` connection and waits on the global advisory lock. With the configured pool (5+10 per worker, 10 s timeout, 60 s idle-in-transaction timeout) this produces pool starvation, cascading 503s and reconcile failures under load.
4. **AUD-04 (MEDIUM) — concurrency race on the NID fast path.** The `nid_hash` lookup happens *before* the advisory lock is acquired in the create branch. Two concurrent first-registrations with the same NID both create a citizen; the loser gets `23505` → HTTP 503 instead of the existing citizen. (The advisory lock does not cover the read that decides "create".)
5. **AUD-05/AUD-09 (MEDIUM) — evidence and reconcile defects.** Merge ambiguous-commit reconciliation reuses the request-scoped `db` instead of a fresh session, violating the stated `bounded_retry` contract; and the "actual-code PostgreSQL" harness uses hand-built DDL, stub FKs, `expire_on_commit=False`, a 25+25 connection pool, and calls resolver functions directly — never the HTTP endpoints. Reports overstate what was proven.

---

## 3. Detailed findings

### AUD-01 — "Reject" review decision re-links the patient instead of minting a new citizen

- **Severity:** HIGH
- **Status:** Pre-existing logic, touched by MPI-04 (response capture/commit handling) but not corrected
- **Location:** `backend/app/services/mpi/api.py:416-459` (reject branch), especially `434-447`; `backend/app/services/mpi/resolver.py:388-401` (decide) and `335-366` (candidate query); `backend/app/services/mpi/schemas.py:87-96`; `backend/app/services/mpi/matcher.py:178-187`
- **Triggering scenario:** An admin reviews an ambiguous claim (score 0.70–0.90) linked to citizen A and chooses `reject` ("detach from this citizen and mint a new canonical one"). The claim is deleted (`api.py:431-432`) and `resolve_identity()` is called with `national_id=None`. Because A is still `status="active"` with the same name/DOB/gender/phone, A is still the best candidate with the **same 0.70–0.90 score** → `classify()` returns `"review"` → a **new `pending_review` claim to the same A** is created. If a different citizen B scores ≥0.90, `classify()` returns `"auto_match"` and the patient is **auto-linked to B** with `match_method="probabilistic"`.
- **Patient-data / identity-safety impact:** (a) Wrong-patient linkage: an administrator who rejects a suspected wrong match can silently bind the patient to another person's canonical record without review. (b) False separation: the API returns `status: "rejected"` while the patient remains attached to the rejected citizen. (c) No `MergeAudit` row is written although the endpoint docstring (`api.py:391-393`) promises "Writes a MergeAudit row so the decision is hash-chained" — the decision is unaudited in the integrity ledger.
- **Reproduction (synthetic):** Seed citizens A and B, both active; create a pending claim for patient P→A; seed B's phone/DOB/name so `score(P,B)=0.95` and `score(P,A)=0.80`. `POST /mpi/review/{claim_id}/decide {"decision":"reject","reason":"..."}`. Observe `new_citizen_ulid == B.citizen_ulid` and `match_method == "probabilistic"`, and `SELECT count(*) FROM mpi_merge_audit WHERE event_type IN ('reject','split') = 0`. In the variant without B, observe a new pending claim to A (no separation).
- **Evidence:** `api.py:448-450` comment says *"Force a new citizen even if probabilistic finds another… If one does, mark it manual-review again"* — the code does neither. `resolver.py:391-401` proves review/auto-match reuse `best_candidate`. `matcher.py:183-187` proves the thresholds. No `acquire_audit_chain_lock`/`_write_audit` call exists in the reject branch.
- **Proposed fix:** Add an explicit resolver mode `mint_new_citizen=True` (or a dedicated `create_detached_citizen()`) that bypasses scoring and always creates a fresh `Citizen` + claim, excludes the old citizen id from any candidate query, writes a hash-chained `MergeAudit` decision event (requires D-MPI-4 taxonomy), and runs through `bounded_retry` with a reconcile hook keyed by `(claim_id, decision)`.
- **Proving test:** `test_reject_mints_new_citizen_even_when_high_scoring_alternative_exists` — assert new ULID differs from both old and alternative, `match_method == "new"`, exactly one new audit row, chain still valid.

---

### AUD-02 — Identity-link endpoints bypass the advisory lock, tenant checks and DB uniqueness

- **Severity:** HIGH
- **Status:** Pre-existing (not part of the MPI diff), but it is a live write path that bypasses MPI serialization and is therefore in scope
- **Location:** `backend/app/routes/canonical_patient.py:268-321` (`create_patient_link`, `create_citizen_link`), `:150-195` (merge endpoint); `backend/app/services/mpi/canonical_service.py:173-233`; `backend/app/models/canonical_patient.py:61-104`
- **Triggering scenario:** Any authenticated user calls `POST /canonical-patient/link-patient {"patient_id": X, "canonical_id": Y, ...}` with X from lab 1 and Y from lab 2. Only `get_current_user` is required — no `require_own_lab`, no `require_role`. Concurrent duplicate calls both pass the check-then-insert in `link_patient()`. `PatientLink` and `CitizenLink` declare only `Index(...)`, **no `UniqueConstraint`** on `patient_id`, `citizen_id` or the pair.
- **Patient-data / identity-safety impact:** Cross-tenant identity relinking by a non-admin; duplicate links for one patient/citizen. Because `get_canonical_by_patient()` uses `.first()`, one canonical becomes unreferenced — a **lost reference** — and one human can be represented by two canonical identities across labs.
- **Reproduction (synthetic):** Two threads call `link_patient(db, patient_id=42, canonical_id=7)` concurrently; both see `existing is None`; both insert. `SELECT count(*) FROM patient_links WHERE patient_id=42 = 2`. For the auth case, authenticate as a lab-only user and call the endpoint with a foreign patient/canonical pair — HTTP 200.
- **Evidence:** `canonical_patient.py:274-275, 302-303` dependencies are `get_current_user` only. Model `__table_args__` at `61-67` and `84-90` contain no uniqueness. `canonical_service.py:181-202` / `213-233` are classic TOCTOU with no lock.
- **Proposed fix:** Add `require_own_lab`/role guards to both link endpoints; add DB unique constraints (`UNIQUE(patient_id)`, `UNIQUE(citizen_id)`, optionally `UNIQUE(patient_id, canonical_id)`) via an owner-authorised migration; inside `link_patient`/`link_citizen` use `INSERT … ON CONFLICT DO NOTHING RETURNING` or acquire a transaction-scoped advisory lock and re-check before insert. This overlaps D-MPI-6 (canonical hardening scope) and needs owner approval for the schema part.
- **Proving test:** `test_link_endpoints_reject_cross_lab_and_concurrent_duplicates` — non-owner gets 403; 10 concurrent identical links produce exactly one row; `get_canonical_by_patient()` is stable.

---

### AUD-03 — Connection-pool starvation: request session + retry session per MPI write

- **Severity:** HIGH
- **Status:** Introduced by MPI-04 (bounded_retry wiring)
- **Location:** `backend/app/services/mpi/api.py:156,168-172,207-215` (resolve), `:275,291,311-319` (merge); `backend/app/database.py:189-192,242,284-298`; `backend/app/services/mpi/reliability.py:160-212`
- **Triggering scenario:** Each MPI write endpoint resolves `db: Session = Depends(get_db)` and performs a query **before** `bounded_retry()` (`Patient` lookup at `api.py:168-172`; `_find_merge_replay` at `:291`). That opens a transaction and pins one pooled connection. `bounded_retry()` then calls `_database.SessionLocal()` for every attempt, needing a **second** connection, and may block on the single global advisory lock. With `DB_POOL_SIZE=5`, `DB_MAX_OVERFLOW=10`, `pool_timeout=10s`, reaching ~15 concurrent MPI writes per worker means every request holds one connection while waiting for another — classic self-deadlock until `pool_timeout`.
- **Patient-data / identity-safety impact:** Availability of the national MPI resolve path. Under load, registration returns HTTP 503; an ambiguous retry then also fails to reconcile; `idle_in_transaction_session_timeout='60s'` can kill the request session while it waits, turning a recoverable wait into a hard failure.
- **Reproduction (synthetic, isolated PG):** Set `DB_POOL_SIZE=2`, `DB_MAX_OVERFLOW=0`, `DB_POOL_TIMEOUT=2`; fire 3 concurrent `/mpi/resolve` requests; the third waits 2 s and returns 503 with `MPI resolve could not be committed`. Repeat while another transaction holds `AUDIT_LOCK_KEY` to also trigger the 60 s idle timeout.
- **Evidence:** `get_db()` at `database.py:291-298` creates `SessionLocal()` and only closes at request teardown. `bounded_retry` at `reliability.py:186` calls `session_factory()` = `_database.SessionLocal` (`api.py:212,316`). Pool defaults at `database.py:189-191`; per-connection `idle_in_transaction_session_timeout` at `:236`. The PostgreSQL harness uses `pool_size=25, max_overflow=25, pool_timeout=30` (`test_80_implementation.py:44-46`) and therefore cannot reveal this.
- **Proposed fix:** Release the request `db` before entering `bounded_retry()` (do the ABAC/existence reads, capture scalars, then `db.close()`), or pass the request session into the retry helper and avoid the second connection; give reconcile its own short-lived session factory; add a bounded admission semaphore for MPI writes; add a dedicated pool/monitoring alert.
- **Proving test:** `test_mpi_write_pool_does_not_starve` — pool of 2, 6 concurrent endpoint calls through `TestClient`, assert zero `pool_timeout` 503s and all responses are 200.

---

### AUD-04 — NID fast-path read occurs before the advisory lock; concurrent duplicate NID yields 503

- **Severity:** MEDIUM
- **Status:** Introduced by MPI-01 (lock placement covers the insert, not the decision read)
- **Location:** `backend/app/services/mpi/resolver.py:335-345` (NID lookup), `:403-409` (lock acquired only in the create branch), `reliability.py:46-59`
- **Triggering scenario:** Two concurrent first-time resolves for different local patients with the **same national ID**. Both execute the `nid_hash` SELECT before either commits → both see no hit. Both fall to probabilistic path, do not match, and enter the create branch. The advisory lock serializes the inserts; the second insert violates the partial unique index on `nid_hash` (documented at `models.py:56-57`), raising `23505`, which is classified **permanent** and never retried → `resolve` returns HTTP 503.
- **Patient-data / identity-safety impact:** Failed patient registration/identity resolution for a legitimate patient; client-visible 503 rather than the already-created canonical. No wrong merge, but an avoidable availability and trust defect at national scale.
- **Reproduction (synthetic):** Two threads call `resolve_identity` with `national_id` = same synthetic NID, different `(lab_id, patient_id)`; assert one returns 200 and the other raises `23505`; assert `citizens` has one row for that NID.
- **Evidence:** `resolver.py:335-340` is outside any lock; `acquire_audit_chain_lock(db)` is only at `:409`, after the decision is made; `PERMANENT_SQLSTATES` contains `23505` (`reliability.py:115`).
- **Proposed fix:** Acquire the advisory lock before the NID lookup when a NID is supplied, then re-read under the lock; or catch `23505` on citizen insert and reconcile to the existing `nid_hash` citizen before returning (idempotent NID registration).
- **Proving test:** `test_concurrent_same_nid_resolves_to_one_citizen` — 10 workers, same NID, assert one citizen, zero 5xx, all responses carry the same ULID.

---

### AUD-05 — Merge reconcile reuses the request-scoped session, violating the bounded_retry contract

- **Severity:** MEDIUM
- **Status:** Introduced by MPI-05/MPI-07
- **Location:** `backend/app/services/mpi/api.py:311-312` (`def _reconcile(): return _find_merge_replay(db, ...)`) vs `backend/app/services/mpi/reliability.py:178-180` ("reconcile is called on a fresh session") and `MPI-07_IMPLEMENTATION_REPORT.md:20`; contrast `_resolve_reconcile` at `api.py:78` which correctly creates `_database.SessionLocal()`.
- **Triggering scenario:** An ambiguous merge commit (DB committed, ack lost → transient SQLSTATE). `bounded_retry` has already rolled back and **closed its own** failed session. Reconcile then reads through the *request* `db`, whose transaction was opened earlier by `_find_merge_replay` at `api.py:291`. Today this works only because PostgreSQL defaults to READ COMMITTED; if isolation is raised to REPEATABLE READ/SERIALIZABLE, or the request session was killed by `idle_in_transaction_session_timeout`, the committed merge is invisible → replay → duplicate audit (or 503).
- **Patient-data / identity-safety impact:** Duplicate merge audit rows and possible re-application of state changes on an identity record; or a 503 reported for an already-applied merge.
- **Reproduction (synthetic):** In an isolated PG test, set the request session to REPEATABLE READ and take its snapshot before the merge commits; inject a transient error after commit in `bounded_retry`; assert (current code) reconcile returns `None` and a second audit row is written.
- **Evidence:** Direct source comparison above. The unit test `test_retry_reconciles_ambiguous_commit_before_replay` (`test_mpi_reliability.py:169-189`) uses a **fake** reconcile callable and does not exercise the API wiring, so the defect is untested.
- **Proposed fix:** Change `_reconcile` in `manual_merge` to open its own `_database.SessionLocal()`, query, and close (mirror `_resolve_reconcile`); close the request `db` before `bounded_retry` (also fixes AUD-03).
- **Proving test:** `test_merge_ambiguous_commit_reconciles_on_fresh_session` using a REPEATABLE READ request session; assert one audit row and HTTP 200.

---

### AUD-06 — Swapped-ULID replay racing with the first merge returns HTTP 400, not the original result

- **Severity:** MEDIUM
- **Status:** Introduced by MPI-05/MPI-07 (pre-check outside the lock)
- **Location:** `backend/app/services/mpi/api.py:288-293` (pre-check), `:311-312` (reconcile), `:320-321` (`ValueError` → 400); `backend/app/services/mpi/resolver.py:530-547` (idempotency and cycle checks)
- **Triggering scenario:** A client reconnects and retries a merge with primary/secondary **swapped** while the original merge is still in flight. The pre-check at `:291` sees no audit row. The advisory lock serializes the two; the second call has `secondary` = the first call's (still active) primary and `primary` = the first call's secondary (now merged). The idempotency check at `resolver.py:530` does not match, and the cycle check at `:546` raises `ValueError("citizens already resolve to the same canonical identity")` → HTTP 400.
- **Patient-data / identity-safety impact:** No wrong merge (the cycle guard correctly refuses), but a client-visible failure for an already-successful operation; an operator may retry again or open an incident. Idempotency is not delivered under the exact race the feature claims to cover.
- **Reproduction (synthetic):** Barrier-synchronise two calls to `manual_merge` with `(A,B)` and `(B,A)`, same reason; assert statuses `{200, 200}` (actual: `{200, 400}`) and `manual_merge` audit count == 1.
- **Evidence:** `_find_merge_replay` handles swapping only when it observes a committed audit row; the in-resolver idempotency check is **directed** (`secondary.status == "merged" and secondary.merged_into_id == primary.id`), so it fails for the swapped direction. `MPI-05_IMPLEMENTATION_REPORT.md:38` claims concurrent replay returns the original result; the test `test_merge_replay_reversed_ulids_returns_original_without_new_audit` (`test_mpi_api_reliability.py:50-66`) is sequential and unit-level only.
- **Proposed fix:** In `merge_citizens`, after acquiring the lock, resolve the unordered pair against the audit ledger **in both directions** and return the original row regardless of supplied order; treat the "already resolve to same canonical" condition as idempotent success when an audit row exists for the pair, not as an error.
- **Proving test:** `test_concurrent_swapped_merge_replays_are_both_200`.

---

### AUD-07 — Resolve idempotency key ignores payload; corrected patient identity is silently discarded

- **Severity:** MEDIUM
- **Status:** Pre-existing design, amplified by MPI-05 reconcile
- **Location:** `backend/app/services/mpi/resolver.py:292-309`; `backend/app/services/mpi/api.py:71-98,183-215`
- **Triggering scenario:** A lab corrects a patient's NID/name/DOB and calls `/mpi/resolve` again for the same `(lab_id, patient_id)`. The existing-claim short-circuit returns the original citizen without re-scoring. In the ambiguous-commit case, `_resolve_reconcile` returns the persisted claim with `created=False` for the **new** payload as well.
- **Patient-data / identity-safety impact:** A known-wrong identity link can never be corrected through the resolve API; the error persists silently. Relevant to wrong-patient safety even though no new wrong link is created by this code.
- **Reproduction (synthetic):** Resolve P with NID-A; then call resolve for P with NID-B; assert the returned ULID and stored `nid_hash` still reflect A.
- **Evidence:** `resolver.py:293-309` returns immediately on `existing_claim`; no payload hash is stored on `IdentityClaim` (`models.py:130-147`).
- **Proposed fix:** Owner decision D-MPI-5 is required. Technically: store a payload fingerprint on the claim; on change, either create a new claim version and re-resolve under the lock, or return an explicit 409 "identity changed — use review endpoint" rather than silently returning the stale outcome.
- **Proving test:** `test_resolve_with_changed_payload_does_not_silently_return_stale_citizen`.

---

### AUD-08 — Full audit-chain verifier is inert in production (test-only)

- **Severity:** MEDIUM
- **Status:** Pre-existing helper, unchanged; MPI-08 added segment verification but did not wire the full verifier
- **Location:** `backend/app/services/mpi/resolver.py:230-249`; repository-wide grep shows call sites only in `backend/tests/test_mpi_hash_chain_integrity.py:113,132,151,195,218,265`
- **Triggering scenario:** An out-of-band rewrite or fork of `mpi_merge_audit` rows occurs in production. Nothing calls `verify_merge_audit_chain()`, so no alert, gate, or denial results.
- **Patient-data / identity-safety impact:** The "detection-only" control provides no actual detection unless an operator manually invokes it. Integrity of the identity-decision ledger is unmonitored.
- **Reproduction (synthetic):** Tamper one audit row in a test DB, start the application, wait — no log entry, metric, or endpoint reflects the broken chain.
- **Evidence:** No import/call outside tests; MPI-10 §8 explicitly notes "No fork auto-repair or incident policy" and MPI-07 §5 leaves D-MPI-3/4 to the owner.
- **Proposed fix:** Wire a scheduled governance job / readiness probe / admin endpoint that runs the verifier and emits an alert and metric (`mpi_audit_chain_valid`); define fork-response policy under D-MPI-3/4.
- **Proving test:** `test_tampered_audit_chain_is_reported_by_governance_probe`.

---

### AUD-09 — PostgreSQL "actual-code" evidence does not exercise the application schema, session or endpoints

- **Severity:** MEDIUM
- **Status:** Evidence-quality defect in MPI-09/MPI-10
- **Location:** `/tmp/opencode/gula-mpi-tests/test_80_implementation.py:33-48` (stub tables, `expire_on_commit=False`, pool 25+25/30 s), `:50-81` (hand-built DDL), `:84-101` (schema built by `CREATE TABLE`, not migrations), `:150-157,193-200,221-228,258-262` (calls `resolver.*` directly, never `api.manual_merge`/`api.resolve` via HTTP)
- **Triggering scenario:** A reader treats "73 passed / actual code exercised / PostgreSQL proof" as evidence that the shipped HTTP endpoints are safe under production constraints.
- **Patient-data / identity-safety impact:** The following are **not** validated on PostgreSQL: `expire_on_commit=True` response behaviour, `bounded_retry`, request-scoped reconcile (AUD-05), `decide_pending_review` (AUD-01), real migrations/unique indexes, real `Numeric(4,3)`/`String(500)` constraints (harness uses `NUMERIC(5,3)`, `TEXT`, and omits the `entry_hash` UNIQUE constraint), and the production pool (AUD-03).
- **Reproduction:** Compare harness DDL to `backend/app/services/mpi/models.py:150-187` and `backend/app/database.py:242`; observe divergences; grep harness for `api.` / `TestClient` — absent.
- **Evidence:** `MPI-09_POSTGRESQL_VALIDATION_REPORT.md:43-58` honestly says resolver functions were called, but `:104-105` acceptance criterion "Actual implemented code exercised (not only abstract strategies)" is broader than what was tested.
- **Proposed fix:** Re-run PostgreSQL validation against a database created by the real Alembic chain, with the production `SessionLocal` and `TestClient` calls to `/mpi/resolve`, `/mpi/merge`, `/mpi/review/{id}/decide`, using production pool settings; keep the current harness as strategy-level evidence only.
- **Proving test:** `test_postgres_endpoints_with_migration_schema_and_production_session`.

---

### AUD-10 — Same-pair concurrency test does not assert `worker_errors == 0` while reports claim it

- **Severity:** MEDIUM
- **Status:** Test-quality / report-claim defect
- **Location:** `/tmp/opencode/gula-mpi-tests/test_80_implementation.py:216-242` (records `"worker_errors": len(result["errors"])` at `:241` but asserts only `count == 1` and chain validity at `:235-237`); `/tmp/opencode/gula-mpi-tests/metrics.json:204-216` shows the **strategy-level** `idempotent_concurrent` had `errors: ["23505"]`
- **Triggering scenario:** A regression causes some workers to fail with `23505` or `40001` while still producing one audit row. The test passes; MPI-05 `:38` and MPI-10 `:74` continue to claim `worker_errors=0`.
- **Patient-data / identity-safety impact:** Masks client-visible failures on identity merges; report accepted on evidence the test does not enforce.
- **Reproduction:** Inject an error after the first successful same-pair merge and observe the test still passes.
- **Evidence:** Direct source and metrics comparison. The metrics `implementation.same_pair_10.worker_errors=0` is a single recorded run, not an invariant.
- **Proposed fix:** Add `assert result["errors"] == []`; reconcile MPI-05/MPI-10 language with the strategy-level `23505` outcome (which is handled by the synthetic helper, not by the MPI API).
- **Proving test:** Mutation test that introduces a duplicate write and confirms the test fails.

---

### AUD-11 — Review decisions (confirm/reject) are not written to the hash-chained ledger

- **Severity:** MEDIUM
- **Status:** Pre-existing, but MPI-04 touched these paths
- **Location:** `backend/app/services/mpi/api.py:388-393` (docstring promise), `:403-414` (confirm), `:416-467` (reject); no `_write_audit` call in either branch
- **Triggering scenario:** An admin confirms or rejects an ambiguous identity claim. Only the `IdentityClaim.match_method` is changed (confirm) or the claim is deleted/recreated (reject).
- **Patient-data / identity-safety impact:** High-impact identity adjudications are absent from the tamper-evident ledger; accountability and forensic reconstruction rely on application logs only.
- **Reproduction (synthetic):** Confirm a pending claim; assert `count(MergeAudit where event_type corresponds to decision) == 0`.
- **Evidence:** `resolver._write_audit` call sites are only `resolver.py:427` (create) and `:578` (manual merge).
- **Proposed fix:** Add decision event types under D-MPI-4 and write a chained audit row inside the same transaction (with the advisory lock) for both decisions.
- **Proving test:** `test_review_decisions_append_chained_audit_rows`.

---

### AUD-12 — Canonical merge is described as "audit-logged" but only writes an application log line

- **Severity:** MEDIUM
- **Status:** Pre-existing
- **Location:** `backend/app/routes/canonical_patient.py:156-190` (docstring at `:163` "All merges are audit-logged"; implementation at `:186-190` is `logger.info`), `backend/app/services/mpi/canonical_service.py:96-146` (no audit write)
- **Triggering scenario:** `POST /canonical-patient/merge` merges two canonical identities.
- **Patient-data / identity-safety impact:** Identity merges outside the MPI ledger are not tamper-evident; the route also has no commit-failure rollback/503 translation (`:185` bare `db.commit()`), unlike the MPI endpoints.
- **Reproduction (synthetic):** Merge two canonicals; assert no `MergeAudit` row and inspect log only.
- **Proposed fix:** Emit a chained audit event for canonical merges (owner decision D-MPI-4) and wrap `db.commit()` in the same error handling as MPI endpoints.
- **Proving test:** `test_canonical_merge_appends_audit_and_handles_commit_failure`.

---

### AUD-13 — Broken merge chain silently returns `self`

- **Severity:** LOW
- **Status:** Pre-existing
- **Location:** `backend/app/services/mpi/models.py:99-112` (`canonical()` returns `self` on a >10-hop or broken chain)
- **Triggering scenario:** `merged_into_id` points to a missing/corrupt row or a cycle longer than 10.
- **Patient-data / identity-safety impact:** Consumers (including `_resolve_reconcile` at `api.py:88` and `get_citizen` at `api.py:248`) receive the *non-surviving* identity as if it were canonical, masking corruption.
- **Reproduction (synthetic):** Set `A.merged_into_id = nonexistent_id`; assert `A.canonical().id == A.id` and no error/alert.
- **Proposed fix:** Raise a dedicated `BrokenCanonicalChainError` (or emit a metric) and add a chain-integrity check to the verifier; keep a safe fallback only for read paths that explicitly opt in.
- **Proving test:** `test_broken_canonical_chain_is_detected`.

---

### AUD-14 — Audit hash canonicalization relies on exact numeric/type round-trip (latent mismatch)

- **Severity:** LOW
- **Status:** Latent
- **Location:** `backend/app/services/mpi/resolver.py:92-94` (`_canonical_json` uses `default=str`), `:140-151` (hash-time `match_score_val` is a raw float), `:186-196` (verify-time `float(row.match_score)`), `models.py:176,186` (`Numeric(4,3)`, JSON), harness DDL `NUMERIC(5,3)`/`TEXT`
- **Triggering scenario:** A future audit write supplies a `match_score` with more than 3 decimals, or a `match_features` value that serialises differently through `default=str` at hash time than through the JSONB column at read time.
- **Patient-data / identity-safety impact:** Legitimate rows would fail their own hash verification, producing false tamper alerts (or, if verification is ignored, hiding real tampering).
- **Reproduction (synthetic):** Call `_write_audit(match_score_val=0.91234)`, flush/expire, call `_audit_entry_hash(row)` — mismatch expected against `entry_hash`.
- **Evidence:** Current call sites pass `None` for `match_score_val`, so no live corruption today; the harness schema also diverges, so the tests cannot catch this.
- **Proposed fix:** Normalise every hashed field to its persisted representation before hashing (quantise `match_score` to 3 decimals, serialise `match_features` through the same JSON serializer with `sort_keys=True`), and assert hash reproduction in every audit write test.
- **Proving test:** `test_audit_hash_round_trips_for_non_integer_score`.

---

### AUD-15 — Advisory lock is a single global serialization point (documented throughput ceiling)

- **Severity:** INFORMATIONAL
- **Status:** Accepted design (B + D)
- **Location:** `backend/app/services/mpi/reliability.py:39-59`; `MPI-09:76-95` metrics
- **Observation:** One `AUDIT_LOCK_KEY` serialises all MPI genesis and merge appends. Measured full-stack merge throughput falls from 15.7 ops/s at 2 workers to 3.06 ops/s at 20 workers (p95 77→568 ms). The key is stable/versioned and the one-argument bigint overload is correctly used; no defect, but this is a national-scale capacity constraint that must be sized and monitored.
- **Proposed action:** Capacity plan and alert on lock wait; revisit sharding only with a documented chain model (owner decision).

---

### AUD-16 — Detection-only verification is explicitly accepted; no auto-repair or fork policy exists

- **Severity:** INFORMATIONAL
- **Status:** Owner decision pending (D-MPI-3/4)
- **Location:** `backend/app/services/mpi/resolver.py:230-239` docstring; `MPI-10:102,107,138`
- **Observation:** The implementation intentionally does not repair a forked chain and has no agreed response policy. This is honestly disclosed. It is recorded here so the acceptance decision is explicit rather than implied by "PASS" package verdicts.

---

## 4. Cross-cutting determinations (mandated checks)

### 4.1 Every transaction / commit / rollback path

| Path | Ownership | Commit | Rollback on failure | Audit finding |
|---|---|---|---|---|
| `resolve` (`api.py:207-219`) | `bounded_retry` owns outer transaction; session closed in `finally` | `reliability.py:189` | `:194-195` suppress + close | AUD-03, AUD-04 |
| `manual_merge` (`:314-325`) | same | same | same | AUD-03, AUD-05, AUD-06 |
| `merge_citizens` SAVEPOINT (`resolver.py:559-600`) | nested inside outer | `savepoint.commit()` `:597` (NOT outer commit) | `savepoint.rollback()` `:599` | Correct as designed |
| `decide_pending_review` confirm (`:403-414`) | request `db` | `db.commit()` `:408` | `db.rollback()` `:410` | AUD-11 |
| `decide_pending_review` reject (`:416-467`) | request `db` | `db.commit()` `:461` | `db.rollback()` `:463` | AUD-01, AUD-11 |
| `canonical merge` (`routes/canonical_patient.py:184-185`) | request `db` | bare `db.commit()` | none | AUD-12 |
| canonical link endpoints (`:277-284`, `:305-312`) | request `db` | bare `db.commit()` | none | AUD-02 |

No path commits inside a SAVEPOINT — MPI-04's core claim holds. No path was found that leaves the advisory lock leaked: it is transaction-scoped and every owner either commits, rolls back, or closes the session.

### 4.2 Lost response / ambiguous commit

- Resolve: reconciled by `(lab_id, patient_id)` on a fresh session — **works**, but ignores changed payload (AUD-07).
- Merge: reconciled by unordered pair on the **request** session — fragile (AUD-05); swapped replay under race returns 400 (AUD-06).
- Review confirm/reject and canonical endpoints: **no** retry/reconcile at all (AUD-01, AUD-12).

### 4.3 Advisory lock key stability, acquisition order, deadlock, leakage

- Key derivation is deterministic and versioned (`:39-43`); the 63-bit mask matches PostgreSQL's bigint advisory lock; one-argument overload avoids the two-int keyspace. **Correct.**
- Order in `merge_citizens`: advisory lock (`:507`) → single ascending-id `FOR UPDATE` (`:514-520`) → SAVEPOINT (`:559`). **Correct**; swapped primary/secondary does not create an acquisition cycle. The user source-invariant test still passes.
- `resolve_identity` create branch takes the advisory lock before minting/audit (`:409`), **but after** the NID decision read (AUD-04).
- Lock leakage: none found. Deadlock: none found across MPI paths; the lock is global so only one MPI merge appender runs at a time (AUD-15 throughput).

### 4.4 SQLite compatibility vs PostgreSQL proof

SQLite lock acquisition is an explicit no-op (`reliability.py:55-57`) and tests assert that (`test_mpi_reliability.py:44-47`). SQLite tests therefore prove only logic and SQL portability, **not** locking. The PostgreSQL harness does provide genuine advisory-lock scope evidence (observer blocked across SAVEPOINT until outer rollback, `test_80_implementation.py:275-299`) and genuine fork/lost-update/deadlock baselines — but it is synthetic, hand-DDL, resolver-level, and uses a different session/pool configuration (AUD-09). It is **not** production proof.

### 4.5 Audit hash canonicalization and timestamps

`_write_audit` uses one `occurred_at` instance for both hash and column (`:139-161`) — the original timestamp defect is genuinely fixed. `_occurred_at_iso` normalises naive/aware values to UTC (`:97-111`); `_canonical_json` is sorted and separator-stable (`:92-94`); `_audit_row_dict` is shared by segment and full-chain verification (`:179-202`). Residual numeric/type normalisation risk is AUD-14.

### 4.6 Audit segment verification scope

`_verify_audit_segment(db, first_id=audit.id, expected_prev=expected_prev)` filters `id >= first_id` (`:213-218`). Under the advisory lock no other appender can insert a higher id while our transaction is open, so the segment scope is sound **on PostgreSQL**. On SQLite (no lock) it could include another transaction's rows; this is not exercised. Detection-only by design (AUD-08, AUD-16).

### 4.7 Write paths bypassing the lock

| Write | Lock? | Finding |
|---|---|---|
| `resolver.resolve_identity` auto-match/pending-review claim (no new citizen) | **No advisory lock** (safe: no audit append) | OK |
| `resolver.resolve_identity` create | Yes (after NID read) | AUD-04 |
| `resolver.merge_citizens` | Yes | OK |
| `decide_pending_review` confirm/reject | No (reject's create path acquires it via resolver) | AUD-01, AUD-11 |
| `canonical_service.merge_canonicals` | No (different table; ordered `FOR UPDATE`) | AUD-12 |
| `canonical_service.link_patient/link_citizen` and their endpoints | **No** | AUD-02 |

### 4.8 API/OpenAPI stability and preservation of prior user changes

- Boot check: `routes: 125`, `openapi paths: 1805`, MPI route methods unchanged. **No API/OpenAPI change confirmed independently.**
- `FINAL_DECISION.md` md5 = `effdfeaf10234678d83b2668c4489552`; `HOLD — do not release to production.` present at line 13; `D-020 PENDING_APPROVAL` and `D-021 PENDING_APPROVAL — no approval record exists` at `DECISION_REGISTRY.md:70-71`. **Governance state unchanged.**
- User files retain pre-implementation mtimes: `test_mpi_merge_integrity.py` 2026-11-17 22:53, `test_mpi_hash_chain_integrity.py` 2026-11-17 23:47, `test_security_merge_regression_synthetic.py` 2026-11-17 19:26, `mpi/models.py` 2026-11-14, `mpi/schemas.py` 2026-11-14, `database.py` 2026-11-14, `migrations/env.py` 2026-11-17. Saved numstat diff shows only `resolver.py` (+232/−30), `api.py` (+207/−42), `canonical_service.py` (+19/−6) added to the pre-existing tracked delta. **No user work was lost or overwritten.**

### 4.9 Reports vs evidence

| Report claim | Audit assessment |
|---|---|
| MPI-01 "Fork prevention demonstrated on real PostgreSQL with actual code" | **Supported** for resolver-level appends; not for HTTP endpoints (AUD-09). |
| MPI-02 "Ascending FOR UPDATE on both paths; 0 deadlocks" | **Supported** at source and harness level. |
| MPI-03 "No lost updates" | **Supported** by 20-worker atomic-increment evidence. |
| MPI-04 "No route/method/model changed; response before commit" | **Supported** by independent boot check and source. |
| MPI-05 "Concurrent replay: original result returned, no duplicate mutation" | **Partially supported**: sequential/unit case yes; racing swapped replay returns 400 (AUD-06); strategy harness recorded `23505` (AUD-10). |
| MPI-07 "Reconcile runs on a fresh session" | **Not true for merge** (AUD-05). |
| MPI-08/09 "detection-only, synthetic-only" | **Honest**; but verifier is not wired (AUD-08). |
| MPI-10 `PARTIAL`, HOLD unchanged, no production readiness | **Honest and correct.** |
| MPI-10 "No skipped, weakened or disabled test" | Literally true, but the same-pair test omits an error assertion that reports rely on (AUD-10). |

---

## 5. Wrong-patient merge / lost-reference determination

**Does a wrong-patient merge (identity-linkage) vulnerability exist? — YES.**
- AUD-01: the review "reject" path can auto-link the patient to a different, high-scoring citizen with no review and no audit; in the common case it re-links to the very citizen that was rejected.
- AUD-02 (pre-existing): any authenticated user can relink a patient/citizen to an arbitrary canonical across labs.

**Does a lost-reference vulnerability exist? — YES.**
- AUD-02: duplicate links plus `.first()` lookups strand one canonical row and split one human across two canonical identities.
- AUD-04/AUD-07: failed or stale resolves leave the lab patient pointing at the wrong/absent canonical outcome for a corrected identity.

The advisory lock, ascending row-lock order, atomic version increments, pre-commit response capture and hash-chain fixes are genuine and correct; they do **not** compensate for these decision-layer and authorization-layer defects.

---

## 6. Final verdict

# `REJECT`

**Rationale:** The implementation contains a HIGH-severity wrong-patient identity-linkage path (AUD-01) and a HIGH-severity unauthenticated/tenant-bypassing, lock-bypassing link-write path (AUD-02), plus a HIGH-severity pool-starvation design (AUD-03) that can take the national MPI resolve path offline under load. Nine MEDIUM findings remain, including two where report claims exceed what the tests/evidence enforce. There are no CRITICAL findings and no evidence that any defect has harmed real patient data, but correctness and identity safety are not established for the shipped code.

**What REJECT does and does not mean:**
- It does **not** require reverting any user work, deleting reports, or changing `FINAL_DECISION`/HOLD — all of which remain exactly as found.
- It does **not** dispute the genuinely correct primitives (advisory lock scope, key stability, ascending row locks, atomic increments, pre-commit response capture, honestly-labelled PARTIAL verdict).
- It **does** mean this change set must not be accepted as a correct MPI implementation, and no production-readiness argument may be built from it until AUD-01…AUD-03 are fixed and re-audited. A re-audit after those fixes may consider CONDITIONAL ACCEPT.

---

## 7. Severity-ordered fix plan

| Order | Finding(s) | Fix | Owner gate |
|---:|---|---|---|
| 1 | **AUD-01** | Add explicit `mint_new_citizen` resolver mode; exclude rejected citizen; write chained audit for the decision; use `bounded_retry`. | D-MPI-4 (audit event taxonomy) |
| 2 | **AUD-02** | Add lab/role guards to link endpoints; add DB unique constraints on link tables; use conflict-safe insert under lock. | D-MPI-6 (canonical hardening scope) + migration authorization |
| 3 | **AUD-03** | Release request `db` before `bounded_retry`; single-connection retry/reconcile; admission semaphore; pool alerting. | Engineering (no schema change) |
| 4 | **AUD-04** | Move NID read under the advisory lock or reconcile `23505` to the existing NID citizen. | Engineering |
| 5 | **AUD-05, AUD-06** | Fresh-session merge reconcile; unordered-pair idempotency inside the locked region for swapped replay. | Engineering |
| 6 | **AUD-07** | Payload fingerprint on claims; explicit conflict/update semantics. | D-MPI-5 |
| 7 | **AUD-08, AUD-11, AUD-12, AUD-16** | Wire chain verifier into governance probe; add audit events for review and canonical merges; define fork-response policy. | D-MPI-3 / D-MPI-4 |
| 8 | **AUD-09, AUD-10, AUD-14** | Re-run PG validation with migration schema + production session/pool + HTTP endpoints; assert worker errors; normalise hashed numeric fields. | Engineering (evidence only) |
| 9 | **AUD-13** | Detect broken canonical chains instead of silently returning `self`. | Engineering |
| 10 | **AUD-15** | Capacity plan and lock-wait monitoring for the single global advisory key. | Operations |

**Stop boundary honoured:** no fix was applied, no migration/DDL executed, no Git operation performed, `FINAL_DECISION` and HOLD untouched, D-020/D-021 untouched, and `gula-platform` untouched.

**End of report.**
