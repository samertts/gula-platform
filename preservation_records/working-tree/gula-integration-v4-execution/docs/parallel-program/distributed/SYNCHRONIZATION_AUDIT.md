# A06 — Synchronization, Event Bus & Event Store Audit

**Program:** PROGRAM-GULA-PARALLEL-001 (GULA National Healthcare Platform, Iraq)
**Agent:** A06 — Offline & Distributed Systems Auditor
**Wave:** A (Discovery / AUDIT ONLY)
**Date:** 2026-11-19
**Companion report:** `docs/parallel-program/distributed/OFFLINE_AUDIT.md` (findings A06-001…A06-011; SCOPE_REQUESTs SR-A06-01…SR-A06-10)
**Status:** COMPLETE — read-only; no source, config, git, service, database or test-execution changes.

---

## 0. Governance and constraints observed

Same as `OFFLINE_AUDIT.md` §0: read-only, only two owned write paths, no git state changes, no services/migrations/chaos/real DB, all user work report-only, evidence with `path:line`, no protocol invention.

Constitution check for this report: no dependency is added. All reviewed implementations use free/open-source building blocks (Python stdlib, SQLAlchemy, PostgreSQL, FastAPI, in-process buses). CRDT/Merkle technologies are discussed **only** as a clearly labelled research evaluation (§7); **no automatic adoption is recommended** and no vendor-specific coupling is proposed.

---

## 1. Scope and inventory

### 1.1 Files reviewed

**Event bus / event store / outbox (kernel):** `backend/app/kernel/event_bus/{bus.py,store.py,outbox.py,inbox.py,retry_queue.py,dead_letter_queue.py,dispatcher.py,replay.py,recovery.py,events.py,versioning.py,snapshot.py}` (directory inventory + substantive reads of the first nine), `backend/app/kernel/routes.py:100-139`, `backend/app/kernel/__init__.py`, `backend/app/kernel/capabilities_registry_populator.py` (search-level).

**Transactional outbox (service):** `backend/app/services/outbox_service.py`, `backend/app/models/outbox.py` (search-level), `backend/app/core/events.py`, `shared/events/bus.py`, `backend/app/worker.py` (search-level), `backend/app/core/startup.py` (search-level).

**Synthetic event vocabulary/store/contracts:** `backend/app/health_core/common/{events.py,event_types.py}`, `backend/app/health_core/integration/{offline.py,conflicts.py}`, `backend/app/health_core/reliability/{idempotency.py,retry.py,sync_conflicts.py}`, `backend/app/health_core/client_integration/{manifests.py,validators.py,observations.py}` (targeted reads/searches).

**Idempotency / reconciliation / retries:** `backend/app/core/idempotency.py`, `backend/app/clinical/command_guard.py`, `backend/app/core/resilience.py`, `backend/app/core/sync_engine.py`, `backend/app/nhdw/offline.py`, `backend/app/insurance/api/{claims.py,payments.py}` (search-level), `backend/app/insurance/financial/engine.py` (search-level), `backend/app/health_data/event_store/store.py` (search-level).

**Tests:** `backend/tests/test_outbox_service.py` (inventory), `backend/tests/kernel/**`, `backend/tests/kernel_hardening/**` (inventory), `backend/tests/health_core/**` (offline/conflicts/reliability tests read).

### 1.2 Protection status (verified `git status --porcelain`)

| Path | Status | Note |
|---|---|---|
| `backend/app/kernel/rules_runtime.py` | **M** | USER WORK — not touched (not an event-bus file). |
| `backend/app/health_core/common/{events.py,event_types.py}`, `backend/app/health_core/integration/{offline.py,conflicts.py}`, `backend/app/health_core/reliability/**`, `backend/tests/health_core/**` | **?? untracked** | USER WORK — report only. |
| `backend/app/kernel/event_bus/**`, `backend/app/services/outbox_service.py`, `shared/events/**`, `backend/app/core/{idempotency,resilience,sync_engine}.py`, `backend/app/models/outbox.py` | clean tracked | Read-only during Wave A. |

### 1.3 Architectural map — four disconnected event/sync stacks

