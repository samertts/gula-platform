# GULA SEC-015 — Adversarial Independent Re-Review 2 (OD-001 gate)

**Directive:** `GULA-SEC015-REVIEW-2` · **Mode:** READ-ONLY / ADVERSARIAL VERIFICATION
**Repository:** `gula-integration` · **Branch:** `integration/gula-unification-v1`
**Reviewed HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Reviewer:** fresh-context adversarial reviewer (this session) · **Date:** 2026-11-20
**Prior reviewer:** `ses_e0a984dadffemm3LClZf6oKOPo` (PASS, engineering scope) — **not relied upon for this verdict**

---

## 1. Executive verdict

**FINAL VERDICT: PASS WITH CONDITIONS.**

No CRITICAL or HIGH finding was identified. The SQLite serialization fix is demonstrated at the database level in both journal modes and across processes; the PostgreSQL path is correct **in the application's actual configuration (READ COMMITTED)**; tamper detection remains effective; the public `log_action()` contract is unchanged; and fresh source-tied test runs reproduce the green result.

However, this review **independently reproduced an audit-chain fork under PostgreSQL `REPEATABLE READ` and `SERIALIZABLE`**. The advisory lock does not protect those isolation levels because the transaction snapshot is established before (or at) lock acquisition, and the application neither enforces READ COMMITTED nor rejects other levels. The prior review recorded this only as a "documented, non-blocking latent precondition." Empirical reproduction elevates it to a **MEDIUM condition with a mandatory owner action**: enforce the supported isolation level (or explicitly reject unsupported levels) and re-verify before OD-001 can be accepted.

**OD-001 remains `BLOCKED`.** This report does not award `INDEPENDENTLY VERIFIED`, does not authorize a commit, and does not change release posture (`HOLD`; Stable v1.0.0 not declared; no `PRODUCTION READY`).

---

## 2. Exact source revision reviewed

| Item | Value |
|---|---|
| Repository / worktree | `/home/samertts/workspace/projects/gula-integration` |
| Branch | `integration/gula-unification-v1` |
| HEAD (commit) | `2206654dc713ea2de8c564a3207dfe05fde23549` |
| Source under review is **uncommitted working-tree state** (HEAD + modified files), not a tagged release | yes |
| `backend/app/services/audit_service.py` MD5 | `40c2598a02319b00c0351ddc689f7ed7` |
| `backend/tests/unit/test_audit_chain_integrity.py` MD5 | `501e5fc8eb26f1cbd1824b5cfff61975` |
| `backend/tests/test_compliance_integrity.py` MD5 | `eb07739eefd982faf30ed673d23fd73d` |
| `GULA_SEC015_AUDIT_CHAIN_REMEDIATION_REPORT.md` MD5 | `677ea163f566ba7e788ed3d9d9782851` |
| Staged state at start and end | 20 staged `R100` renames; staged count 20; staged name-status MD5 `56c524d6ffe9872c3a3ac6eff8c8f203` |
| `git diff --check` | exit 0 (start and end) |
| Protected MD5s | `GOVERNANCE/FINAL_DECISION.md` = `effdfeaf10234678d83b2668c4489552`; `MPI_FINAL_INDEPENDENT_AUDIT.md` = `1a02c01563c93b07a7cdb92c0462bf36`; `MPI_INDEPENDENT_AUDIT_FINDINGS.md` = `ea3969d09aaf7b0b28a065838b44a594` — all exact |
| Sibling `gula-platform` HEAD (read-only, authoritative loose ref `refs/heads/remediate-security-001`) | `f478676b6fc375338648dde46fbf076c015a3f91` — unchanged |
| Sibling worktree | never entered; no git command executed with it as working directory; its `backend/.venv` was **not used** |

**Revision-identity limitation:** the pre-existing raw logs do not embed a git HEAD or working-tree hash, so those specific artifacts cannot be cryptographically tied to this revision. This review therefore generated **fresh evidence directly against the MD5-identified working tree above** (§10).

