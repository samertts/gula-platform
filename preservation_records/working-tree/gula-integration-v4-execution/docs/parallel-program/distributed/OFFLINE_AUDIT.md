# A06 — Offline Clinical Mode Audit

**Program:** PROGRAM-GULA-PARALLEL-001 (GULA National Healthcare Platform, Iraq)
**Agent:** A06 — Offline & Distributed Systems Auditor
**Wave:** A (Discovery / AUDIT ONLY)
**Date:** 2026-11-19
**Status:** COMPLETE — read-only; no source, config, git, service, database or test-execution changes were made.

---

## 0. Governance and constraints observed

| Rule | Compliance evidence |
|---|---|
| Read-only on all source/config | All investigation used `read`, `glob`, `grep`, `git status --porcelain`, `git diff --stat`, `git show HEAD:<path>` (read-only). No edits outside the two owned report paths. |
| Write only to owned paths | Only `docs/parallel-program/distributed/OFFLINE_AUDIT.md` and `docs/parallel-program/distributed/SYNCHRONIZATION_AUDIT.md`. |
| No git state changes | No add/commit/stage/checkout/stash/merge/worktree operations. |
| No services/migrations/chaos/real DB | No execution of applications, tests, Alembic or database commands. |
| 378 protected paths | All flagged findings on user-owned files are **report-only**. See §1.2. |
| Evidence-based | Every finding cites `path:line` or an exact excerpt. Speculation is explicitly labelled. |

Constitution notes (PROGRAM-CONSTITUTION-001): the reviewed offline stack uses free/open-source components (Python stdlib, SQLite, Fernet/`cryptography`, `httpx`, `vite-plugin-pwa`/Workbox). **No new dependency is recommended.** GLOSI catalogue entries for Automerge/CouchDB (§RESEARCH EVALUATION) are evidence catalogues, **not adopted dependencies** — verified by manifest search (no `automerge`, `yjs`, `yrs`, `pouchdb`, `rxdb` in project lockfiles). No vendor lock-in is introduced by this report.

---

## 1. Scope, inventory and method

### 1.1 Files reviewed (≈50 read directly, plus repository-wide searches)

**Control plane (5):** `AGENTS.md`, `PROGRAM_CONTROL.md`, `AGENT_ASSIGNMENTS.md`, `FILE_OWNERSHIP_MATRIX.md`, `CONFLICT_REGISTER.md`.

**Offline clinical mode (primary):**
- `edge_agent/gula_edge_agent/{agent.py,state.py,runtime.py,security.py}`; `edge_agent/config.example.toml`, `edge_agent/README.md` (directory inventory)
- `backend/app/services/offline_sync_service.py`
- `backend/app/health_core/integration/offline.py`
- `backend/app/core/self_healing.py`
- `backend/app/core/sync_engine.py`; `backend/app/core/hybrid_router.py`; `backend/app/core/resilience.py`
- `backend/app/nhdw/offline.py`
- `backend/app/clinical/command_guard.py`; `backend/app/clinical/failure_injection.py` (search-level)
- `frontend-v3/src/main.tsx`, `frontend-v3/vite.config.ts`, `frontend-v3/public/offline.html`, `frontend-v3/public/manifest.webmanifest`
- `config/quality-gates/offline-gate.py`
- `gula_offline_simulation_test.py`, `gula_offline_simulation_guide.md`
- `docs/sndhs/05-offline-sync.md`
- `backend/app/health_core/client_integration/observations.py` (independent corroboration of FE gaps)
- `backend/app/certification/dimensions/offline.py` (search-level)

**Event/sync stack (detail in the companion report):** `backend/app/kernel/event_bus/**` (bus, store, outbox, inbox, retry_queue, dead_letter_queue, dispatcher, replay, recovery), `backend/app/services/outbox_service.py`, `backend/app/core/events.py`, `shared/events/bus.py`, `backend/app/health_core/common/{events.py,event_types.py}`, `backend/app/health_core/reliability/{idempotency.py,retry.py,sync_conflicts.py}`, `backend/app/health_core/integration/conflicts.py`, `backend/app/kernel/routes.py`.

**Tests read:** `backend/tests/test_offline_sync.py`, `backend/tests/test_offline_conflict_synthetic.py`, `backend/tests/health_core/test_integration_offline.py`, `backend/tests/health_core/test_integration_conflicts.py`, `backend/tests/health_core/test_reliability_conflicts.py`, `backend/tests/health_core/test_reliability_retry_metrics.py`, `backend/tests/kernel_hardening/test_recovery.py`; test inventory via `grep` over `backend/tests/**`.