| # | Stack | Entry point | Storage | Delivery / replay | Idempotency | Verdict |
|---|---|---|---|---|---|---|
| 1 | Kernel event bus | `backend/app/kernel/event_bus/bus.py:25-52` | `EventStore` in-memory dict (`:10-27`) | synchronous `dispatcher.dispatch` (`:40-42`); retry/outbox/inbox/DLQ constructed but **not used by `publish`** | none on publish | Prototype |
| 2 | Service transactional outbox | `backend/app/services/outbox_service.py:51-75,81-157` | `outbox_events` SQL table | worker polls 10s, emits to `shared.events` in-process singleton | by DB row id/status only; no event-id dedupe | Partial (durable enqueue, non-durable dispatch) |
| 3 | Health Core synthetic events | `backend/app/health_core/common/events.py:1-71`, `integration/offline.py:57-161` | in-memory `OfflineOutbox` / `ReplayJournal` | deterministic `(occurred_at, sequence)` replay | **strong**: event-id dedupe, fingerprint check, version/gap/stale conflict decisions | Strong contract, non-production |
| 4 | Core offline sync engine | `backend/app/core/sync_engine.py:19-102` | in-memory event log + synced-id set | `reconcile_incoming()` returns decisions only | integer version + LWW timestamp (client-supplied) | Stub / prototype |

There is **no code path connecting stacks 1–4**. `backend/app/core/events.py:16-32` re-exports `shared.events`, which is separate from the kernel bus; Health Core events are explicitly "never published to any real broker" (`common/events.py:3-5`).

---

## 2. Findings

### A06-012 — P1 — Four parallel event stacks with no authoritative event store; all kernel/core stores are non-durable

- **Severity:** P1
- **Title:** Event identity, ordering and idempotency are defined independently in four subsystems; kernel `EventStore` overwrites silently on duplicate id and loses everything on restart.
- **Evidence:**
  - Stack map §1.3 with citations.
  - `backend/app/kernel/event_bus/store.py:12-18` — `self._events: dict[str, Event]`; `save()` assigns `self._events[event.id] = event` with no duplicate detection.
  - `backend/app/kernel/event_bus/bus.py:40-42` — `publish()` calls `store.save()` then `dispatcher.dispatch()`; no outbox/inbox entry is written.
  - `backend/app/health_core/common/events.py:3-6` — synthetic events not published or durably stored.
  - `backend/app/core/sync_engine.py:26-27` — in-memory log/set.
- **Affected components:** `kernel/event_bus/**`, `services/outbox_service.py`, `health_core/**`, `core/sync_engine.py`.
- **Root cause:** Independent workstreams implemented compatible-sounding but incompatible event mechanisms without a single event contract or ownership decision.
- **Safe-fix possible?** No — requires an architecture decision on one authoritative store and a migration of contracts (A01/ORCH).
- **Approval required?** **Yes** — architecture + event-sourcing semantics. **SCOPE_REQUEST SR-A06-11.**

### A06-013 — P1 — Transactional outbox gives durable enqueue but not the advertised at-least-once delivery; failed handlers are marked `done`

- **Severity:** P1
- **Title:** `OutboxWorker.run_once()` ignores the dispatched-handler count and catches handler exceptions inside the bus, so an event whose consumer failed is permanently marked `done` with no retry/DLQ path.
- **Evidence:**
  - `backend/app/services/outbox_service.py:14-16` — documentation claims "At-least-once delivery guarantee".
  - `:112-128` — `dispatched = events.emit(event.event_type, payload)`; on **any** non-exception return (including `0`) the code sets `event.status = "done"` and increments `processed`. The `except` at `:130` only triggers on exceptions from `emit` itself.
  - `shared/events/bus.py:24-38` — `emit()` wraps every handler in `try/except`, logs and continues, returning only the count of handlers that did not raise. It never re-raises.
  - `:44-45` `_BATCH_SIZE=50`, `_POLL_SECS=10`; `:95-105` selects pending/failed with `with_for_update(skip_locked=True)` — good concurrency practice, but no event-id uniqueness in `OutboxEvent` (no dedupe across re-emission).
  - `:227-245` `purge_old_events()` deletes `done`/`failed` rows after 30 days — a failed consumer's evidence can be purged.
- **Affected components:** `outbox_events` dispatch, all downstream clinical notifications/consumers registered on `shared.events`.
- **Root cause:** The bus's failure-swallowing semantics defeat the worker's exception-based retry logic; "was emitted" is treated as "was processed".
- **Safe-fix possible?** No — requires changing delivery semantics and adding a durable DLQ/retry contract; behaviour change outside Wave A.
- **Approval required?** **Yes** — event-delivery semantics (A07/ORCH; A09 for tests). **SCOPE_REQUEST SR-A06-12.**

### A06-014 — P1 — Kernel `publish()` bypasses the outbox/inbox/retry/DLQ components it constructs; DLQ has no automatic ingress

