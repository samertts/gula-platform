# P-03 / AUD-F03 — decision packet REVISION 3 (HEAD-evidence baseline)

**Generated:** 2026-11-21 UTC
**Supersedes for decision purposes:** `AUDIT_EXECUTION_RECORDS/P-03_DECISION_PACKET.md` and
`AUDIT_EXECUTION_RECORDS/P-03_DECISION_PACKET_REV2.md` (both retained unchanged as evidence).
**REV3 purpose:** resolves every finding in `AUDIT_EXECUTION_RECORDS/PACKET_REVIEW_2026_11_21.md`
(P-03 section). No source change; no implementation.
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
| **B2 — Execution / deployment** | `backend/app/control_plane/routes.py:291-306` calls `sdk.releases.deploy(release_id, user_str)`; `ReleaseManager.deploy` (`release/manager.py:78-99`) mutates in-memory `status`→`DEPLOYING`→`DEPLOYED`/`FAILED`, sets `deployed_by`, awaits `asyncio.sleep(0.3)`, and logs. Exceptions at `:95-97` are swallowed into `FAILED`; no audit record is produced. HEAD has no rollback route (only the manager method at `:101-109`). **Second deployment surface (disclosed):** `POST /control-plane/fleet/deploy` (`control_plane/routes.py:211-226`) → `ProvisioningEngine.deploy` (`control_plane/fleet/provisioning.py:36-64`) mutates in-memory deployment/fleet state and swallows exceptions at `:60-62`. It is **OUT of B2** unless the owner explicitly selects it as D1 option (e); an owner choosing D1=(a) must not assume all deployment surfaces are covered. |
| **B3 — Secret access** | `backend/app/control_plane/config/secrets.py:29-33` (`get`, `get_required`) and `:44-57` (`rotate`) access/rotate secrets with only `logger.info` at `:56`. `access_audit_log()` at `:59-67` is a **pure dict builder with zero callers** (HEAD-wide `git grep`); it neither writes nor receives a DB session. `sdk.secrets` is instantiated (`sdk.py:39`) but no route calls it. |
| **B4 — Audit read** | `backend/app/control_plane/routes.py:309-327`. `sdk.audit` is `None` at construction (`sdk.py:50`) and `set_audit()` (`:60-61`) has **no callers**. When `None`, the route returns `{"entries": [], "count": 0, "note": "Audit service not initialized"}` (`:318-319`). When set, `EnterpriseAudit.query()` (`control_plane/audit.py:50-69`) calls the **stale shared query helper** `query_audit_log` (`shared/audit/service.py:65+`); its `log()` path (`:31-48`) calls the stale shared **writer** `create_audit_entry` (`:26-62`). Neither is the canonical `log_action` surface. |
| **Schema mismatch (confirmed)** | `shared/audit/service.py:26-62` INSERTs into `audit_logs` columns `entity_type`, `entity_id`, `previous_hash`, `timestamp`. The canonical HEAD model `backend/app/models/audit_log.py:13-27` defines `user_id`, `user_role`, `lab_id`, `action`, `resource_type`, `resource_id`, `details`, `ip_address`, `created_at`, `chain_hash` — **none** of `entity_type`, `entity_id`, `previous_hash`, `timestamp`. The `EnterpriseAudit` path (`control_plane/audit.py:26-48`) therefore cannot produce a canonical chained row. |
| **Actor provenance** | `_user` (`control_plane/routes.py:26-27`) delegates to `get_current_user` (`backend/app/security/dependencies.py:36-76`), returning `LabUser | User` with authoritative `.id`, `.role`, `.lab_id` (`:65-71`; model fields `backend/app/models/user.py:14-20`, `lab_user.py:14-19`). HEAD deploy ignores this principal and uses the body field `user`. |
| **Persistence dependency** | `backend/app/control_plane/routes.py` handler signatures have **no** `get_db` / `Session` parameter; `log_action` requires `db: Session` (`backend/app/services/audit_service.py:184-194`). `get_db` is nevertheless already present in the dependency graph through `get_current_user` (`backend/app/security/dependencies.py:39`, reached via `control_plane/routes.py:17,26-27`). Adding `Depends(get_db)` to selected routes is therefore **wiring an existing dependency**, not introducing a new session infrastructure component. |

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
- **Concurrent chain integrity is NOT guaranteed at HEAD and is NOT fixed by this packet.** `_get_last_chain_hash` (`audit_service.py:106-112`) reads the chain head with an unlocked `SELECT chain_hash FROM audit_logs ORDER BY id DESC LIMIT 1`; `log_action` reserves `nextval` and computes `chain_hash` from that read at `:218-225` before `db.add()/db.flush()`. Two concurrent workers can read the same predecessor, producing rows that `verify_audit_chain` (`:238-268`) rejects; the append-only triggers (`20250322_0002_perf_indexes_audit_protection.py:76-104`) block in-place repair. Adding serialization would change shared canonical code beyond this control-plane packet. **Resolution:** T9 is moved to a separate design package (`P-03-CONCURRENCY`) and is explicitly **not** an acceptance condition here; no single-process GREEN result may be presented as multi-worker chain-integrity evidence.

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
5. If B4 is selected, define a **new canonical read helper** in `backend/app/services/audit_service.py` (e.g. `query_audit_logs(db, ...) -> list[dict]`) that selects canonical `AuditLog` columns (`backend/app/models/audit_log.py:13-27`) and maps them to the `/control-plane/audit-log` response shape, then re-point the route to it. **No such canonical query helper exists at HEAD**; creating it is part of the authorized D5 scope. The stale shared query helper (`shared/audit/service.py:65+`, reached through `control_plane/audit.py:50-69`) is not used for selected boundaries. No secret value in responses; no schema change.
6. No schema change, migration, new dependency, hash-algorithm change, protected-file change or unrelated control-plane behavior change. No staging or commit.