**Searches executed (read-only):** `idempoten|merkle|vector_clock|reconcil|crdt|automerge|conflict|retry|replay` over `backend/app/**`; `offline|sync_queue|outbox` over `backend/app/**`; dependency manifests for CRDT libraries; tests for `sync_engine|hybrid_router|self_healing|OfflineService|OfflineSyncEngine`.

### 1.2 Protection status of files in this scope (verified `git status --porcelain`)

| Path | Status | Consequence |
|---|---|---|
| `backend/app/services/offline_sync_service.py` | **M (modified, unstaged)** | USER WORK — protected; report only. Contains the *uncommitted* fix for the fake-CRDT defect (A06-002). |
| `backend/app/kernel/rules_runtime.py` | **M** | USER WORK — outside the kernel event-bus path; not touched. |
| `backend/tests/test_offline_sync.py` | **M** | USER WORK — protected; tests the uncommitted fix. |
| `backend/app/health_core/common/events.py`, `event_types.py`, `integration/offline.py`, `reliability/**`, `integration/conflicts.py` | **?? untracked** | USER WORK — protected; report only. |
| `backend/tests/health_core/**`, `backend/tests/test_offline_conflict_synthetic.py` | **?? untracked** | USER WORK — protected; report only. |
| `edge_agent/**`, `gula_offline_simulation_test.py`, `gula_offline_simulation_guide.md`, `config/quality-gates/offline-gate.py`, `frontend-v3/**`, `backend/app/core/{self_healing,sync_engine,hybrid_router}.py`, `backend/app/nhdw/offline.py`, `backend/app/services/outbox_service.py`, `backend/app/kernel/event_bus/**`, `shared/events/**` | clean (tracked, unmodified) in this query | Read-only during Wave A regardless. |

**No file in this scope was modified by A06.**

### 1.3 Executive summary

Offline capability exists in **multiple, disconnected implementations** with no single production path: an in-memory `OfflineSyncEngine` (services), a different same-named `OfflineSyncEngine` (core), a synthetic `OfflineOutbox`/`ReplayJournal` (health_core), a separate SQL-backed `OfflineService` (NHDW), an edge-agent heartbeat loop, a PWA shell with static asset caching, and a standalone simulation script. The strongest, most honest engineering is in the **untracked `health_core` synthetic contract** (idempotent replay, deterministic ordering, explicit conflict decisions, hash-chained accounting). The weakest links are: (a) a simulation that claims successful sync without any server; (b) an unsafe clinical conflict merge that is fixed **only in uncommitted user work**; (c) no durable queue or offline mutation path in the production frontend; (d) stubbed cloud/LAN routing.

**P0 findings require the orchestrator's immediate attention (A06-001, A06-002).**

---

## 2. Findings

### A06-001 — P0 — Offline "reconnection sync" simulation never contacts a server; success claim is self-referential

- **Severity:** P0
- **Title:** `gula_offline_simulation_test.py` marks records `SYNCED` after a local hash check only; no server, transport, acknowledgement, conflict handling or idempotency is exercised.
- **Evidence:**
  - `gula_offline_simulation_test.py:59-83` — `simulate_reconnection_and_sync()` opens the same local SQLite DB, recomputes `sha256(payload)`, and executes `UPDATE offline_queue SET status = 'SYNCED'` (`line 74`). The comment at `line 73` is explicit: `# Simulate successful sync to central DB/DHIS2`.
  - `gula_offline_simulation_test.py:101-102` — `assert synced == 3` followed by `[VERIFICATION PASSED] ... 100% data integrity!`.
  - `gula_offline_simulation_test.py:46-47` — `signature = hashlib.sha256(payload_str.encode()).hexdigest()` — unkeyed digest, not a MAC (see A06-009).
  - `gula_offline_simulation_guide.md:24-34` instructs operators to run this script on reconnect and accept criteria `0% data loss`, `مطابقة تامة لجميع التوقيعات`, `<30s` full sync.
  - `grep` over `.github/workflows/**` found **no** reference to this script or to `offline-gate.py`.
- **Affected components:** Offline simulation/field guide, clinical-integrity evidence, quality-gate narrative; potential operator reliance during real outages.
- **Root cause:** A local-state transition was labelled as an end-to-end integration result. No server interface exists in the script, so integrity is defined as "the local bytes still match their local digest".
- **Safe-fix possible?** No — this is not a code patch in Wave A. Requires a real, isolated test environment with a disposable server/DB and an explicit ORCH/QA-approved test design. The guide's success criteria must be rewritten before any field use.
- **Approval required?** **Yes** — changes to clinical offline evidence/success criteria and any new test harness are outside A06's write set and require orchestrator + A05 (clinical) + A09 (QA) approval. Label any claim of "sync verified" as **UNVERIFIED** until then.
- **Note (labelled speculation):** It is plausible that the script was intended as a UI/demo aid only; however, the guide presents it as a pre-disaster operational test, so the risk of misinterpretation is concrete, not hypothetical.