- **Severity:** P1
- **Title:** The kernel event bus advertises outbox, inbox, retry queue and dead-letter queue, but the publish path only saves to a dict and calls handlers; those components are never populated by bus operations.
- **Evidence:**
  - `backend/app/kernel/event_bus/bus.py:28-38` — components instantiated; `:40-42` — `publish()` uses only `store` and `dispatcher`.
  - `grep` over `bus.py` confirms no calls to `self.outbox.enqueue`, `self.inbox.receive`, `self.retry_queue.enqueue`, or `self.dead_letter_queue.send` in the publish path.
  - `backend/app/kernel/event_bus/outbox.py:34-57`, `inbox.py:34-44`, `retry_queue.py:27-41`, `dead_letter_queue.py:29-40` — self-contained APIs with no callers in `bus.py`.
  - `backend/app/kernel/routes.py:112-137` — admin endpoints expose `outbox.list_pending()` and `dlq.list_all()`, which will report zero/empty for events published through `publish()`.
  - `backend/app/kernel/capabilities_registry_populator.py:237-249` registers capabilities "outbox_pattern" and "internal pub/sub event bus with outbox, inbox, dead letter queue, replay, versioning".
- **Affected components:** Kernel observability/admin endpoints, event durability claims, capability registry.
- **Root cause:** Scaffolding assembled without wiring; admin surfaces can give false assurance.
- **Safe-fix possible?** No — requires defining when an event enters outbox/inbox/DLQ and changing the bus contract.
- **Approval required?** **Yes** — kernel event semantics + capability claim accuracy. **SCOPE_REQUEST SR-A06-13.**

### A06-015 — P2 — Async event handlers are fire-and-forget tasks created from a synchronous publish path

- **Severity:** P2
- **Title:** `EventDispatcher.dispatch()` creates untracked `asyncio.Task`s; failures after dispatch are only logged, and `task.exception()` in the done callback can itself raise for cancelled tasks.
- **Evidence:**
  - `backend/app/kernel/event_bus/dispatcher.py:13-24` — `asyncio.create_task(result)` with no retained reference; `:26-33` `_on_handler_complete` calls `task.exception()` unconditionally, then `logger.error`.
  - `backend/app/kernel/event_bus/bus.py:40-42` — `publish()` is a synchronous `def`; it cannot await handler completion.
  - `backend/app/kernel/event_bus/replay.py:18-23` — replay calls `bus.publish()` synchronously, so replayed events also cannot await their handlers.
- **Affected components:** Kernel event dispatch, replay, recovery.
- **Root cause:** Mixing sync publisher with async handlers without lifecycle management.
- **Safe-fix possible?** No — requires async bus API or tracked task set; behaviour change.
- **Approval required?** **Yes** — kernel runtime semantics. **SCOPE_REQUEST SR-A06-14.**

### A06-016 — P2 — Health Core replay orders by client-supplied timestamp string and has no payload integrity check

- **Severity:** P2
- **Title:** `ordered_entries()` sorts on `event.occurred_at` (an ISO string supplied by the producer) before the monotonic sequence; the replay journal verifies event ids and versions but not payload integrity.
- **Evidence:**
  - `backend/app/health_core/integration/offline.py:82-89` — key `(entry.event.occurred_at, entry.sequence)`; string ordering assumes uniform ISO-8601 representation. `new_event()` produces `moment.isoformat()` (`common/events.py:59-69`), but callers may supply any timezone-aware datetime form (offsets `+00:00` vs `Z`, fractional seconds) with different lexical order.
  - `:116-155` — `ReplayJournal.apply()` checks `event_id` dedupe and `version` against expected; no digest/signature verification.
  - Contrast `backend/app/health_core/reliability/sync_conflicts.py:65-70` — `SyncCandidate.__post_init__` verifies `payload_digest = sha256(canonical_json_bytes(event.payload))` and fails closed; and `:162-207` emits a hash-chained audit ledger.
  - `common/events.py:3-5` — events are plain frozen records; any holder can construct one with a chosen `occurred_at`.
- **Affected components:** Health Core synthetic replay/conflict evidence; any future reuse of this contract for real sync.
- **Root cause:** Integrity/ordering guarantees were implemented in the reliability workstream but not propagated to the integration replay contract.
- **Safe-fix possible?** No in Wave A — files are untracked USER work; changing replay ordering/digest changes contract semantics.
- **Approval required?** **Yes** — event contract change; A05/A09 and user release. **SCOPE_REQUEST SR-A06-15.**

