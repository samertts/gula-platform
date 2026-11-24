# P-03 / AUD-F03 — decision packet REVISION 2 (HEAD-evidence baseline)

**Generated:** 2026-11-21 UTC
**Supersedes for decision purposes:** `AUDIT_EXECUTION_RECORDS/P-03_DECISION_PACKET.md` (original retained unchanged).
**Evidence baseline:** committed HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`, branch `integration/gula-unification-v1`.
All line ranges below refer to `git show HEAD:<path>` at that SHA. Working-tree behavior is **not** used as evidence.
**Status:** `PREPARED ONLY` · NOT `IMPLEMENTED` · NOT `TESTED` · NOT `INDEPENDENTLY REVIEWED` · NOT `ACCEPTED` · NOT `PRODUCTION READY`.
**Gate:** R4 — explicit, package-specific owner authorization required before any implementation.
**Posture:** HOLD · `production_ready_items = 0` · no commit / push / PR / merge / deploy.
**Independence:** approval of P-02 does **not** authorize P-03; no shared implementation is assumed.

---

## 1. Confirmed defects at HEAD

| Boundary | Evidence at HEAD |
|---|---|
| **B1 — Approval** | There is **no standalone approval route**. The only approval call is `backend/app/control_plane/routes.py:295-298`, executed when the deploy request carries `approve_first`; it calls `sdk.releases.approve(release_id, user_str)` with `user_str` taken from the **request body** (`:294`). `ReleaseManager.approve` (`release/manager.py:69-76`) mutates in-memory `status`/`approved_by` and writes `logger.info` only. No canonical `log_action` exists anywhere under `backend/app/control_plane` (HEAD-wide `git grep` returned no matches). |
| **B2 — Execution / deployment** | `backend/app/control_plane/routes.py:291-306` calls `sdk.releases.deploy(release_id, user_str)`; `ReleaseManager.deploy` (`release/manager.py:78-99`) mutates in-memory `status`→`DEPLOYING`→`DEPLOYED`/`FAILED`, sets `deployed_by`, awaits `asyncio.sleep(0.3)`, and logs. Exceptions at `:95-97` are swallowed into `FAILED`; no audit record is produced. HEAD has no rollback route (only the manager method at `:101-109`). |
| **B3 — Secret access** | `backend/app/control_plane/config/secrets.py:29-33` (`get`, `get_required`) and `:44-57` (`rotate`) access/rotate secrets with only `logger.info` at `:56`. `access_audit_log()` at `:59-67` is a **pure dict builder with zero callers** (HEAD-wide `git grep`); it neither writes nor receives a DB session. `sdk.secrets` is instantiated (`sdk.py:39`) but no route calls it. |
| **B4 — Audit read** | `backend/app/control_plane/routes.py:309-327`. `sdk.audit` is `None` at construction (`sdk.py:50`) and `set_audit()` (`:60-61`) has **no callers**. When `None`, the route returns `{"entries": [], "count": 0, "note": "Audit service not initialized"}` (`:318-319`). When set, `EnterpriseAudit.query()` (`control_plane/audit.py:50-69`) calls the stale shared writer. |
| **Schema mismatch (confirmed)** | `shared/audit/service.py:26-62` INSERTs into `audit_logs` columns `entity_type`, `entity_id`, `previous_hash`, `timestamp`. The canonical HEAD model `backend/app/models/audit_log.py:13-27` defines `user_id`, `user_role`, `lab_id`, `action`, `resource_type`, `resource_id`, `details`, `ip_address`, `created_at`, `chain_hash` — **none** of `entity_type`, `entity_id`, `previous_hash`, `timestamp`. The `EnterpriseAudit` path (`control_plane/audit.py:26-48`) therefore cannot produce a canonical chained row. |
| **Actor provenance** | `_user` (`control_plane/routes.py:26-27`) delegates to `get_current_user` (`backend/app/security/dependencies.py:36-76`), returning `LabUser | User` with authoritative `.id`, `.role`, `.lab_id` (`:65-71`; model fields `backend/app/models/user.py:14-20`, `lab_user.py:14-19`). HEAD deploy ignores this principal and uses the body field `user`. |
| **Persistence dependency** | `backend/app/control_plane/routes.py` has **no** `get_db` / `Session` dependency; `log_action` requires `db: Session` (`backend/app/services/audit_service.py:184-194`). No DB session source exists for control-plane writes at HEAD. |

**Confirmed vs hypothesis.** All items above are **confirmed by HEAD source inspection**.
Whether an uncommitted deployment ever configured `set_audit`, whether the stale-column writer currently fails at
runtime, and whether any real control-plane decision was unaudited are **hypotheses**: no production access,
deployment configuration, PHI or secret value was inspected.

## 2. Transaction boundaries and failure behavior

- HEAD release state is a process-local dict (`ReleaseManager._releases`, `:44-46`). It is not durable across restarts and has no DB transaction.
- HEAD deploy swallows its own execution exception (`:95-97`) and still returns a `Release` object; the route returns success (`:302-306`).
- The canonical writer `log_action` (`audit_service.py:184-235`) builds the row, computes the chain hash on PostgreSQL using `nextval(pg_get_serial_sequence('audit_logs','id'))` (`:218-223`), flushes, and writes anchors (`:233-234`). There is **no isolation guard at HEAD** (`:215` checks dialect only).
- Any new audit write must be committed **before** the corresponding in-memory state transition, or the transition is governed by a fail-closed error path. Cross-resource atomicity between the DB row and the in-memory dict is impossible; this residual must be disclosed, not hidden.
- Exactly-once semantics cannot be guaranteed: canonical `log_action` has no correlation/dedupe parameter or unique constraint, and HEAD has no idempotency key. Acceptance must therefore be **at most one canonical row per operation under test**, with duplicate-event risk under retry disclosed; a stronger guarantee requires a separate schema/design package.

## 3. Existing tests at HEAD and their limitations

- HEAD-wide scan found **no** test file referencing `/control-plane`, `ReleaseManager` or `EnterpriseAudit`.
- No `log_action` call or canonical-chain assertion exists in control-plane tests (none exist).
- `backend/tests/conftest.py:28,93-150` uses SQLite only; it does not exercise the PostgreSQL-specific `nextval` branch of `log_action` (`audit_service.py:218-220`).
- `backend/tests/unit/test_audit_anchor.py` tests anchor files, not control-plane boundaries.
- The untracked working-tree file `backend/tests/unit/test_audit_bypass_regression.py` is **not** HEAD evidence.
- **No RED/GREEN evidence was reproduced in this documentation-only revision.**

## 4. Minimum proposed change (NOT applied)

For each owner-selected boundary only:
1. Supply a DB `Session` to the affected route via `Depends(get_db)`; pass it to canonical `log_action` with an action from the existing taxonomy (`control_plane/audit.py:12-23`: `control.release`, `control.decision`, `control.deployment`, `control.secret_access`), actor fields from the authenticated principal, `resource_type`/`resource_id` identifying the release or secret reference, version/outcome and a correlation value in `details` (advisory only, not a dedupe guarantee).
2. Commit/flush the canonical audit row before the in-memory release-state mutation. On audit failure, roll back, do not mutate state, and fail the request closed.
3. Keep the existing in-memory `approved_by` / `deployed_by` fields for API responses; they are not the audit source of truth.
4. If B3 is selected, add auditing at the real accessors (`get`, `get_required`, `rotate`) with a DB session supplied by the caller; log the key **reference only**, never a value. Do not wire only `access_audit_log()`.
5. If B4 is selected, re-point `/audit-log` reads to canonical `audit_logs` rows via `log_action`'s companion query surface, replacing the stale shared writer path; no secret value in responses.
6. No schema change, migration, new dependency, hash-algorithm change, protected-file change or unrelated control-plane behavior change. No staging or commit.

**Explicitly out of scope:** two-person rule, role/permission changes, service-actor identity plumbing, durable outbox, dedupe schema, deploy/rollback route additions, and any change to actual deployment behavior. Each requires its own decision package.

## 5. Actor policy evaluation

| Actor class | HEAD state | Proposed treatment |
|---|---|---|
| Authenticated human principal | `_user` → `get_current_user` returns `LabUser | User` with authoritative `.id` / `.role` / `.lab_id` | **Recommended:** sole actor source; `user_id=user.id`, role from `user.role`, lab from `user.lab_id`. Test asserts body-supplied actor is ignored. |
| Service / system actor | No service principal concept on HEAD control-plane routes; only string `approved_by`/`deployed_by` from body | **Separate owner decision:** if required, define an authenticated service identity and its mapping to `user_role`; never infer it from a request body. Default: not authorized. |
| Missing principal | HEAD dependency returns 401 before route execution; service-layer calls may still pass `None` | Fail closed: 401/403, no state mutation, no audit row. |
| Invalid actor (unknown/inactive/unverified) | `get_current_user` rejects at `dependencies.py:65-76` | Fail closed; regression test asserts no audit row and no state mutation. |

## 6. PostgreSQL-compatible test plan — **UNVERIFIED**

**Environment status:** HEAD test fixtures are SQLite-only. A `gula-postgres` container exists but is not established as a disposable isolated test environment and was **not** used. No `DATABASE_URL` was set. All tests below are **UNVERIFIED**; no SQLite substitute is offered.

Prerequisites for future authorized execution: disposable PostgreSQL 16, synthetic schema/seed only, no PHI/production services, `ENV=test`, a real PostgreSQL `Session` fixture, and monkeypatching of control-plane SDK singletons.

| # | Boundary | Test assertion | Result at HEAD (predicted from source, not executed) |
|---|---|---|---|
| T1 | B1 approval | Drive deploy with `approve_first`; assert exactly one canonical chained row, taxonomy action, principal actor, release id/version, `verify_audit_chain(db)["verified"] is True` | FAIL — no audit row |
| T2 | B2 deployment | Drive deploy alone; assert one canonical chained row and no exception swallowing | FAIL — no audit row; HEAD swallows execution error |
| T3 | B3 secret get/required/rotate | Assert key-name-only audit row, no secret value in `details`, chain verified | FAIL — no writer, no DB session, `access_audit_log()` unused |
| T4 | B4 audit read | GET `/control-plane/audit-log` returns the canonical rows with filters | FAIL — `sdk.audit is None` → empty response |
| T5 | Missing principal | No principal → 401/403, zero rows, no state mutation | HEAD dependency already rejects; service-layer variant unverified |
| T6 | Invalid actor / body spoofing | Body actor different from principal → audit actor equals principal; spoofed value absent | FAIL — HEAD uses body value |
| T7 | Audit failure | Forced canonical writer failure → rollback, no state mutation, non-2xx response | FAIL — HEAD has no audit write |
| T8 | Retry / duplicate event | Repeat the same operation → at most one row per operation under test; duplicate risk recorded | FAIL — no dedupe at HEAD; stronger guarantee needs separate design |
| T9 | Concurrency | Two concurrent approvals on distinct releases → two valid chained rows, no hash corruption | FAIL — no canonical write |
| T10 | Rollback | Audit failure after status change attempt → in-memory status unchanged | FAIL — HEAD mutates before any audit consideration |

Reproducible command pattern once the disposable PostgreSQL fixture exists (NOT executed here):

```bash
cd /home/samertts/workspace/projects/gula-integration/backend
ENV=test \
DATABASE_URL="postgresql://<synthetic-user>@<disposable-host>:5432/<synthetic-db>" \
PYTHONPATH=..:/home/samertts/workspace/projects/gula-integration \
/tmp/opencode/gula-int-py312/bin/python -m pytest \
  tests/test_p03_control_plane_audit_postgres.py -q
