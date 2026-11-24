# P-02 / AUD-F02 — decision packet REVISION 2 (HEAD-evidence baseline)

**Generated:** 2026-11-21 UTC
**Supersedes for decision purposes:** `AUDIT_EXECUTION_RECORDS/P-02_DECISION_PACKET.md` (original retained unchanged).
**Evidence baseline:** committed HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`, branch `integration/gula-unification-v1`.
All line ranges below refer to `git show HEAD:<path>` at that SHA. Working-tree behavior is **not** used as evidence.
**Status:** `PREPARED ONLY` · NOT `IMPLEMENTED` · NOT `TESTED` · NOT `INDEPENDENTLY REVIEWED` · NOT `ACCEPTED` · NOT `PRODUCTION READY`.
**Gate:** R4 — explicit, package-specific owner authorization required before any implementation.
**Posture:** HOLD · `production_ready_items = 0` · no commit / push / PR / merge / deploy.

---

## 1. Confirmed defect at HEAD

| Field | Evidence at HEAD |
|---|---|
| Finding | `AUD-F02` — critical-result alert audit bypass on an active clinical path. |
| Function | `backend/app/routes/ai.py:641-667` — `_emit_critical_alert(db, order_id, critical_tests, token_prefix)`. |
| Direct bypass | `:646-662` constructs `AuditLog(...)` directly and `:663` calls `db.commit()`. No call to canonical `log_action` exists; `AuditLog` is imported at `:50`, `log_action` is not imported. |
| Hash-chain omission | `backend/app/models/audit_log.py:25-27` — `chain_hash` is nullable, intended for legacy rows. The helper never sets it, so the INSERT produces `chain_hash = NULL`. Canonical verification `backend/app/services/audit_service.py:248-250` explicitly skips NULL-chain rows; the alert is therefore outside tamper-evident verification. |
| Canonical schema omission | `backend/app/models/audit_log.py:16-18` — new events are expected to carry `lab_id`; the helper sets `user_id=None`, `user_role="system:ai"`, action, resource fields and details only. |
| Error suppression | `backend/app/routes/ai.py:664-667` — blanket `except Exception`, `logger.error(...)`, `contextlib.suppress(Exception): db.rollback()`. No re-raise, no failure signal. |
| Active call path | `:934-943` — when `critical_flags` exist, a fresh `SessionLocal()` is opened in `run_in_executor`, the helper is called at `:939`, the session is closed in `finally:`, and the endpoint awaits the executor. The AI call follows at `:945-947`. |
| Operational consequence | Audit-write failure is logged and swallowed; the endpoint proceeds to return an interpretation. A critical clinical alert can be absent from the tamper-evident trail while the API reports success. |
| Reference | `GULA_AUDIT_SECURITY_FINDINGS.md` AUD-F02; original review observation R3-02 (graded LOW in the earlier independent review report, but the underlying bypass is the MEDIUM finding here). |

**Confirmed vs hypothesis.** The direct write, NULL chain, suppression and call path are **confirmed by HEAD source**.
Whether the failure occurs in production, how often it occurs, and whether any downstream consumer relies on the
swallowed behavior are **hypotheses** — no production telemetry, PHI or service access was used.

## 2. HEAD transaction and persistence behavior

1. `_load_results_from_db` (`:880-912`) opens its own session, reads `LabResult` / `LabOrder` / `Patient`, and closes it in `finally`. It does not overlap the audit transaction.
2. `_write_critical_alert` (`:936-941`) opens a second session (`SessionLocal()`), calls the helper, closes it. The helper itself calls `db.commit()` at `:663`; on failure it rolls back inside a suppressed exception.
3. The canonical writer `log_action` (`backend/app/services/audit_service.py:184-235`) serializes dict details (`:198-202`), builds `AuditLog` (`:203-213`), and on PostgreSQL reserves the serial ID with `nextval(pg_get_serial_sequence('audit_logs','id'))` (`:218-220`), reads the predecessor hash (`:222`), computes the chain hash (`:223`), adds/flushes (`:224-225`), and writes an anchor at the anchor interval (`:233-234`). On non-PostgreSQL dialects it uses the fallback branch `:226-231`.
4. **No isolation-level guard exists at HEAD.** `:215` only checks `bind.dialect.name == "postgresql"`; there is no `AuditChainIsolationError`, no `READ COMMITTED` enforcement and no transaction-isolation refusal. Any claim about guard-refusal behavior on this packet's baseline is **unverified** and belongs to a future, separately authorized hardening change.
5. The PostgreSQL append-only trigger (`backend/migrations/versions/20250322_0002_perf_indexes_audit_protection.py:73-101`) blocks UPDATE/DELETE, not INSERT; it does not protect a NULL-chain row from being written.

## 3. Existing tests at HEAD and their limitations

| Test at HEAD | Limitation for AUD-F02 |
|---|---|
| `backend/tests/unit/test_audit_anchor.py` (15 tests, e.g. `:61-342`) | Tests the anchor file subsystem only; never calls `_emit_critical_alert` or the AI endpoint. |
| `backend/tests/test_compliance_integrity.py`, `backend/tests/test_disaster_recovery.py` | Call `verify_audit_chain` as a utility; do not exercise this helper or assert critical-alert chaining. |
| `backend/tests/test_ai_integration.py`, `test_ai_platform.py`, `test_ai_guardrails.py`, `test_ai_evaluation.py`, `test_ai_benchmark.py`, `test_ai_fabric_access.py` | Exercise AI behavior; a HEAD-wide scan found **zero** occurrences of `critical_result_alert` or `log_action` in these files. No audit-chain assertion exists. |
| `backend/tests/unit/test_audit_bypass_regression.py` | **ABSENT at HEAD** (present only in the untracked working tree). Must not be cited as HEAD evidence. |
| `backend/tests/conftest.py:28,93-150` | Session engine is `sqlite:///:memory:`/file SQLite with synthetic DDL. SQLite does not exercise the PostgreSQL `nextval`/`pg_get_serial_sequence` branch of `log_action` (`audit_service.py:218-220`). |