### A06-017 — P2 — Kernel retry queue never advances `retry_count`, never dead-letters, and outbox `processing` state can strand

- **Severity:** P2
- **Title:** `RetryQueue.enqueue()` computes a backoff from the current count but nothing increments it; `dequeue_ready()` removes entries permanently; `OutboxPattern.dequeue()` sets `processing` with no recovery path.
- **Evidence:**
  - `backend/app/kernel/event_bus/retry_queue.py:27-35` — `next_retry_at = time.time() + base * 2**entry.retry_count`; `dequeue_ready()` returns ready entries and drops them from `_entries`. No `entry.retry_count += 1`, no re-enqueue, no DLQ handoff.
  - `:37-41` — `retry_count()` reads a count that is never mutated by the queue.
  - `backend/app/kernel/event_bus/outbox.py:37-42` — `dequeue()` sets `status = "processing"`; only `mark_completed`/`mark_failed` exist, and there is no code that reclaims `processing` messages after a crash.
  - `backend/app/kernel/event_bus/dead_letter_queue.py:29-40` — `send()` has no caller in the bus path (A06-014).
- **Affected components:** Kernel retry/DLQ/outbox reliability; capability claims.
- **Root cause:** Component-level stubs without an executor; no state machine for `processing`.
- **Safe-fix possible?** No — requires a retry executor and durable state machine.
- **Approval required?** **Yes** — kernel reliability semantics. **SCOPE_REQUEST SR-A06-16.**

### A06-018 — P2 — `core/sync_engine.reconcile_incoming()` only reports decisions; accepted events are never applied, and LWW trusts client time

- **Severity:** P2
- **Title:** The "version-checked sync" engine has no write path: it appends status dicts but never updates local state or the event log for incoming events; conflict tie-break uses an untrusted timestamp.
- **Evidence:**
  - `backend/app/core/sync_engine.py:46-88` — builds `reconciliation_results` with `ACCEPTED`/`REJECTED_*` only; no `self.local_event_log.append(...)`, no model update, no `mark_as_synced` for accepted incoming events.
  - `:55-57` — `incoming_version`, `incoming_id`, `incoming_ts = event_data.get("timestamp", 0)` from the incoming payload.
  - `:72-79` — equal version decided by `incoming_ts <= local_event.timestamp` (floating client clock).
  - `:63-71` — stale-version rejection compares integer versions but does not handle concurrent equal-version **different values** deterministically other than by timestamp.
  - No vector clock, no Merkle, no signature verification in this module; no tests found (A06-011).
- **Affected components:** Omni-Network offline sync, clinical data convergence.
- **Root cause:** Decision-only prototype mistaken for a reconciliation engine.
- **Safe-fix possible?** No — requires defining an apply path and a trusted ordering source.
- **Approval required?** **Yes** — clinical data semantics. **SCOPE_REQUEST SR-A06-17.**

### A06-019 — P2 — No CRDT or Merkle reconciliation implementation or dependency exists; vector clocks are confined to one in-memory prototype

- **Severity:** P2
- **Title:** Searches for `crdt`, `automerge`, `yjs`, `yrs`, `pouchdb`, `rxdb`, `merkle`, `vector_clock` found no runtime library and no Merkle-based anti-entropy; the only vector-clock logic is `services/offline_sync_service.py`.
- **Evidence:**
  - `backend/app/services/offline_sync_service.py:42,101-118,314-326` — `vector_clock` field, per-entity increment, causal comparison `_has_causal_relationship()`, clock merge — all in-memory, no persistence.
  - `backend/tests/test_offline_conflict_synthetic.py:10-11,233-238` — explicitly states CRDT convergence is **not** claimed and asserts no `crdt` enum remains in the working tree.
  - `git show HEAD:backend/app/services/offline_sync_service.py:19,176-182` — committed HEAD still has a `CRDT_MERGE` that is **not** a CRDT (cross-ref A06-002).
  - Dependency search over `*.txt/*.toml/*.json/*.lock/*.yaml/*.yml`: no CRDT library in project manifests. `@electric-sql/pglite` appears only as an optional peer in `apps/gula-web-suite/pnpm-lock.yaml:2334,2366` and `apps/gula-platform-ui-refresh/pnpm-lock.yaml:2267,2299` (Drizzle-style optional peer), not as a sync engine.
  - `GLOSI/REGISTRY/registry.json:2825-2996` and `GLOSI/REPORTS/evidence/phase3_source_verification.json:229-237` catalogue Automerge/CouchDB as **evaluated** open-source options — catalogue evidence only, no import.
  - No `merkle` match in `backend/app/**` (search result).