### A06-002 — P0 — Unsafe first-seen-key-wins `CRDT_MERGE` remains in committed HEAD; safe fix exists only in uncommitted user work

- **Severity:** P0
- **Title:** The committed (`HEAD`) conflict resolver silently selects the first-seen value for every contested key; the corrected non-CRDT quarantine strategy is an unstaged user modification and will be lost from any build made from `HEAD`.
- **Evidence:**
  - `git show HEAD:backend/app/services/offline_sync_service.py` (read-only): line 19 `CRDT_MERGE = "crdt_merge"`; lines 176-182:
    ```python
    elif resolution == ConflictResolution.CRDT_MERGE:
        merged = {}
        for op in (conflict.operation_a, conflict.operation_b):
            for k, v in op.data.items():
                if k not in merged:
                    merged[k] = v
        result = merged
    ```
  - Working tree `backend/app/services/offline_sync_service.py:20-25` documents the removal: "the former `CRDT_MERGE = "crdt_merge"` was a first-seen-key-wins dictionary merge. It is NOT a CRDT ...". `:200-248` implements `CONFLICT_QUARANTINE`, retaining both contested values with provenance; `:174-181` adds replay idempotency; `:253-269` records deterministic `resolved_at`.
  - `git status --porcelain -- backend/app/services/offline_sync_service.py backend/tests/test_offline_sync.py` → ` M` on both; `git diff --stat` → 95 and 33 lines changed respectively (+109/−19).
  - `backend/tests/test_offline_conflict_synthetic.py:1-14` (untracked) explicitly states the old behaviour "could silently overwrite a clinical value".
  - `security-audit/bandit.json:92001` contains a stale reference to `def test_crdt_merge(self)` — corroborates that the unsafe version circulated in an earlier evidence artifact.
- **Affected components:** `backend/app/services/offline_sync_service.py`, `backend/tests/test_offline_sync.py`, `backend/tests/test_offline_conflict_synthetic.py`, any deployment/CI built from committed state.
- **Root cause:** A clinically significant remediation (F-069/D-023) was applied in the working tree but never committed. Committed code still offers a resolution mode that picks a value by arrival order, with no deterministic actor tie-break, no tombstones, no per-field registers, and no idempotent replay — so a lab result can be silently overwritten during reconnect.
- **Safe-fix possible?** No in Wave A (file is modified user work). The safe path is for the **user/orchestrator** to review and commit the existing working-tree change, after which Wave C may treat it as clean. A06 must not stage or commit it.
- **Approval required?** **Yes** — user-owned modified file + clinical conflict semantics + git state change. Requires explicit user release and orchestrator approval. **P0 halt:** no offline conflict-resolution behaviour should be certified or exercised against clinical data until HEAD contains the fix.
- **SCOPE_REQUEST:** SR-A06-01 (commit/release ownership of the F-069 fix) — see §6.

### A06-003 — P1 — No durable offline queue in any production path; all primary stores are process-local

- **Severity:** P1
- **Title:** Offline operations, signatures, vector clocks and replay journals live only in Python dictionaries/sets; a process restart loses all pending clinical work.
- **Evidence:**
  - `backend/app/services/offline_sync_service.py:81-86` — `_operations`, `_conflicts`, `_vector_clocks`, `_sync_log` are in-memory containers; `:339-348` `EncryptedSyncStore` is an in-memory `dict[str, bytes]`.
  - `backend/app/health_core/integration/offline.py:9` — explicit: "No queue, broker, database, network or filesystem is involved."; `:60-61` `OfflineOutbox._entries` dict; `:103-105` `ReplayJournal._applied`/`_versions`.
  - `backend/app/health_core/common/events.py:1-6` — events "are not published to any real broker and are not written to any durable store".
  - `backend/tests/test_offline_conflict_synthetic.py:12` — "Crash durability remains NOT VERIFIED (F-028: in-memory store)."
  - `backend/tests/kernel_hardening/test_recovery.py:55-64` — `test_outbox_survives_crash` only checks `list_pending()` after an in-process `dequeue()`; **no crash or restart occurs** (misleading evidence label).
  - The only real persistence found is `backend/app/nhdw/offline.py:57-67` (`nhdw_offline_changes` SQL table) and the standalone simulation's `/tmp` SQLite DB (`gula_offline_simulation_test.py:15`) — neither is wired to the edge agent or frontend.