---

## 3. Scope and exclusions

**In scope:** `audit_service.py` (locking, hash computation, verification, anchor), the two named test files, `AuditLog` model, append-only migration triggers, `verify_audit_chain()` call sites, `log_action()` call sites (206 across 59 files), historical commits `2cdc5479` / `f0b021bd3` / `2fb4fd11`, and all six prescribed raw logs.

**Excluded / not authorized:** full backend suite rerun; source/test/migration/config edits; staging, commit, push, merge, PR, deployment; production DB, shared Redis/RabbitMQ/MinIO; PHI, credentials, secrets; unrelated architecture refactoring; `shared/audit/service.py` schema mismatch (separate `BLOCKED` item); release/production-approval decisions.

**Disposable environments used:** (a) a `/tmp/opencode` SQLite probe using stdlib `sqlite3` and fresh temp files; (b) a new PostgreSQL 16.14 container `sec015-review2-pg16` on isolated port `55433` with test-only credentials, removed after testing; (c) a fresh `/tmp/opencode/sec015_review2_venv` Python 3.12.13 environment installed from the repo's own `backend/requirements.txt`. The shared `gula-postgres` container was never contacted.

---

## 4. Root-cause reproduction evidence

**Independently established from source history and raw evidence — not from developer comments.**

| Check | Evidence | Result |
|---|---|---|
| Historical correct implementation | `git show 2cdc5479:backend/app/services/audit_service.py` | `prev_hash = _get_last_chain_hash(db)` executed **before** the dialect branch / `db.add(entry)`. Correct. |
| Historical faulty implementation | `git show f0b021bd3:backend/app/services/audit_service.py` | SQLite branch: `db.add(entry); db.flush(); prev_hash = _get_last_chain_hash(db)` — predecessor read **after** insert. |
| Defect reproduces | `/tmp/opencode/sec015_red_baseline.log` | 7 failed / 6 passed. `test_two_sequential_events_link_to_predecessor`: stored hash `83c117…` ≠ recomputed `3dfa6f…`; `test_persisted_hash_verification_without_repair`: `assert 'tampered' == 'intact'`; AST guard: `assert 229 < 227` (predecessor read after insert). |
| Mechanism | `_get_last_chain_hash()` = `SELECT chain_hash FROM audit_logs ORDER BY id DESC LIMIT 1` (audit_service.py:117-123) | After `flush()` the new row is max-id and its `chain_hash` is `NULL`, so the helper returns `_GENESIS_HASH` for every row. Confirmed. |
| Current fix removes defect | current source MD5 `40c2598a…` + fresh run `/tmp/opencode/sec015_review2_focused.log` | 13/13 passed. Both branches read predecessor before `db.add()`; `UPDATE audit_logs` precedes read in SQLite branch; `pg_advisory_xact_lock` precedes read in PG branch (AST guard test passes). |
| No manual re-stitching | `test_compliance_integrity.py::_seed_chain_persisted` (lines 58-77) | `db.expire_all()` then returns persisted rows; no hash rewriting. Fresh related run 73/73 passed. |
| Timestamps / deterministic ordering | `_canonical_audit_timestamp()` (lines 59-73) + tests `test_timestamp_uses_canonical_utc_representation`, `TestAuditTimestampCanonicalization` | Write-time and verify-time hashes identical for aware and naive UTC representations; deterministic JSON with `sort_keys=True`. Confirmed. |

**Conclusion:** root cause is genuine, historically introduced by `f0b021bd3`, and corrected by the current implementation. The original defect cannot be reproduced against the current code.

---

## 5. SQLite locking analysis

**Probe:** `/tmp/opencode/sec015_review2_sqlite_probe.py` → `/tmp/opencode/sec015_review2_sqlite_probe.log` and `..._mp.log`; SQLite 3.37.2; fresh temp DB files; exact statement `UPDATE audit_logs SET id = id WHERE 1 = 0`; two connections in-process plus four separate OS processes; `timeout=0.2s` (and 5 s for the process test).