- **Affected components:** Sync protocol claims, assurance evidence, dependency governance.
- **Root cause:** Terminology ("CRDT", vector clocks) entered design/evidence artifacts without an implemented algorithm; no anti-entropy design exists.
- **Safe-fix possible?** No — algorithm/dependency decisions are outside Wave A. **No library adoption is recommended by A06** (§7).
- **Approval required?** **Yes** — architecture + dependency governance (A01/ORCH). **SCOPE_REQUEST SR-A06-18.**

### A06-020 — P2 — Idempotency is fragmented across four mechanisms; offline operations have no Idempotency-Key and cannot pass the clinical guard

- **Severity:** P2
- **Title:** Durable clinical idempotency exists (`ClinicalCommandGuard`), plus a DB-key TTL helper and synthetic in-memory processors, but offline sync operations carry no key and no adapter links them.
- **Evidence:**
  - `backend/app/clinical/command_guard.py:34-48` — `require_idempotency_key()` returns 400 when header absent; `:97-176` — `claim()` uses durable `ClinicalCommandReceipt` with unique-key race handling; `:226-276` — `complete()` writes structured audit.
  - `backend/app/core/idempotency.py:1-31,93-152` — header-based `Idempotency-Key`, lab-scoped DB table `idempotency_keys`, TTL cleanup (`:173-181`); no key supplied → "pass through without idempotency protection" (`:103-104`).
  - `backend/app/health_core/reliability/idempotency.py:48-98` — synthetic `SYN-KEY-` in-memory processor with fingerprint conflict.
  - `backend/app/insurance/api/claims.py:52,283-314` and `domain/models.py:426` — separate `idempotency_key` column for claims.
  - `backend/app/services/offline_sync_service.py:35-47` — `SyncOperation` has `operation_id` (hash of entity/ts/device) but **no** `Idempotency-Key` field; no adapter to `ClinicalCommandGuard` found.
  - `backend/app/core/sync_engine.py` — `event_id = uuid4()` per capture, no durable idempotency.
- **Affected components:** Clinical replay safety, offline-to-online apply path, auditability.
- **Root cause:** Idempotency implemented per-surface without a shared key namespace or a replay adapter.
- **Safe-fix possible?** No — requires a cross-cutting contract and clinical-route integration.
- **Approval required?** **Yes** — clinical behaviour + API contract (A05/A07). **SCOPE_REQUEST SR-A06-19.**

### A06-021 — P3 — Outbox cleanup mixes naive and timezone-aware datetimes; processed_at is a single batch timestamp

- **Severity:** P3
- **Title:** `purge_old_events()` uses `datetime.utcnow()` (naive) against `created_at` written with timezone-aware `datetime.now(UTC)`, and `run_once()` snapshots `now` once for the whole batch.
- **Evidence:**
  - `backend/app/services/outbox_service.py:236` — `cutoff = datetime.utcnow() - timedelta(days=days)`; compare `:71` — `created_at=datetime.now(UTC)`.
  - `:92` — `now = datetime.now(UTC)` before the loop; `:117` — `event.processed_at = now` for every event in the batch.
  - `:40-41` — imports `MAX_ATTEMPTS` from `app.models.outbox` (model-level constant).
- **Affected components:** Outbox retention, forensic timing accuracy.
- **Root cause:** Legacy naive-datetime usage retained in one helper.
- **Safe-fix possible?** **Technically yes** (use `datetime.now(UTC)` and per-event timestamps) but not in Wave A.
- **Approval required?** **Yes** — data retention semantics; A07/A08. **SCOPE_REQUEST SR-A06-20.**

### A06-022 — P3 — Recovery engine's PARALLEL/BATCHED replay can violate aggregate ordering

- **Severity:** P3
- **Title:** `RecoveryEngine` offers concurrent replay strategies that do not preserve the deterministic event order used by the replay journal.
- **Evidence:**
  - `backend/app/kernel/event_bus/recovery.py:137-159` — `_execute_parallel` and `_execute_batched` use `asyncio.gather` over events without ordering.
  - `:128-136` — only SEQUENTIAL preserves list order.
  - `backend/app/health_core/integration/offline.py:82-89,116-155` — replay correctness depends on `(occurred_at, sequence)` and strict per-aggregate version increments; a version-2 event applied before version-1 yields a CONFLICT decision.
  - `backend/app/kernel/event_bus/replay.py:18-23` — replay is sequential, but recovery is a separate path.