- **Affected components:** Offline capture, reconnect replay, conflict audit, all offline-capable clients.
- **Root cause:** Prototype/harness design was retained as the apparent production contract; durability was never promoted from the synthetic layer into a runtime store.
- **Safe-fix possible?** No — requires selecting a self-hosted durable store (existing PostgreSQL/SQLite infrastructure), defining a durable schema, and approval. No new technology is recommended by A06 (Reuse Before Build: PostgreSQL/SQLite already present).
- **Approval required?** **Yes** — clinical data durability and DB schema changes (`FILE_OWNERSHIP_MATRIX` §4; A07 primary). Cross-scope with A07/A09.

### A06-004 — P1 — Frontend PWA has no offline mutation queue, IndexedDB store or background sync; `offline.html` is not wired; offline gate checks substrings only

- **Severity:** P1
- **Title:** The production SPA can display a static fallback page but cannot capture orders/results offline or replay them on reconnect.
- **Evidence:**
  - `frontend-v3/vite.config.ts:11-76` — `VitePWA` with `registerType: 'autoUpdate'`; `workbox` config (`:45-71`) contains only `globPatterns` and `runtimeCaching` for images/fonts. There is **no** `navigateFallback`, `offline`, API runtime caching, or background-sync plugin.
  - `frontend-v3/src/main.tsx:6-17` — only `registerSW` from `virtual:pwa-register`; no offline queue initialisation.
  - `frontend-v3/public/offline.html:1-48` exists but no source/config reference to it was found (`grep` over `frontend-v3/**`); with generated SW and no `navigateFallback`, it is an unattached asset.
  - Repository-wide grep for `IndexedDB|indexedDB|SyncManager|offlineOutbox|offline_queue` in `frontend-v3/**` found **zero** matches (only `playwright.config.ts:16 serviceWorkers: "block"` and `main.tsx:9`).
  - `config/quality-gates/offline-gate.py:28-110` — checks file-name substrings and in-file keyword presence (`'sync' in content.lower() and ('queue' ... or 'SyncManager' ...)` at `:93-96`). It would pass on comments or dead code; it does not execute the app.
  - No workflow in `.github/workflows/**` references `offline-gate.py` (search result: no matches).
  - Independent corroboration: `backend/app/health_core/client_integration/observations.py:132-144` records `LayerKey.OFFLINE_OUTBOX` = `ABSENT` and `SYNC_CONFLICT` = `ABSENT` for frontend-v3: "no client outbox or replay module", "Readiness page explicitly records version conflict/audit contract as unproven".
- **Affected components:** `frontend-v3` PWA, offline clinical capture, offline gate/CI evidence.
- **Root cause:** PWA installability was implemented (manifest, icons, SW registration) but offline-first data capture was not; a static asset was mistaken for an offline capability.
- **Safe-fix possible?** No — requires FE design plus durable queue decisions and contract tests; files are owned by A02/A03/A09 and `frontend-v3/vite.config.ts`/`package.json` are user-modified (protected).
- **Approval required?** **Yes** — FE clinical workflow behaviour, user-modified config, and CI semantics. **SCOPE_REQUEST SR-A06-02.**

### A06-005 — P1 — Hybrid network router's cloud and LAN branches are empty stubs; OFFLINE branch discards the request

- **Severity:** P1
- **Title:** `HybridNetworkRouter.route_request()` returns `None` for INTERNET/LAN and a bare status dict for OFFLINE — no request is executed and nothing is enqueued.
- **Evidence:**
  - `backend/app/core/hybrid_router.py:43-59` — dispatch to `_execute_cloud` / `_execute_lan` / offline queue.
  - `backend/app/core/hybrid_router.py:61-67` — `def _execute_cloud(...): pass` and `def _execute_lan(...): pass` (the file ends at line 67).
  - `:56-59` — offline branch returns `{"status": "queued", "mode": "offline"}` without creating any queue record.
  - `get_best_path()` (`:31-41`) can therefore select a path whose execution is a no-op; `NetworkPath.MESH` is defined (`:11`) but never returned.
- **Affected components:** Offline/low-connectivity clinical request routing; integration with `core/sync_engine.py`.
- **Root cause:** Skeleton implementation presented as "Intelligently routes clinical data requests" (`:15-17`). No queue integration and no error/return contract.
- **Safe-fix possible?** No — implementing transport and queue semantics is a behaviour change outside Wave A and outside A06 ownership.
- **Approval required?** **Yes** — clinical request routing + new queue/transport semantics; requires orchestrator and A05/A07. **SCOPE_REQUEST SR-A06-03.**

### A06-006 — P1 — NHDW offline batch applies LWW by ISO-string comparison and marks every change conflicted if any one change conflicts