**No RED/GREEN evidence was reproduced for this revision.** Nothing was executed against PostgreSQL in this documentation-only step.

## 4. Minimum proposed change (NOT applied)

**Option A — fail closed (recommended for decision, not implemented):**
1. In `backend/app/routes/ai.py:641-667` only, replace direct `AuditLog` construction with a single canonical call to `log_action` carrying the same action/resource/role/details, plus `lab_id` resolved from the order when available.
2. Remove the blanket suppression: on audit failure perform a narrow `db.rollback()` (with a guarded rollback that cannot mask the original error) and **re-raise**. The caller at `:934-943` then fails the `/ai/interpret` request before the AI call at `:945-947`.
3. Keep the success-path response contract unchanged; no schema change, migration, new dependency, change to the hash algorithm, or change to any other audit/identity/privacy behavior.
4. Preserve the mixed-provenance file's other hunks byte-for-byte; no staging or commit.

**Option B — durable outbox (NOT in scope of this packet):** buffer the alert in a durable outbox with retry, dedupe and monitoring. It requires a new table/migration, worker ownership, retention and reconciliation policy, and its own design package and owner decision. Selecting (b) means this packet is not authorized.

**Alternatives explicitly rejected:** (i) keep the current suppression (fails the finding); (ii) log-only compensation without persistence (not tamper-evident); (iii) retry inside the request without a dedupe key (duplicate-event risk).

## 5. Failure, transaction and availability analysis

| Concern | Analysis |
|---|---|
| Transaction boundary | Audit uses its own session and commits before the AI call. Fail-closed re-raise leaves no partial DB write after rollback; the read session is already closed. |
| Availability | On canonical writer failure the entire interpretation request fails before the AI call. This is a clinical-path availability trade-off that the owner must explicitly accept. |
| Retry / duplicate-event | Caller does not retry. If a future retry is added, no idempotency key exists; repeated critical alerts could be duplicated. Any retry requires a separate dedupe design. |
| Concurrency | Two concurrent interpreters of the same order can produce two alerts; canonical chain serialization on PostgreSQL uses `nextval` and predecessor read (`:218-223`) but does not deduplicate business events. |
| Rollback | Rollback must attempt once and re-raise the original exception even if rollback itself fails. |
| Unknown isolation guard | No guard at HEAD; therefore no guard-refusal behavior can be tested on this baseline. If a guard is introduced later, PostgreSQL tests are mandatory. |

## 6. PostgreSQL-compatible RED/GREEN test plan — **UNVERIFIED**

**Environment status:** `backend/tests/conftest.py` at HEAD is SQLite-only. A `gula-postgres` Docker container exists on the host, but it is **not established as a disposable, isolated test environment** for this workstream and was **not** used. No `DATABASE_URL` was set. Therefore the entire PostgreSQL test plan is marked **UNVERIFIED**; no SQLite substitute is offered for PostgreSQL-only behavior.