- **Affected components:** Recovery/replay correctness for event-sourced aggregates.
- **Root cause:** Throughput-oriented strategies added without an ordering contract.
- **Safe-fix possible?** No — requires per-aggregate partition ordering design.
- **Approval required?** **Yes** — recovery semantics. **SCOPE_REQUEST SR-A06-21.**

---

## 3. Event duplication and clinical integrity — assessment

| Concern | Finding | Evidence-based answer |
|---|---|---|
| Duplicate event id on kernel bus | A06-012 | Silently overwrites prior event in `EventStore` (`store.py:14-15`); no conflict signal. |
| Duplicate enqueue in Health Core outbox | — | Handled: `OfflineOutbox.enqueue()` no-op for identical event, raises on id reuse with different payload (`integration/offline.py:63-75`); tested in `test_integration_offline.py:53-69`. |
| Replay idempotency | — | Handled synthetically: second replay yields `DUPLICATE` (`integration/offline.py:122-130`; test `:112-119`). |
| Outbox worker re-dispatch after crash | A06-013 | Durable `pending` rows survive (`outbox_service.py:95-105`), but a handler that threw is marked `done` and never retried. |
| Version gap / stale / divergent events | — | Explicit `ApplyDecision.CONFLICT` with reason codes (`integration/offline.py:131-155`); tested. |
| Payload tampering during replay | A06-016 | Not checked in the replay path; only the reliability conflict module verifies digests. |
| Offline operation → clinical audit | A06-020, OFFLINE A06-002/003 | No durable, authenticated, idempotent path from an offline operation to a clinical receipt/audit record. |

**Conclusion:** idempotency and deterministic conflict *reasoning* are comparatively mature in the synthetic Health Core layer; they are **not connected** to durable dispatch or clinical write paths. Duplicate-event defences differ per stack, so the same event can be a no-op in one stack, an overwrite in another, and a silent success in a third.

---

## 4. CRDT / vector clock / Merkle reconciliation — verification matrix

| Technique | Present? | Evidence |
|---|---|---|
| CRDT algorithm (per-field registers, tombstones, deterministic actor tie-break) | **No** | `test_offline_conflict_synthetic.py:10-11` disclaims it; HEAD's `CRDT_MERGE` is first-seen-key-wins (`git show HEAD:...:176-182`). |
| Automerge/yjs/yrs runtime dependency | **No** | Manifest search across `*.txt/*.toml/*.json/*.lock/*.yaml/*.yml`; only GLOSI catalogue entries (`GLOSI/REGISTRY/registry.json:2825-2996`). |
| Vector clocks | **Partial (prototype only)** | `offline_sync_service.py:42,101-118,314-326`; causal test `test_offline_conflict_synthetic.py` via `_op(..., clock=...)`; no persistence, no server-side use. |
| Merkle tree / anti-entropy digests | **No** | No `merkle` match in `backend/app/**`; `hybrid_router.py:40-41` mentions mesh only as a comment. |
| Hash chains for audit | **Yes (synthetic)** | `health_core/reliability/sync_conflicts.py:162-207`, `audit.py` (hash-chain verify), `assert_full_accounting` (`:210-225`). |
| Last-write-wins | **Yes, multiple variants** | `offline_sync_service.py:183-189`; `core/sync_engine.py:72-79`; `nhdw/offline.py:218-235`; `health_core/integration/conflicts.py:128-136`. Inconsistent tie-breakers (local float time, client float time, ISO strings). |
| Lamport/version vectors in protocol docs | **Documented only** | `docs/sndhs/05-offline-sync.md:51-71`. |

---

## 5. Test coverage — honest assessment