- **Severity:** P1
- **Title:** `OfflineService.apply_batch()` can overwrite clinical rows based on lexical timestamp comparison and uses a batch-level `conflicts` counter to set per-record sync status; `resolve_conflict()` auto-selects a winner.
- **Evidence:**
  - `backend/app/nhdw/offline.py:179-196` — `remote_updated = change.data.get("updated_at", "")`; `local_updated = existing.updated_at.isoformat() ...`; comparison `remote_updated > local_updated` is string comparison, not timezone-aware datetime comparison; ISO strings with differing offsets/fractional seconds are not reliably ordered.
  - `:188-189` — conflicting change increments a shared `conflicts` counter but does **not** mark that specific record.
  - `:209-211` — `change_in_db.sync_status = SyncStatus.CONFLICT if conflicts > 0 else SyncStatus.SYNCED` applied **to every change in the batch**; a single conflict labels all records conflicted (and a later clean record can be left CONFLICT).
  - `:218-235` — `resolve_conflict()` picks `winner = remote_data if remote_ts >= local_ts else local_data` and logs `strategy: "last_write_wins"` — automatic clinical selection, no quarantine/human workflow, same string-comparison weakness.
  - `:181-196` — updatable key filter excludes `id, lab_id, created_at, created_by, version` but not `updated_at`/`sync_status`; ownership fields are client-influenced.
- **Affected components:** NHDW hospital operations offline sync (admissions, transfers, tasks, ward rounds, care plans, alerts), clinical auditability.
- **Root cause:** Client-supplied strings used as authoritative clocks; conflict state tracked at batch scope; no explicit conflict strategy contract (contrast `health_core/integration/conflicts.py:18-23`, which offers named strategies with full accounting).
- **Safe-fix possible?** No — clinical write semantics and DB behaviour change; requires A05/A07 and explicit human-reconciliation policy.
- **Approval required?** **Yes** — clinical logic + DB writes. **SCOPE_REQUEST SR-A06-04.**

### A06-007 — P1 — Large gap between the documented sovereign offline protocol and any implemented code

- **Severity:** P1
- **Title:** `docs/sndhs/05-offline-sync.md` specifies a 72-hour autonomous RSN, signed envelopes, vector clocks, replay tokens, gRPC/QUIC with mTLS, WORM audit mirroring and bandwidth tiers; the reviewed implementation provides none of these transport/crypto properties.
- **Evidence:**
  - `docs/sndhs/05-offline-sync.md:5-13` — "fully autonomously for ≥ 72 h", "No data loss. No silent overwrite. No double-write."
  - `:42-48` — session layer "signed envelope, vector clocks, replay tokens"; transport "gRPC over QUIC, mTLS ... multipath".
  - `:51-71` — per-RSN `local_seq`, `vector_clock[rsn]`, signed chunked pull/push, ack high-watermark, 7-day replay window.
  - Actual code: `backend/app/services/offline_sync_service.py:42,101-118` has only per-entity in-memory vector clocks with an unkeyed SHA-256 signature (`:328-336`); `backend/app/core/hybrid_router.py:61-67` has no transport; `backend/app/kernel/event_bus/**` is in-memory with no broker; `docs/sndhs/05-offline-sync.md` has no implementation cross-reference in the audited modules.
- **Affected components:** Architecture/compliance claims, RSN offline design, procurement/assurance evidence.
- **Root cause:** Design document and implementation evolved independently; no traceability matrix binds the specified protocol to code.
- **Safe-fix possible?** No — this is a program-level scope decision. A06 recommends **labelling the document as target-state design**, not as verified capability (no new technology adoption implied).
- **Approval required?** **Yes** — architecture/governance claim change (ORCH + A01). **SCOPE_REQUEST SR-A06-05.**

### A06-008 — P2 — Edge agent has no offline result backlog and accepts server-controlled loop timing

- **Severity:** P2
- **Title:** Failed task-result reports are logged and dropped; heartbeat interval and kill-switch/quarantine states come from the server response with no local durability.
- **Evidence:**
  - `edge_agent/gula_edge_agent/agent.py:173-182` — `_report_result()` catches all exceptions and only logs `logger.warning("result reporting failed: %s", exc)`; no retry queue, no local spool.
  - `:186-225` — main loop: `resp.get("kill_switched")` (`:192`), `resp.get("quarantined")` (`:196`), `self._heartbeat_s = int(resp.get("next_heartbeat_s", 30))` (`:221`), then `await asyncio.sleep(max(5, self._heartbeat_s))` (`:225`). There is no upper bound on the server-supplied interval (only a 5s floor).
  - `:107-128` — heartbeat errors return `{}`, silently pausing task execution for another interval.
  - `edge_agent/gula_edge_agent/state.py:3-15,74-84` — encrypted state file persists `completed_uids` (ack-style cleanup) but no pending-task/result queue is persisted.