| Adversarial question | Observed result |
|---|---|
| Does a zero-row `UPDATE` acquire a write reservation? | **Yes.** `in_transaction=True` immediately after executing it on an **empty** table (both rollback-journal and WAL modes). |
| Does the reservation persist until caller commit? | **Yes.** A second connection executing the same `UPDATE` returned `database is locked`; after the holder's `COMMIT` the second connection acquired it. |
| Do separate connections serialize? | **Yes.** Concurrent writer blocked; concurrent **reader** succeeded (RESERVED permits reads), so the fix does not block verification/reads. |
| Do separate processes serialize? | **Yes.** 4 processes → all OK; rows formed a single nested chain `W0:GENESIS → W2:W0:… → W1:W2:… → W3:W1:…`; 4 distinct hashes, no fork. |
| Can a writer read a stale predecessor? | **No.** With A holding the lock and an uncommitted row inserted, B could not acquire the lock at all (`database is locked`), so B never reached the predecessor `SELECT`. |
| Lock contention / busy timeout / retry safety | Contention surfaces as a catchable `OperationalError`; the test's 10-attempt rollback-and-retry pattern is appropriate (see F-04). |
| Rollback releases reservation | **Yes** — after A `ROLLBACK`, a fresh connection acquired the lock. |
| Process termination mid-transaction | Child killed with `SIGKILL` while holding an uncommitted insert; on reopen, orphan row absent (`orphan_rows=0`), DB consistent, writer lock acquirable. |
| WAL vs rollback journal | Identical results in both modes; no changed correctness assumption. |
| Connection pooling/reuse | No unsafe behavior observed; lock is transaction-scoped, not connection-scoped, and is released on commit/rollback/close. |
| Process-level lock substituted? | **No.** DB-level proof obtained; no `threading.Lock`/`RLock` is used for chain serialization in production code. |

**Conclusion:** SQLite transaction-level serialization is demonstrated. The zero-row `UPDATE` is not optimized away and holds the write transaction to the caller's commit boundary.

---

## 6. PostgreSQL locking and isolation analysis

**Probes:** `/tmp/opencode/sec015_review2_pg_probe.py` → `..._pg_probe.log`; `/tmp/opencode/sec015_review2_pg_isolation_nosnap.py` → `..._nosnap.log`. Target: disposable `postgres:16-alpine` **16.14**, port 55433, DB `gula_audit_verify`, test-only credentials, 4 threads × own engine/connection, advisory key `0x47554C4155444954` = `5140098393200413012` (BIGINT-safe). The exact app SQL semantics were replicated (advisory lock → `nextval(pg_get_serial_sequence('audit_logs','id'))` → `SELECT chain_hash … ORDER BY id DESC LIMIT 1` → INSERT). Shared `gula-postgres` untouched.