| Area | Tests found | What is actually verified | Gaps |
|---|---|---|---|
| Kernel bus/store/replay/versioning | `backend/tests/kernel/test_event_bus.py`, `test_event_store.py`, `test_events.py`, `test_versioning.py`, `test_recovery.py`, `conftest.py` | Unit behaviour of in-memory components. | Do not verify wiring into `publish()` (A06-014), durability, or cross-stack idempotency. |
| Kernel hardening | `backend/tests/kernel_hardening/{test_chaos_engineering.py,test_performance_baseline.py,test_memory_leaks.py,test_stress.py,test_recovery.py}` | In-process stress/chaos-style unit tests; e.g. `test_recovery.py:55-64` "survives crash" only checks in-memory state after `dequeue()`. | No real crash, restart, broker, DB or network; names overstate durability. |
| Transactional outbox | `backend/tests/test_outbox_service.py` (inventory lines 4-11, 37, 70-235) — atomic emit, rollback, worker processing, attempts/MAX_ATTEMPTS, batch size, Unicode payload. | Solid unit coverage of DB-side outbox behaviour. | Handler-failure-is-marked-done case (A06-013) is not covered as a failure; no real async consumer crash. |
| Health Core offline/replay/conflicts/reliability | `backend/tests/health_core/test_integration_offline.py` (10), `test_integration_conflicts.py` (11), `test_reliability_conflicts.py`, `test_reliability_retry_metrics.py`, `test_contracts_idempotency.py`, `test_quality_review_static.py:314` | Strong synthetic property-based reasoning: idempotency, ordering, full accounting, bounded backoff. | Synthetic/in-memory only; no durable store, no transport, no real clock skew, no clinical values. All files untracked USER work. |
| Core sync engine / hybrid router | **No dedicated tests found** | — | A06-005, A06-018, A06-011. |
| End-to-end reconnect (offline → online → durable apply → audit) | **None found** | — | The single most important missing test; requires an approved isolated environment. |

No tests were executed by A06 (Wave A constraint). No output from prior test runs was supplied to this agent, so pass/fail status is **not asserted** anywhere in this report.

---

## 6. Findings summary

| Severity | IDs | Count |
|---|---|---|
| P0 | (in companion report: A06-001, A06-002) | 2 |
| P1 | A06-012, A06-013, A06-014 (+ companion A06-003…A06-007) | 8 total program-wide for A06 |
| P2 | A06-015…A06-020 (+ companion A06-008, A06-009, A06-010) | 9 total |
| P3 | A06-021, A06-022 (+ companion A06-011) | 3 total |

**Top 5 for this report:** A06-012 (fragmented non-durable event stacks), A06-013 (failed handlers marked done), A06-014 (outbox/DLQ not wired into bus), A06-018 (reconcile-only sync engine), A06-019 (no real CRDT/Merkle; terminology in evidence only).

---

## 7. RESEARCH EVALUATION — decentralized networking / emergency communications

> **CLEARLY-LABELLED RESEARCH EVALUATION ONLY.**
> **A06 does NOT recommend automatic adoption, integration, purchase or dependency addition of any technology described below.** This section evaluates techniques against documented requirements and the platform constitution; it changes no protocol, no code, no dependency manifest and no clinical workflow. Any future proof-of-concept requires a separate orchestrator-approved scope, a free/open-source-first comparison, self-hosting, replaceability analysis, cost analysis, and A04/A05/A07/A08 review.

### 7.1 Why this was evaluated (documented need, not an implementation request)

- `docs/sndhs/05-offline-sync.md:5-13` requires ≥72 h autonomous operation and "no silent overwrite, no double-write" during partitions.
- `:42-48` names multipath transport (cellular + satellite + microwave failover) and mTLS over gRPC/QUIC.
- `backend/app/core/hybrid_router.py:8-12,40-41` defines `LAN`/`MESH`/`OFFLINE` paths; `_execute_lan()` is a stub (`:65-67`).
- These are *requirements/stubs*; no technology decision has been made in the repository.

### 7.2 Techniques worth evaluating (free/open-source first — PROGRAM-CONSTITUTION-001)

| Technique | What it offers | Free/open-source, self-hosted candidates already catalogued or known | Fit / caveats for clinical data |
|---|---|---|---|
| Store-and-forward / Delay-Tolerant Networking (DTN) | Durable bundle queue, custody transfer, reconnect replay | Bundle Protocol implementations (e.g. IETF DTN reference implementations), or a simple self-hosted durable queue on existing PostgreSQL/SQLite | Aligns with "Reuse Before Build" — existing PostgreSQL/SQLite could provide the durable queue before any new protocol. Custody semantics must not be equated with clinical acknowledgement. |
| Anti-entropy via Merkle/high-watermark digests | Efficient divergence detection between regional nodes | Implementable with stdlib hashing over canonical JSON; no library required | Digest comparison detects *difference*, not clinical correctness; conflict policy still requires human-governed rules. |
| CRDTs for **non-clinical** collaboration (e.g. shared notes, inventories) | Convergence without coordination | Automerge (Apache-2.0; catalogued `GLOSI/REGISTRY/registry.json:2825-2996`), CouchDB (Apache-2.0; same registry) | **Not appropriate for clinical results/orders**: automatic merge of clinical values is explicitly rejected by the existing quarantine design (`offline_sync_service.py:239-242`; `test_offline_conflict_synthetic.py:10-11`). Any use must exclude clinical values. |
| Vector clocks / version vectors | Causality detection, concurrent-write identification | Algorithm implementable in-house; prototype exists at `offline_sync_service.py:314-326` | Prototype is in-memory and unauthenticated; a real protocol needs persistence, actor identity, and bounded clock size. |
| Local mesh / ad-hoc emergency comms | Last-mile connectivity during internet outage | Open-source Wi-Fi Direct / LoRa / mesh firmware stacks; existing LAN path stub at `hybrid_router.py:65-67` | Healthcare safety, spectrum regulation (Iraq), device attestation and patient confidentiality are unresolved; requires A04 + regulatory review. No vendor-specific product should be assumed. |
| Emergency bearer channels (satellite/microwave) | Backhaul when fibre/cellular fails | Multiple open standards exist; `docs/sndhs/05-offline-sync.md:45-47` lists cellular/sat/microwave | High cost/complexity, licensing and sovereign-control considerations; would require a documented cost analysis before any evaluation. |