- **Affected components:** Edge AI task results, offline resilience, device lifecycle.
- **Root cause:** Fire-and-forget HTTP reporting; control-plane responses trusted for scheduling without local policy envelope.
- **Safe-fix possible?** No in Wave A — requires edge runtime behaviour change; `edge_agent/**` is clean but outside a remediation wave.
- **Approval required?** **Yes** — edge-agent behaviour + security policy on control-plane timing. **SCOPE_REQUEST SR-A06-06.**

### A06-009 — P2 — "Digital signature" in the offline guide/simulation is an unkeyed digest; sync signatures use an undefined shared secret and non-constant-time comparison

- **Severity:** P2
- **Title:** Integrity claims rely on SHA-256 of the payload without a key; the sync engine's HMAC-like construction has no key management and uses `==` comparison.
- **Evidence:**
  - `gula_offline_simulation_test.py:46-47` and `:70-72` — `hashlib.sha256(payload)` recomputed and compared; no secret, no signer identity.
  - `gula_offline_simulation_guide.md:21,33` — calls these `بصمات التحقق الرياضية (SHA-256)` / `التوقيعات الرقمية` (digital signatures) and sets a "perfect match" success criterion.
  - `backend/app/services/offline_sync_service.py:328-336` — `_sign_operation()` = SHA-256 of `{op_id}:{json(data)}:{device_id}:{self._device_secret}`; `_verify_signature()` uses `op.signature == expected` (plain string comparison, not `hmac.compare_digest`). The "secret" is a constructor argument (`:81`), with no generation, storage, rotation or per-device identity binding.
  - `edge_agent/gula_edge_agent/security.py:1-13` — states the agent cannot verify server task signatures at all; a public verification key is only a "future hardening step".
- **Affected components:** Offline integrity evidence, device authenticity, clinical non-repudiation.
- **Root cause:** Digest-of-data conflated with authenticated integrity; no key-management design in the prototype.
- **Safe-fix possible?** No — key management and signature protocol are a security design change (A04 primary).
- **Approval required?** **Yes** — security protocol change. **SCOPE_REQUEST SR-A06-07** (cross-ref A04); no algorithm/technology adoption is recommended here.

### A06-010 — P2 — Redis-only degradation may never clear: success path omits degradation recomputation

- **Severity:** P2
- **Title:** `checked_redis_connection()` does not call `health.update_degraded_state()` on success, so an L1_CACHE_HEAVY state entered on Redis failure can persist after Redis recovers.
- **Evidence:**
  - `backend/app/core/self_healing.py:297-309` — success branch (`:302-304`) records success and returns `True`; `update_degraded_state()` is called only in the exception branch (`:308`).
  - Contrast `:278-294` — DB check calls `update_degraded_state()` on both success (`:288`) and failure (`:293`).
  - `:234-256` — `update_degraded_state()` is the only path that exits L1/L2 to NONE when circuits are closed.
  - `:438-459` — `RecoveryWorker._probe_services()` probes only circuits in `OPEN`/`HALF_OPEN`; with DB closed and Redis recovered, no other probe recomputes the level.
- **Affected components:** Degraded-mode middleware, offline/low-resource operation of the backend.
- **Root cause:** Asymmetric circuit-recovery bookkeeping between the DB and Redis wrappers.
- **Safe-fix possible?** **Technically yes** (one-line call on the success path) but **not in Wave A**: file is clean but Wave C is blocked, and this alters runtime resilience behaviour.
- **Approval required?** **Yes** — resilience behaviour change; A08 (reliability) primary. **SCOPE_REQUEST SR-A06-08.**

### A06-011 — P3 — Two unrelated classes named `OfflineSyncEngine` create an ambiguous contract

- **Severity:** P3
- **Title:** `services/offline_sync_service.py` and `core/sync_engine.py` both define `OfflineSyncEngine` with different data models and conflict semantics.
- **Evidence:**
  - `backend/app/services/offline_sync_service.py:80-86` — vector clocks, signed operations, conflict quarantine.
  - `backend/app/core/sync_engine.py:19-27` — `local_event_log` + `synced_event_ids`, integer versions, LWW-by-timestamp in `reconcile_incoming()` (`:46-88`).
  - Test inventory: `grep OfflineSyncEngine backend/tests/**` matches only the `services` variant in `test_offline_sync.py` and `test_offline_conflict_synthetic.py`; the `core` variant has **no tests found**.