```

The command is a **plan**, not evidence; no such test file exists at HEAD and no run was performed.

## 7. Acceptance / rejection / rollback

**Engineering acceptance (all required):**
- Every owner-selected boundary has a PostgreSQL RED→GREEN test with assertions T1–T10 as applicable; synthetic data only.
- Canonical chain verified; no secret value appears in any audit row or response.
- Principal-only actor assertion passes; missing/invalid actor cases fail closed.
- Audit failure leaves release state unchanged; at-most-once assertion passes with duplicate risk disclosed.
- Focused and related suites pass; ruff clean; `git diff --check` exit 0; fresh-context independent review with **0 CRITICAL and 0 HIGH** and all conditions cleared; report in `P-03_AFTER_REV2.md`.

**Engineering rejection (any one):**
- Any CRITICAL/HIGH finding; SQLite substituted for PostgreSQL guard/chain evidence; secret value in audit; body actor accepted; stale shared writer still used for selected boundaries; state mutation on audit failure; schema/migration/new dependency/protected-file change; unrelated file modified; any production access.

**Rollback:** revert only the selected control-plane hunks; no migration or protected-file change; all 20 staged `R100` renames and staged MD5 `56c524d6ffe9872c3a3ac6eff8c8f203` untouched.

## 8. Independent owner decisions required

Each line is a **separate** decision; no decision authorizes another package.

- **D1 — Boundaries:** (a) B1+B2 only; (b) B1+B2+B3; (c) B1+B2+B3+B4; (d) defer. A separate store design is **not** available in this packet.
- **D2 — Actor policy:** (a) authenticated human principal only (recommended); (b) principal plus an explicitly defined authenticated service identity (requires its own design); (c) defer. Request-body actors are rejected in every option.
- **D3 — Failure policy:** (a) fail closed (recommended); (b) durable outbox design package (not authorized here).
- **D4 — Idempotency:** (a) accept at-most-once under test with duplicate-risk disclosure (recommended for this packet); (b) separate dedupe/schema design package.
- **D5 — Audit-read route:** (a) re-point `/control-plane/audit-log` to canonical rows when B4 is selected; (b) leave it unchanged and accept the inert-route risk.
- **D6 — Staging/commit scope:** decided separately from this packet; no commit authority is implied.

Exact combined decision text once the owner has chosen:

> "I authorize package P-03 / AUD-F03 REVISION 2, baselined at HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`, exactly as scoped in `AUDIT_EXECUTION_RECORDS/P-03_DECISION_PACKET_REV2.md`, with D1=__, D2=__, D3=__, D4=__, D5=__. Request-body actors and secret values are never written to audit details. This decision does not authorize a commit, staging change, push, Draft PR, merge, release, deployment, `PRODUCTION READY`, or any change to HOLD or `production_ready_items = 0`. D6 is decided separately."

Alternative: **"P-03 is deferred; keep AUD-F03 open and this packet prepared."**