### 7.3 Constitution alignment gate (must be satisfied before any future evaluation)

1. **Free First / Open Source First:** prefer Apache/MIT/BSD/MPL/GPL options above; the GLOSI catalogue already records Apache-2.0 Automerge/CouchDB with licence evidence.
2. **Self-Hosted First:** any queue/broker must run on GULA-controlled infrastructure; no SaaS dependency.
3. **No Vendor Lock-In:** replaceable interfaces; no proprietary protocol baked into clinical records.
4. **Zero Paid Dependency:** any paid bearer service requires an approved cost analysis; none is proposed here.
5. **Reuse Before Build:** existing PostgreSQL/SQLite/Redis and the existing synthetic conflict/replay contracts should be evaluated before any new component.
6. **Local AI First:** unaffected (edge AI already uses local Ollama — `edge_agent/gula_edge_agent/runtime.py:40-48`).
7. **Free Security First:** mTLS/OpenSSL-style controls over commercial security products.

### 7.4 Explicit non-recommendation

A06 recommends **no** adoption decision. The priority is to first establish the basics already in scope: a durable queue, one authoritative event contract, idempotent authenticated replay, explicit human-governed conflict quarantine, and an end-to-end reconnect test (A06-001…A06-003, A06-012…A06-020). Only after those exist would a decentralized/emergency-communications evaluation be meaningful — and even then it must be separately authorized.

---

## 8. SCOPE_REQUESTs (continued from companion report)

| ID | Request | Owner |
|---|---|---|
| SR-A06-11 | Single authoritative event store/contract decision across the four stacks. | A01 / ORCH |
| SR-A06-12 | Redefine outbox delivery semantics; treat handler failure as retryable; add durable DLQ. | A07 / A09 |
| SR-A06-13 | Wire (or remove) kernel outbox/inbox/retry/DLQ; correct admin endpoints and capability registry claims. | A07 / ORCH |
| SR-A06-14 | Async handler lifecycle: tracked tasks or async bus API. | A07 / A08 |
| SR-A06-15 | Canonical timestamp form + payload digest in the Health Core replay contract. | A05 / A09 + user release |
| SR-A06-16 | Kernel retry executor + `processing` reclaim state machine. | A07 |
| SR-A06-17 | Define and implement an apply path for `reconcile_incoming()` or retire the module. | A05 / A07 |
| SR-A06-18 | Correct CRDT/vector-clock/Merkle claims in evidence; no dependency adoption. | A01 / ORCH |
| SR-A06-19 | Shared Idempotency-Key contract bridging offline operations and clinical guard. | A05 / A07 |
| SR-A06-20 | Timezone-correct outbox cleanup and per-event timestamps. | A07 / A08 |
| SR-A06-21 | Per-aggregate ordering for recovery replay strategies. | A07 |
| SR-A06-22 | Approved isolated end-to-end reconnect test environment (static/read-only analysis only in Wave A). | A09 / ORCH |

---

## 9. Closing statement

The synchronization surface is **well supplied with isolated, well-tested synthetic building blocks** but **not assembled into a reliable production path**. The three most consequential gaps are: no authoritative durable event store, an outbox that reports success when consumers fail, and a sync "reconciler" that never applies anything. These are architecture/behaviour decisions for the orchestrator; A06 has made no changes and recommends no new technology.

*End of SYNCHRONIZATION_AUDIT.md.*