- **Affected components:** Developer/onboarding clarity, import correctness, assurance traceability.
- **Root cause:** Parallel prototypes retained without a canonical naming/ownership decision.
- **Safe-fix possible?** No in Wave A — renaming is a code change across possibly unknown importers.
- **Approval required?** **Yes** — code/API naming; A01/A07. **SCOPE_REQUEST SR-A06-09.**

---

## 3. Clinical integrity of offline operations (orders / results)

| Question | Evidence-based answer | Confidence |
|---|---|---|
| Are offline-created operations persisted? | **No** in the production path — in-memory dicts/sets (A06-003). Only NHDW has a SQL table, and the simulation has a `/tmp` SQLite DB. | High |
| Can an offline result silently overwrite another value? | **Yes in committed HEAD** via `CRDT_MERGE` (A06-002). In the uncommitted working tree, `CONFLICT_QUARANTINE` retains both values and refuses to auto-select clinical keys (`offline_sync_service.py:223-242`). | High |
| Is the offline operation authenticated? | Weak/undefined: unkeyed digest in simulation (A06-009); shared-secret SHA-256 with no key lifecycle in the sync engine. | High |
| Is replay idempotent? | In the **working tree** `health_core` outbox/replay and conflict resolution are idempotent (`integration/offline.py:63-75,122-130`; `offline_sync_service.py:174-181`). In **HEAD** `resolve_conflict` has no `resolved_at` guard — repeated calls append duplicate audit rows. | High |
| Is there an audit trail for offline decisions? | Synthetic only: `_sync_log` (in-memory), hash-chained `health_core/reliability/sync_conflicts.py:162-207` (untracked, synthetic). No durable clinical audit record for offline writes. | High |
| Do offline operations satisfy clinical Idempotency-Key requirements? | **No evidence of integration.** Clinical routes require `Idempotency-Key` (`backend/app/clinical/command_guard.py:34-48`), but `SyncOperation` (`offline_sync_service.py:35-47`) has no such field; no adapter was found. | High |
| What happens to an order/result created in the PWA while offline? | **Nothing is captured.** No offline queue/IndexedDB/background sync in `frontend-v3` (A06-004). | High |

**Conclusion (evidence-based):** offline clinical operations are **not currently safe or auditable end-to-end**. The synthetic contracts demonstrate that correct behaviour is *designable* (idempotent replay, explicit conflict accounting), but the production path lacks durability, transport, authentication and a durable audit chain. This conclusion does **not** alter any clinical protocol; it reports the gap.

---

## 4. Test coverage — honest assessment

| Test file | Status | What it really covers | Gaps |
|---|---|---|---|
| `backend/tests/test_offline_sync.py` (M — USER) | 14 tests: create, receive, signature rejection, pending/synced, clear, vector clock, LWW, conflict detection, quarantine (new), sync log, duplicate, causal ops, encrypted store. | Pure in-process logic of the *services* engine. | No persistence/restart, no network, no multi-node real sync, no clinical route integration, no Idempotency-Key, no durability proof. Tests the **uncommitted** fix. |
| `backend/tests/test_offline_conflict_synthetic.py` (?? — USER) | 12 tests: quarantine non-overwrite, agreed merge, out-of-order arrival, 2-node reconnect, multi-node no-loss, duplicate, idempotent audit row, manual resolution, invalid signature, replay recovery, no-CRDT enum. | Honest synthetic contract; explicitly disclaims CRDT convergence and crash durability (`:10-13`, `:222-224`). | Synthetic only; no durable store, no real clock skew, no server/DB; "recovery" is replay into a new in-memory engine. |
| `backend/tests/health_core/test_integration_offline.py` (?? — USER) | 10 tests: monotonic sequences, duplicate enqueue, reused event_id rejection, `(occurred_at, sequence)` ordering, replay/versions, second-replay duplicate, divergent/stale/gap decisions, tenant-scoped keys. | In-memory outbox/replay contract. | No durable storage, no signature/hash verification of payloads, no real reconnect. |
| `backend/tests/health_core/test_integration_conflicts.py` (?? — USER) | 11 tests: REJECT/KEEP_FIRST/KEEP_LAST, full accounting, order-independence, decision IDs, fail-closed validator, invalid candidate sets. | Deterministic conflict decisions + in-memory audit records. | Strategies auto-select a winner by `occurred_at` (`:94-95,128-136`) — no clinical quarantine assertion at this layer. |
| `backend/tests/health_core/test_reliability_conflicts.py`, `test_reliability_retry_metrics.py` (?? — USER) | Hash-chained per-candidate accounting; bounded jitter-free backoff, DLQ, metrics. | Strong synthetic reliability properties. | No runtime executor (retry delays are computed, never slept); no DB/network. |
| `backend/tests/kernel_hardening/test_recovery.py` | `test_outbox_survives_crash` (`:55-64`) only checks in-memory state after `dequeue()`. | Component behaviour. | **Misleading name** — no process crash/restart (A06-003). |
| `gula_offline_simulation_test.py` | Standalone script, not pytest; no CI reference found. | Local SQLite hash round-trip. | Not an integration test (A06-001). |
| `backend/app/core/{sync_engine,hybrid_router}.py`, `backend/app/nhdw/offline.py` | **No dedicated tests found** (`grep` over `backend/tests/**`). | — | Critical untested offline/sync surfaces (A06-005, A06-006, A06-011). |
| `config/quality-gates/offline-gate.py` | String-existence gate, not wired into CI (search). | Manifest/SW/offline-page/keyword presence. | Would pass with dead code; no behavioural assertion (A06-004). |

