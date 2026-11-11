# Systemic Concurrency Pattern — Findings Across the Repo

Continuation of the concurrency-continuation directive. Both prior findings
(`payments-capture-refund-cas`, `device-outbox-claim-cas`) were the same
root shape: a live mutation service read a row with a plain `SELECT`, then
mutated and wrote it back with no row lock and no version check. This
document generalizes the search rather than re-auditing one more domain
in isolation.

## 1. Outbox/queue implementation inventory (Section 6)

Three distinct outbox-pattern implementations exist in this repo:

| Implementation | Persistence | Claim mechanism | Reachability | Disposition |
|---|---|---|---|---|
| `app/services/outbox_service.py::OutboxWorker` | `outbox_events` table (real migration, in the CI-required table list) | `.with_for_update(skip_locked=True)` — **already present** | Live: wired to a background `asyncio` loop from `main.py` lifespan; this is the platform's canonical, at-least-once event-delivery mechanism | **VERIFIED SAFE** — already correct, comment even documents why ("safe for multiple workers"). No change needed. |
| `app/devices/outbox.py::process_batch` | `device_outbox_messages` table (real migration) | Was a plain unlocked `SELECT` | Live: reachable via `POST /device-integration/outbox/process` | **FIXED this session** — `device-outbox-claim-cas`, see `docs/security/DEVICES_OUTBOX_CAS_STATUS.md` |
| `app/kernel/event_bus/outbox.py::OutboxPattern` | **In-memory Python list only** — not persisted, would lose all state on process restart regardless of locking | Plain unlocked iteration (`dequeue()`) | Instantiated on every `EventBus` (used by `identity/events.py`, `kernel/runtime/bootloader.py`, and 5 `national/*` routers), **but its `dequeue`/`enqueue`/`mark_completed`/`mark_failed` methods have exactly zero call sites anywhere in the repo** (grepped exhaustively) — only `list_pending()` is ever called (`kernel/routes.py:120`, a read-only count for a stats endpoint) | **DEAD_OR_UNREACHABLE** — not a live vulnerability. The class exists and is race-shaped, but nothing ever calls the methods that would race. Not fixed (nothing to fix — nothing to reach); flagged rather than silently ignored per this directive's own finding-lifecycle rule. |

**GULA does not have one canonical outbox pattern — it has one canonical
implementation (`app/services/outbox_service.py`) plus two domain-local
reimplementations of varying quality** (`devices` real-but-was-unsafe,
`kernel/event_bus` unsafe-but-unreachable). No merge is proposed: the
devices one is intentionally domain-scoped (per-lab tenant isolation,
`device_outbox_messages.lab_id`) which the canonical one does not need
(it is platform-wide); merging them would be an architecture change
outside this pass's authority, consistent with this session's standing
rule against duplicating/conflicting with in-progress ownership.

## 2. Concurrency proof template applied (Section 5)

For both `payments-capture-refund-cas` and `device-outbox-claim-cas`:
reproduced pre-fix on a real disposable PostgreSQL 16 database with two
genuine threads/connections and a `threading.Barrier`, classified
**VULNERABLE**, fixed (`SELECT ... FOR UPDATE` / `FOR UPDATE SKIP
LOCKED`), reproduced post-fix (closed), negative-proofed (`git stash`
byte-identical revert/restore), permanent regression test added, full
suite rerun clean. Full evidence already committed:
`docs/security/PAYMENTS_CAPTURE_REFUND_CAS_STATUS.md`,
`docs/security/DEVICES_OUTBOX_CAS_STATUS.md`.

## 3. Scope of this pass vs. the full systemic sweep

The originating directive's sections 7–21 (idempotency inventory across
every domain, transaction-ownership audit of every live mutation service,
certificate/API-key rotation concurrency, trust/federation state-machine
design, secrets/credentials audit, cross-tenant systemic sweep of every
raw-SQL/background-job/AI-tool query, AI/agent surface audit, clinical
and financial and inventory domain-specific concurrency sweeps, cache
consistency, background-worker inventory, failure injection matrices) are
each independently a multi-day audit against an already-mature,
159-model-file, 55-route-module monolith. None of them were performed in
this pass. Attempting to mark them VERIFIED or CLOSED without doing the
work would be exactly the fabrication this directive's own Section 26
prohibits, so they are recorded as **NOT STARTED** in
`MUSTAFA_ACTIVE_REPAIR_QUEUE.md` rather than silently dropped or falsely
claimed complete. See `docs/security/FINAL_LIVE_SURFACE_SWEEP.md` for the
honest accounting of what this pass covers and what remains.

## 4. Highest-value next step (per this document's own findings)

The `national` and `governance` schema-latent findings
(`docs/architecture/LIVE_RUNTIME_SURFACE_MAP.md`) are now the single
largest block of reachable-but-non-functional live surface discovered
this session — 11 routers / 103 tables (`national`) and 1 router / 58
tables (`governance`). Neither is a concurrency finding (there is nothing
to race against an unbacked table), so they sit outside this document's
scope, but they are the correct next target for whoever owns those
domains' schema design, ahead of any further security/concurrency work
in either package.

## 5. Continuation — Command Center + Public Health (Section 2/3 of the follow-up directive)

Two more real closures of the exact same pattern named in
`docs/security/SYSTEMIC_CONCURRENCY_PATTERN_REGISTER.md`:
`command-center-emergency-resource-cas` (`resolve_emergency`,
`fulfill_resource`) and `public-health-outbreak-alert-cas`
(`update_alert_status`, which also lacked enum validation on the
client-supplied status string). Both proven pre-fix/post-fix on real
disposable PostgreSQL 16, both negative-proofed, both got permanent
regression suites (their domains had zero prior test coverage). Full
per-domain evidence: `docs/security/COMMAND_CENTER_CONCURRENCY_STATUS.md`,
`docs/security/PUBLIC_HEALTH_CONCURRENCY_STATUS.md`.

This brings the total to **6 independently proven and closed
concurrency defects this session** (payments, devices, biomedical,
command_center, public_health — 5 domains, 6 methods) — three of them
(biomedical, command_center, public_health) sharing the identical
"unused `OptimisticLockMixin`, no terminal-state guard" shape, now
formally registered as a systemic pattern rather than treated as three
coincidental one-offs.