| Property | Result |
|---|---|
| Lock precedes predecessor retrieval | **Yes** in source (lines 231-241) and in probe. |
| Same namespace/key for all writers | **Yes** — one module-level constant. |
| Transaction-scoped lifetime | **Yes** — `pg_advisory_xact_lock`; released on commit **and** on rollback (probe: blocked writer B proceeded after A's `ROLLBACK`, 0.374 s). |
| Concurrent writers cannot fork under default isolation | **Confirmed at READ COMMITTED**: B waited 1.27 s, then read A's committed hash; 12-row prior harness and 2-row probe both intact. |
| Sequence allocation | `nextval` is non-transactional: rollback consumed id 1, next writer received id 2 — benign **gap**, no duplicate/missing logical event. Allocation occurs inside the lock, so id order equals chain order. |
| Append-only triggers | Probe confirmed `UPDATE` and `DELETE` both rejected; migration `20250322_0002` defines the same triggers in production. |
| Retry behavior | Rollback-and-retry creates no duplicate events (gaps only); no retry loop in `log_action()` itself. |
| **READ COMMITTED** | **INTACT** (broken=[]). |
| **REPEATABLE READ** | **FORKED** — `broken=[2]`; B's predecessor was genesis despite waiting 1.32 s for the lock. Reproduced both with an explicit pre-lock `SELECT 1` and with the advisory lock as the first data statement. |
| **SERIALIZABLE** | **FORKED** — `broken=[2]`; same mechanism, no serialization error raised. |
| Application enforcement of isolation | **None found.** `grep -rIn "isolation_level\|READ COMMITTED\|REPEATABLE READ\|SERIALIZABLE" backend/app --include=*.py` returned only unrelated matches (MPI comment, reliability enum, kernel sandbox context); no engine/session/location sets or checks a DB isolation level. |

**Conclusion:** PG correctness is demonstrated **only** for READ COMMITTED. The prior MEDIUM finding is empirically confirmed as a real fork under two standard isolation levels. Because the application never changes the level, the production configuration remains correct, but the guarantee is an **unenforced precondition** (Finding F-01).

---

## 7. Concurrency and transaction findings

| Topic | Finding |
|---|---|
| SQLite concurrency | Serialized at DB level; cross-process chain single and unbroken (§5). |
| PG concurrency at READ COMMITTED | Serialized; 4×3 rows single unbroken chain (prior harness PG-4; probe §6). |
| PG concurrency at RR/SERIALIZABLE | **Chain fork** — F-01. |
| Transaction boundary ownership | `log_action()` does not own the transaction; both locks are held until the caller commits/rolls back. 206 call sites use `SessionLocal`/`ReadSessionLocal` with `autocommit=False` (`database.py:242,271`); no `autocommit=True` caller found. |
| Lock-order inversion (theoretical) | Advisory lock held for the full transaction; sampled services call `log_action()` *after* business writes (consistent order), but an exhaustive static proof over all 206 sites was not performed. No deadlock reproduced — F-05 (INFORMATIONAL). |
| Concurrency-test history | `sec015_conc_debug.log` shows a forked chain before the zero-row `UPDATE`; `sec015_green.log`/`sec015_green2.log` show 1 failed / 12 passed (contention before final stabilization); `sec015_conc_after_update.log` 2 passed; final `sec015_green_final.log` and fresh review-2 run 13/13. F-04 (INFORMATIONAL). |

---

## 8. Tamper-detection findings

Fresh related-audit run (`/tmp/opencode/sec015_review2_related.log`, **73 passed**) exercised all tamper tests against current source.

| Test / property | Result |
|---|---|
| Payload modification (`test_tampered_payload_is_detected`, endpoint tamper test) | Detected; `status == "tampered"`; forged id in `broken_entries`. |
| Predecessor hash modification | Detected. |
| Missing predecessor (deletion) | Detected at the exact surviving boundary: `broken_ids == [second_id]` (LOW assertion correctly fixed; no weakening). |
| Reordering/substitution | Covered by hash recomputation over ordered `id` values with the full record payload; any field change breaks the link. |
| NULL legacy row | Skipped, not falsely verified; modern row chains from genesis. |
| Persisted records, no repair | `_seed_chain_persisted` uses `db.expire_all()` and returns stored rows; `test_persisted_hash_verification_without_repair` passes. |
| Append-only trigger | PG probe rejected UPDATE and DELETE. |
| Anchor cross-check | `verify_audit_chain()` does **not** cross-check the HMAC anchor files; a fully re-stitched chain would evade it. Pre-existing property — F-06 (INFORMATIONAL). |
| Anchor pre-commit | `_write_anchor()` is called before caller commit — F-03 (LOW, pre-existing). |

**Conclusion:** tamper detection remains effective for all tested single-row mutations and deletions.

---

## 9. Regression and public-contract findings

| Contract element | Verification |
|---|---|
| `log_action()` signature / parameters | Byte-unchanged (lines 195-205); 206 call sites not edited. |
| Timestamp handling | `_canonical_audit_timestamp` unchanged and correct on both dialects (§4). |
| PG sequence behavior | `pg_get_serial_sequence('audit_logs','id')` preserved; gaps benign (§6). |
| Append-only enforcement | Trigger definitions unchanged; probe PASS. |
| Event contents/ordering | `_compute_chain_hash` field set unchanged (`id`, `user_id`, `user_role`, `action`, `resource_type`, `resource_id`, `details`, `ip_address`, `created_at`); `verify_audit_chain` orders by `id ASC`. |
| No new bypasses | No new direct `AuditLog(...)` construction in app code; other `*AuditLog` classes are separate models. No autocommit callers. |
| No weakened assertions | LOW fix strengthened the assertion to exact-boundary (`broken_ids == [second_id]`); all thresholds unchanged. |
| Related suites | 73/73 passed (chain 13, bypass 3, positional 11, anchor 14, compliance 21, MPI chain 11). |

---

## 10. Evidence inventory and reproducibility

### 10.1 Pre-existing artifacts inspected (not generated in this review)

| Artifact | Claimed result verified by direct inspection | Traceability limitation |
|---|---|---|
| `/tmp/opencode/sec015_red_baseline.log` | 7 failed / 6 passed, exit path 1; defect reproduced | No embedded HEAD; interpreter path from sibling `gula-platform/backend/.venv`; no exact command line in log |
| `/tmp/opencode/sec015_green_final.log` | 13 passed, 97.06 s | same |
| `/tmp/opencode/sec015_green_lowfix.log` | 13 passed, 78.83 s | same |
| `/tmp/opencode/sec015_related_audit.log` | 73 passed, 90.77 s | same |
| `/tmp/opencode/sec015_pg_verify.log` | `PG_VERIFY_RESULT=PASS`; PG-1..PG-4; serial sequence `public.audit_logs_id_seq` | same; harness `/tmp/opencode/sec015_pg_verify.py` is outside repo, contains no HEAD/source hash; did not test RR/SERIALIZABLE |
| `/tmp/opencode/sec015_full_suite.log` | 5151 passed / 28 skipped / 0 failed, `FULL_SUITE_EXIT=0`, 636.19 s, 203 warnings | same; **not rerun in this review (not authorized)** |
| `/tmp/opencode/auditfix_full_suite_clean.log` | historical 5138 / 28 / 0 | preserved, not overwritten |
| Supplementary: `sec015_conc_debug.log`, `sec015_green.log`, `sec015_green2.log`, `sec015_conc_after_update.log` | concurrency debug history (§7) | not listed in prior report; inspected here |

### 10.2 New evidence generated in this review (all disposable, source-tied)

| Artifact | Exact command / setup | Result / exit |
|---|---|---|
| `/tmp/opencode/sec015_review2_focused.log` | From `gula-integration/backend`: `ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 REDIS_URL="" DATABASE_URL="sqlite:///:memory:" AUDIT_ANCHOR_DIR=/tmp/opencode/sec015_review2_anchors AUDIT_ANCHOR_KEY=… SECRET_KEY=… ENCRYPTION_KEY=… NID_HMAC_KEY=… PYTHONPATH=.:.. /tmp/opencode/sec015_review2_venv/bin/python -m pytest tests/unit/test_audit_chain_integrity.py -q -p no:cacheprovider` | **13 passed**, 147.25 s, `FOCUSED_EXIT=0` |
| `/tmp/opencode/sec015_review2_related.log` | Same env, same interpreter; six-file related set listed in §9 | **73 passed**, 157.81 s, `RELATED_EXIT=0` |
| `/tmp/opencode/sec015_review2_sqlite_probe.log`, `..._mp.log` | `python3 sec015_review2_sqlite_probe.py` (stdlib Python 3.10, SQLite 3.37.2); see script for exact DDL/statements | all checks PASS; `SQLITE_PROBE_EXIT=0`, `MP_PROBE_EXIT=0` |
| `/tmp/opencode/sec015_review2_pg_probe.log` | `python3 sec015_review2_pg_probe.py` against disposable `sec015-review2-pg16` (PG 16.14, 127.0.0.1:55433, 4 threads) | RC/rollback/trigger PASS; RR/SERIALIZABLE FORKED; `PG_PROBE_EXIT=0` |
| `/tmp/opencode/sec015_review2_pg_isolation_nosnap.log` | `python3 sec015_review2_pg_isolation_nosnap.py`; advisory lock as first data statement (no artificial snapshot step) | RC INTACT; RR and SERIALIZABLE FORKED; `NOSNAP_EXIT=0` |

**Environment for new app tests:** Python 3.12.13 venv created with `uv venv --python 3.12 /tmp/opencode/sec015_review2_venv` and populated from `gula-integration/backend/requirements.txt` plus `pytest pytest-asyncio pytest-timeout pytest-xdist Faker factory_boy greenlet`. Key versions: pytest 9.2.0, pluggy 1.7.0, SQLAlchemy 2.1.9, greenlet 3.5.6, pydantic 2.14.4, fastapi 0.165.0, psycopg2 2.9.13. Concurrency: 4 threads × 3 writes (SQLite test and PG probes); separate engines/connections per writer. Cache and bytecode writes were disabled (`-p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1`).

**Reproducibility:** all probe scripts and logs remain in `/tmp/opencode`; the disposable PG container was removed (`docker rm -f sec015-review2-pg16`) and the remaining container list confirmed `gula-postgres` and `gula-redis` untouched. No PHI, production credentials, or secrets were used.

---

## 11. Findings (CRITICAL / HIGH / MEDIUM / LOW / INFORMATIONAL)

**CRITICAL:** none.
**HIGH:** none.

### F-01 — MEDIUM — PostgreSQL serialization is isolation-level dependent; fork reproduced under REPEATABLE READ / SERIALIZABLE with no application enforcement
- **Evidence:** §6 probes; `broken=[2]` in both non-default levels with the advisory lock as the first data statement; no isolation-level setting or check anywhere in `backend/app`.
- **Reproduction:** two writer threads/connections on disposable PG16; A holds `pg_advisory_xact_lock(GULAUDIT)` for 1.5 s uncommitted; B starts at +0.25 s with `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ` (or SERIALIZABLE); both insert; `verify` reports row 2 as broken. Exact commands: §10.2.
- **Impact:** an audit-chain fork; legitimate events are reported as tampered and the tamper-evident control becomes unreliable. Latent in the production configuration because no code path changes the level; becomes real on any future or external isolation change.
- **Affected code path:** `audit_service.py:225-244` — PG branch (`pg_advisory_xact_lock` → `nextval` → `_get_last_chain_hash` → INSERT) under a snapshot older than the predecessor commit.
- **Required correction:** (1) enforce READ COMMITTED on all audit-writing engines/sessions (e.g. `create_engine(..., isolation_level="READ COMMITTED")`) **or** fail fast in `log_action()` when `db.get_isolation_level()` is not READ COMMITTED; (2) add a disposable-PG16 regression test covering all three levels; (3) revise the remediation report to remove "non-blocking latent precondition" framing and state the enforced scope. **Or** an explicitly documented owner acceptance of a READ COMMITTED-only scope together with the enforcement guard. Until one of these is done, this condition is unresolved.

### F-02 — LOW — Prior raw evidence is not cryptographically tied to the reviewed source revision
- **Evidence:** no HEAD/hash in any prescribed log; warnings reference `../../gula-platform/backend/.venv/...`; `/tmp/opencode/sec015_pg_verify.py` has no source hash; report §4 lists commands but logs do not embed them.
- **Reproduction:** `grep -iEn "2206654|commit|HEAD|revis|git " sec015_*.log` → no revision markers.
- **Impact:** the historical claims (including 5151/28/0) cannot be independently re-bound to these exact MD5s; mis-attribution risk.
- **Affected code path:** evidence-capture process, not source.
- **Required correction / accepted limitation:** accept prior logs as historical context only (done here); require future evidence logs to embed `git rev-parse HEAD`, `md5sum` of changed files, exact command, engine version and concurrency. Fresh source-tied runs in §10.2 mitigate but do not retroactively fix the historical artifacts.

### F-03 — LOW — Anchor checkpoint is written before caller commit
- **Evidence:** `audit_service.py:264-266` calls `_write_anchor()` inside `log_action()` before the caller's `commit`; SQLite termination probe showed an uncommitted row is rolled back while a file write would already have occurred. Present in `2cdc5479` and `f0b021bd3` — pre-existing.
- **Reproduction:** call `log_action()` then `rollback()`; the anchor line remains in `_ANCHOR_DIR`.
- **Impact:** `get_latest_anchor()` may report an anchor for a never-persisted id; anchor/DB divergence.
- **Affected code path:** `log_action()` → `_write_anchor()`.
- **Required correction / accepted limitation:** explicitly accept as pre-existing and out of SEC-015 scope, or move anchor emission to a post-commit hook in a separately reviewed change. Not a blocker for this fix.

### F-04 — INFORMATIONAL — Concurrency test uses silent retries and has a prior failure history
- **Evidence:** test lines 286-306 retry up to 10 times without recording the count; `sec015_conc_debug.log` shows a forked chain; `sec015_green.log`/`sec015_green2.log` show 12 passed / 1 failed before final stabilization.
- **Impact:** a green run can include lock-error retries; the test does not prove "zero contention." Fork detection is still meaningful because it asserts an intact chain and distinct hashes.
- **Affected code path:** `test_audit_chain_integrity.py::TestAuditChainConcurrency`.
- **Required correction / accepted limitation:** accept retry as the intended contention handling, or record/assert retry telemetry. No source change required for SEC-015.

### F-05 — INFORMATIONAL — Full-transaction advisory lock introduces a theoretical lock-order inversion risk
- **Evidence:** advisory lock held until caller commit; 206 call sites; sampled sites log after business writes; no exhaustive static lock-order proof.
- **Impact:** a caller that logs before acquiring row locks could deadlock with one that does the reverse (PG detects and aborts one transaction). No deadlock reproduced.
- **Affected code path:** `log_action()` PG branch plus 206 callers.
- **Required correction / accepted limitation:** optional follow-up lock-order audit of call sites; accept as residual risk for this minimal fix.

### F-06 — INFORMATIONAL — Verification trusts stored hashes and does not cross-check anchors
- **Evidence:** `verify_audit_chain():279-294` feeds each row's stored `chain_hash` forward; anchors are written to files but never consulted by verification. Pre-existing.
- **Impact:** an attacker able to recompute all downstream hashes could evade `verify_audit_chain()`; anchor verification is a separate control.
- **Affected code path:** `verify_audit_chain()`.
- **Required correction / accepted limitation:** document as an explicit limitation of hash-chain-only verification; anchor cross-check belongs to a separate hardening task.

### F-07 — INFORMATIONAL — Full backend suite was not rerun in this review
- **Evidence:** directive does not authorize it; only prior `/tmp/opencode/sec015_full_suite.log` (5151/28/0) exists. Fresh runs covered 13 + 73 focused tests only.
- **Impact:** the full-suite number must be described as historical, not newly verified.
- **Affected code path:** none (process boundary).
- **Required correction / accepted limitation:** owner must not represent the 5151 result as re-verified by this review; a full rerun requires separate authorization.

---

## 12. Exact remediation requirements for each finding

| Finding | Owner action | Verification requirement | Blocks OD-001? |
|---|---|---|---|
| F-01 (MEDIUM) | Enforce READ COMMITTED on audit write connections **or** fail fast on unsupported levels; update report framing | Re-run disposable PG16 probe under RC/RR/SERIALIZABLE; expected RC INTACT and RR/SERIALIZABLE either rejected before insert or INTACT; add repo regression test | **Yes** — resolve or explicitly accept with enforcement |
| F-02 (LOW) | Adopt hash-stamped evidence-capture template | New logs contain HEAD + changed-file MD5s + exact command | No |
| F-03 (LOW) | Record explicit accepted limitation, or schedule post-commit anchor change | Acceptance note in remediation report, or regression test proving no orphan anchor after rollback | No |
| F-04 (INFO) | Document retry semantics or add retry telemetry | Test log records retry count | No |
| F-05 (INFO) | Optional call-site lock-order audit | Static report over 206 sites | No |
| F-06 (INFO) | Document verification limitation | Report/ADR statement | No |
| F-07 (INFO) | Represent full-suite result as historical only | Evidence ledger wording | No |

---

## 13. Residual assumptions and limitations

1. The reviewed production fix is an **uncommitted working-tree modification** on HEAD `2206654d…`; no commit authority was exercised.
2. READ COMMITTED is the only isolation level demonstrated safe; the application does not enforce it (F-01).
3. SQLite correctness is demonstrated for a single file and for cross-process writers; multi-file/attached-DB deployment is not covered (production is PostgreSQL).
4. Anchor files are written pre-commit and are not cross-checked by `verify_audit_chain()` (F-03, F-06).
5. The PG harness used a semantic reimplementation of the SQL (psycopg2), because the only Python 3.12 environment with the full app dependency set was the sibling worktree's venv, which this directive forbids using. The prior repo-sourced PG harness (`sec015_pg_verify.py`, app imports) is historical evidence only; its security/concurrency claims are corroborated by the semantic probe at READ COMMITTED.
6. The 5151-test full-suite result was not rerun (F-07).
7. No operational, clinical, legal, regulatory or release claim is made. `shared/audit/service.py` schema mismatch remains separately `BLOCKED`.
8. Fresh app-test runs used SQLAlchemy 2.1.9 (prior logs predate this); both runs passed, and no version-dependent behavior difference was observed.

---

## 14. Final verdict

**PASS WITH CONDITIONS — OD-001 remains `BLOCKED`.**

Basis: no CRITICAL/HIGH finding; SQLite transaction-level serialization demonstrated; PostgreSQL locking correctness demonstrated for the application's supported isolation level (READ COMMITTED); tamper detection effective; public contract preserved; evidence freshly reproduced against the exact reviewed working tree. The unresolved MEDIUM condition F-01 requires an owner action (enforce or explicitly accept a READ COMMITTED-only scope with a guard) and a defined verification before OD-001 can be accepted.

This review intentionally does **not** self-award `INDEPENDENTLY VERIFIED`, does not authorize SEC-015 source changes, commits, pushes, merges, PRs, deployment, production DB operations, Stable v1.0.0, or `PRODUCTION READY`.

**Final invariant check:** branch `integration/gula-unification-v1` and HEAD `2206654d…` unchanged; 20 staged `R100` renames intact; staged MD5 `56c524d6…` unchanged; all three protected MD5s exact; sibling HEAD `f478676b…` unchanged; `git diff --check` exit 0; no source/test/migration/config/report file modified; no commits, pushes, merges, PRs or deployments; no repo cache/bytecode artifacts introduced; only this report was created in the repository.

**Return to owner:** report `GULA_SEC015_ADVERSARIAL_REVIEW_2_REPORT.md` + evidence summary. OD-001 decision awaits the owner.