**Coverage verdict:** good *unit-level honesty* in the synthetic contract tests; **no end-to-end offline evidence** (persist offline → disconnect → reconnect → idempotent server apply → durable audit). No tests were executed by A06 (Wave A constraint).

---

## 5. RESEARCH EVALUATION — decentralized / emergency communication (summary)

> **Clearly labelled RESEARCH EVALUATION ONLY. No automatic adoption of any new technology is recommended by A06.** The full section, including free/open-source options and constitution alignment, is in `SYNCHRONIZATION_AUDIT.md` §7. Nothing in this section changes a protocol, dependency list or clinical workflow.

- The repository already contains **catalogue-only** evidence for open-source CRDT/DVN technologies: `GLOSI/REGISTRY/registry.json:2825-2996` (Automerge, Apache CouchDB) with licence/activity metadata. No project manifest imports them (verified by manifest grep).
- Mesh/LAN/offline concepts appear only as **design/stub** code: `backend/app/core/hybrid_router.py:8-12,40-41` and `docs/sndhs/05-offline-sync.md:38-48`.
- Research themes worth *evaluating later* (no adoption decision): delay-tolerant networking store-and-forward, CRDTs for non-clinical collaborative notes, Merkle/high-watermark anti-entropy, and emergency bearer channels (satellite/microwave/Wi-Fi Direct as referenced in `docs/sndhs/05-offline-sync.md:45-47`). Each carries clinical-integrity, security and governance costs that require independent approval.
- **Constitution alignment:** any future evaluation must start from free/open-source, self-hosted, replaceable options and document cost/licence analysis (`AGENTS.md`, `docs/constitution/COST_GOVERNANCE.md`). A06 has not added any dependency.

---

## 6. SCOPE_REQUESTs (for the orchestrator; A06 took no action)

| ID | Request | Reason / owner |
|---|---|---|
| SR-A06-01 | Obtain user release + approval to commit the working-tree F-069 fix in `offline_sync_service.py` / `test_offline_sync.py`, or treat HEAD's `CRDT_MERGE` as a P0 block. | USER files + clinical semantics; ORCH + user. |
| SR-A06-02 | Assign FE offline-queue work and gate redesign to A02/A03/A09; unhook/replace the substring gate. | `frontend-v3/**` user-modified; A02/A03/A09. |
| SR-A06-03 | Decide whether `core/hybrid_router.py` is production scope; if so, assign transport/queue implementation. | Behaviour change; A01/A07/ORCH. |
| SR-A06-04 | Review NHDW LWW/conflict semantics for clinical acceptability; assign A05/A07. | Clinical + DB write semantics. |
| SR-A06-05 | Label `docs/sndhs/05-offline-sync.md` as target-state design or produce traceability to code. | Governance claim; A01/ORCH. |
| SR-A06-06 | Edge-agent result spool + bounded control-plane heartbeat policy. | Edge behaviour/security; A04/A08. |
| SR-A06-07 | Define offline integrity signature/key-management design. | Security protocol; A04. |
| SR-A06-08 | Fix Redis-success degradation recomputation in `self_healing.py`. | Resilience behaviour; A08. |
| SR-A06-09 | Canonicalise the two `OfflineSyncEngine` classes/names. | API clarity; A01/A07. |
| SR-A06-10 | Provide an approved isolated test environment for a real reconnect test (no real DB, no chaos). | QA evidence; A09/ORCH. |

---

## 7. Closing statement

A06 found **2 P0, 5 P1, 3 P2, 1 P3** findings in the offline surface. The most important immediate action is not a code edit by this agent but a **governance decision**: the only clinically safe conflict-resolution behaviour in this scope currently exists as **uncommitted user work**, while the committed code can silently overwrite a contested clinical value. Until that is resolved and a real end-to-end reconnect test exists, any claim of verified offline clinical integrity must be treated as **UNVERIFIED — عالي المخاطر / high risk**.

*End of OFFLINE_AUDIT.md.*