**Explicitly out of scope:** two-person rule, role/permission changes, service-actor identity plumbing, durable outbox, dedupe schema, deploy/rollback route additions, any change to actual deployment behavior, and **concurrent chain serialization / T9** (moved to the separate `P-03-CONCURRENCY` design package). Each requires its own decision package.

## 5. Actor policy evaluation

| Actor class | HEAD state | Proposed treatment |
|---|---|---|
| Authenticated human principal | `_user` → `get_current_user` returns `LabUser | User` with authoritative `.id` / `.role` / `.lab_id` | **Recommended:** sole actor source; `user_id=user.id`, role from `user.role`, lab from `user.lab_id`. Test asserts body-supplied actor is ignored. |
| Service / system actor | No service principal concept on HEAD control-plane routes; only string `approved_by`/`deployed_by` from body | **Separate owner decision:** if required, define an authenticated service identity and its mapping to `user_role`; never infer it from a request body. Default: not authorized. |
| Missing principal | HEAD dependency returns 401 before route execution; service-layer calls may still pass `None` | Fail closed: 401/403, no state mutation, no audit row. |
| Invalid actor (unknown/inactive/unverified) | `get_current_user` rejects at `dependencies.py:65-76`; additional rejection paths: permission-version mismatch `:87-95` (401) and deactivated lab `:97-104` (403) | Fail closed for each path; regression test asserts no audit row and no state mutation. |
| Body-supplied actor spoofing | `control_plane/routes.py:294` takes `user_str` from `data.get("user", "unknown")` and passes it to approve (`:296`) / deploy (`:299`); no comparison with the authenticated principal | **Rejected in every option.** Audited actor is the principal only. A test drives a body actor different from the principal and asserts the audit row contains the principal's `.id` / `.role` / `.lab_id` and no spoofed value; default is to omit the attempted value entirely (any optional `details.attempted_actor` inclusion requires explicit owner selection). |
| Audit-database unavailability (fail-closed availability) | No audit write exists at HEAD, so no availability coupling exists today | Under D3(a), an unavailable audit DB fails approval/deploy requests (no committed audit row → no state transition). Owner must explicitly accept this availability loss; a durable outbox is deferred to a separate design package. |

## 6. PostgreSQL-compatible test plan — **UNVERIFIED**

**Environment status:** HEAD test fixtures are SQLite-only. A `gula-postgres` container exists but is not established as a disposable isolated test environment and was **not** used. No `DATABASE_URL` was set. All tests below are **UNVERIFIED**; no SQLite substitute is offered.

Prerequisites for future authorized execution: disposable PostgreSQL 16, synthetic schema/seed only, no PHI/production services, `ENV=test`, a real PostgreSQL `Session` fixture, and monkeypatching of control-plane SDK singletons.