Prerequisites for a future authorized execution: disposable PostgreSQL 16 instance, synthetic schema only, no PHI, no production DB/Redis, `ENV=test`, dedicated test `DATABASE_URL` pointing to the disposable instance, and a fixture that provides a real PostgreSQL `Session` plus monkeypatching of `app.database.SessionLocal`.

| # | Test | RED condition at HEAD | GREEN condition after change | Assertion |
|---|---|---|---|---|
| R1 | Direct-write bypass | HEAD helper writes an `audit_logs` row with `chain_hash IS NULL`; `verify_audit_chain(db)` skips it | Canonical writer produces non-NULL `chain_hash` and `verified is True` | Query by `action="critical_result_alert"`; assert exactly one row, non-NULL hash, chain verified |
| R2 | Failure propagation | HEAD swallows a forced DB error and the endpoint proceeds | Forced error propagates; no audit row remains | Monkeypatch canonical writer to raise; assert raised exception and zero rows |
| R3 | Rollback safety | HEAD suppresses rollback failures | Rollback attempted once; original exception preserved | Monkeypatch `db.rollback` to raise; assert original error type |
| R4 | Canonical schema | `lab_id` absent at HEAD | `lab_id` from order present when available | Assert row fields match canonical contract |
| R5 | Caller-level signal | No failure at HEAD | `/ai/interpret` returns a non-2xx error when audit fails, before AI provider call | Assert AI provider mock not called |
| R6 | Concurrency/retry | N/A | Two concurrent interpretations produce two distinct chained rows, no hash corruption | `ThreadPoolExecutor`, assert 2 rows, chain verified |

Reproducible command pattern once the disposable PostgreSQL fixture exists (NOT executed here):

```bash
cd /home/samertts/workspace/projects/gula-integration/backend
ENV=test \
DATABASE_URL="postgresql://<synthetic-user>@<disposable-host>:5432/<synthetic-db>" \
PYTHONPATH=..:/home/samertts/workspace/projects/gula-integration \
/tmp/opencode/gula-int-py312/bin/python -m pytest \
  tests/test_p02_critical_alert_audit_postgres.py -q
```

The command is a **plan**, not evidence; no such test file exists at HEAD and no run was performed.

## 7. Acceptance / rejection / rollback

**Engineering acceptance (all required):**
- RED→GREEN reproduced on disposable PostgreSQL with the assertions above; synthetic data only.
- Canonical chain verified after the alert write; no NULL-chain alert rows.
- Caller-level failure signal asserted; AI provider not called on audit failure.
- Focused suite plus related suites (audit chain, anchor, compliance integrity, AI integration/guardrails/platform) pass; ruff clean; `git diff --check` exit 0.
- Fresh-context independent review with **0 CRITICAL and 0 HIGH** findings; all conditions cleared by regression tests.
- Report recorded in `P-02_AFTER_REV2.md` before any `INDEPENDENTLY REVIEWED` claim.

**Engineering rejection (any one):**
- Any CRITICAL/HIGH review finding; unverified or substituted SQLite evidence; any NULL-chain audit row; any silent success on audit failure; any schema/migration/dependency change outside the packet; any unrelated file modified; any PHI/production access.

**Owner conditions:** package-specific R4 authorization; explicit selection of (a) or (b); explicit acceptance of the `/ai/interpret` availability trade-off; separate decision for staging/commit scope.

**Rollback:** revert only the `_emit_critical_alert` hunk; no migration or protected-file change. `ACCEPTED` and `PRODUCTION READY` are never implied by this packet or by a PASS review.

## 8. Exact owner decision required

> "I authorize package P-02 / AUD-F02 REVISION 2, baselined at HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`, **exactly as scoped in `AUDIT_EXECUTION_RECORDS/P-02_DECISION_PACKET_REV2.md`**, and I select option **(a) fail closed**. I accept that an audit-write failure during `critical_result_alert` will fail `/ai/interpret` before the interpretation is returned, on this path only. If I select option (b), this packet is not authorized and a separate durable-outbox design package is required. This decision does not authorize a commit, staging change, push, Draft PR, merge, release, deployment, `PRODUCTION READY`, or any change to HOLD or `production_ready_items = 0`. I separately decide staging/commit scope."

Alternative: **"P-02 is deferred; keep AUD-F02 open and this packet prepared."**