| # | Boundary | Test assertion | Result at HEAD (predicted from source, not executed) |
|---|---|---|---|
| T1 | B1 approval | Drive deploy with `approve_first`; assert exactly one canonical chained row, taxonomy action, principal actor, release id/version, `verify_audit_chain(db)["verified"] is True` | FAIL — no audit row |
| T2 | B2 deployment | Drive deploy alone; assert one canonical chained row and no exception swallowing | FAIL — no audit row. Without `approve_first`, `ReleaseManager.deploy` raises `ValueError` at `manager.py:82-83` **outside** the `try` at `:89-97`; `control_plane/routes.py:292-306` has no handler → **unhandled HTTP 500**. The swallow at `:95-97` wraps only `asyncio.sleep` (`:90-94`), not the approval guard. |
| T3 | B3 secret get/required/rotate | Assert key-name-only audit row, no secret value in `details`, chain verified | FAIL — no writer, no DB session, `access_audit_log()` unused |
| T4 | B4 audit read | GET `/control-plane/audit-log` returns the canonical rows with filters | FAIL — `sdk.audit is None` → empty response |
| T5 | Missing principal | No principal → 401/403, zero rows, no state mutation | HEAD dependency already rejects; service-layer variant unverified |
| T6 | Invalid actor / body spoofing | Body actor different from principal → audit actor equals principal; spoofed value absent | FAIL — HEAD uses body value |
| T7 | Audit failure | Forced canonical writer failure → rollback, no state mutation, non-2xx response | FAIL — HEAD has no audit write |
| T8 | Retry / duplicate event | Repeat the same operation → at most one row per operation under test; duplicate risk recorded | FAIL — no dedupe at HEAD; stronger guarantee needs separate design |
| T9 | Concurrency — **DEFERRED to `P-03-CONCURRENCY`; NOT an acceptance condition of this packet** | Two concurrent approvals on distinct releases → two valid chained rows, no hash corruption | FAIL — no canonical write at HEAD; additionally the unlocked chain-head read (`audit_service.py:106-112`, `:218-225`) allows a multi-worker race that breaks `verify_audit_chain`. This packet adds no serialization; no single-process GREEN may be claimed as multi-worker evidence. |
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
- Every owner-selected boundary has a PostgreSQL RED→GREEN test with assertions **T1–T8 and T10** as applicable (T9 is deferred to `P-03-CONCURRENCY`); synthetic data only.
- Canonical chain verified; no secret value appears in any audit row or response.
- Principal-only actor assertion passes, including the body-spoofing case; missing/invalid actor cases (including permission-version and deactivated-lab rejection) fail closed.
- Audit failure leaves release state unchanged; at-most-once assertion passes with duplicate risk disclosed.
- Owner has explicitly accepted the D3(a) fail-closed availability loss and the D1 disclosure that `POST /control-plane/fleet/deploy` is out of scope unless selected.
- Focused and related suites pass; ruff clean; `git diff --check` exit 0; fresh-context independent review with **0 CRITICAL and 0 HIGH** and all conditions cleared; report in `P-03_AFTER_REV3.md`.

**Engineering rejection (any one):**
- Any CRITICAL/HIGH finding; SQLite substituted for PostgreSQL guard/chain evidence; secret value in audit; body actor accepted; stale shared writer still used for selected boundaries; state mutation on audit failure; schema/migration/new dependency/protected-file change; unrelated file modified; any production access.

**Rollback:** revert only the selected control-plane hunks; no migration or protected-file change. **Operational constraint (working-tree state, not HEAD evidence):** all 20 staged `R100` renames and staged name-status MD5 `56c524d6ffe9872c3a3ac6eff8c8f203` remain untouched by this packet.

## 8. Independent owner decisions required

Each line is a **separate** decision; no decision authorizes another package.

- **D1 — Boundaries:** (a) B1+B2 only (where B2 = `POST /releases/deploy` at `control_plane/routes.py:291-306` **only**); (b) B1+B2+B3; (c) B1+B2+B3+B4; (d) defer; (e) B1+B2+`POST /control-plane/fleet/deploy` (`routes.py:211-226` → `fleet/provisioning.py:36-64`) — the second deployment surface, **out of B2 unless explicitly selected here**. A separate store design is **not** available in this packet.
- **D2 — Actor policy:** (a) authenticated human principal only (recommended); (b) principal plus an explicitly defined authenticated service identity (requires its own design); (c) defer. Request-body actors are rejected in every option.
- **D3 — Failure policy:** (a) fail closed (recommended); (b) durable outbox design package (not authorized here).
- **D4 — Idempotency:** (a) accept at-most-once under test with duplicate-risk disclosure (recommended for this packet); (b) separate dedupe/schema design package.
- **D5 — Audit-read route:** (a) re-point `/control-plane/audit-log` to canonical rows when B4 is selected; (b) leave it unchanged and accept the inert-route risk.
- **D6 — Staging/commit scope:** decided separately from this packet; no commit authority is implied.

Exact combined decision text once the owner has chosen:

> "I authorize package P-03 / AUD-F03 REVISION 3, baselined at HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`, exactly as scoped in `AUDIT_EXECUTION_RECORDS/P-03_DECISION_PACKET_REV3.md`, with D1=__, D2=__, D3=__, D4=__, D5=__. Request-body actors and secret values are never written to audit details. I accept the fail-closed availability loss if I select D3=(a), and I understand `POST /control-plane/fleet/deploy` remains unaudited unless I select D1=(e). I understand T9/concurrent chain integrity is deferred to `P-03-CONCURRENCY`. This decision does not authorize a commit, staging change, push, Draft PR, merge, release, deployment, `PRODUCTION READY`, or any change to HOLD or `production_ready_items = 0`. D6 is decided separately."

Alternative: **"P-03 is deferred; keep AUD-F03 open and this packet prepared."**
