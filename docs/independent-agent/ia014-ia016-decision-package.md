# Decision package — the kernel event bus: delivery, protocol, and what the admin endpoints should say

**Lane:** Account 2 (independent adversarial audit), `claude/independent-audit-1`.
**Status:** evidence complete; three coupled decisions open. Nothing here is a
recommendation to adopt without review, and no architecture was chosen on the
committee's behalf.

Related findings: **IA-013** (bus loses events / no durable delivery), **IA-013a**
(FIXED — store bound), **IA-014** (admin endpoints pinned at zero), **IA-015** (FIXED —
dead probe on 6 route groups), **IA-016** (the same probe on 8 more, where the obvious fix
is a regression).

---

## 1. What is actually true today (all RUNTIME VERIFIED)

| Fact | Evidence |
|---|---|
| `Kernel` never exposes subsystems as attributes | `kernel.__dict__` = `_components`, `_services`, `_start_time`, `config`, `state`; `hasattr` stays False after `register_component` |
| `hasattr(kernel, "event_bus")` appeared in **14** files and is unsatisfiable in all of them | AST scan of `app/` |
| 6 of those built a throwaway bus per request | **89 served paths / 115 operations** — now FIXED (IA-015) |
| 8 of those pass `event_bus=None` permanently | **138 served paths / 130 operations** — NOT fixed (IA-016) |
| The kernel bus has **no subscribers in production code** | every kernel-bus `.subscribe()` in the tree is under `backend/tests/` |
| `publish()` never writes to outbox, inbox, retry queue or DLQ | 10 failing publishes → 0/0/0/0 |
| Two served admin endpoints report exactly those unwritten components | `/kernel/events/outbox`, `/kernel/events/dlq`, both `system:admin` |
| Two event protocols exist | kernel bus: `publish(Event)`; the 8 services: `emit(name, dict)` |
| A durable outbox **already exists and is wired** | `app/services/outbox_service.py` over the present `outbox_events` table, `OutboxWorker` started at `app/worker.py:86` and `app/core/startup.py:270` |

The last row is the crux. GULA has two outboxes: one real, backed by a migrated table and
a running worker, and one in-memory and unwritten, whose API surface is nonetheless served
to operators.

---

## 2. Decision 1 — does the kernel event bus deliver durably at all? (IA-013)

The question is not "how should retry work". It is **whether this bus should exist as a
delivery mechanism** given that `outbox_service.py` already is one.

| Option | What it means | Cost | Consequence |
|---|---|---|---|
| **D1-A. Retire it as a delivery mechanism.** Keep `publish`/`subscribe` as an in-process notification hook, documented as best-effort and lossy. Remove the outbox/inbox/retry/DLQ components, and with them the two admin endpoints. | Honest naming; one durable path (`outbox_events`). | Small. Deletes ~5 unwritten modules and 2 served endpoints. | Anything needing durability must use `outbox_service.py`. Resolves IA-014 by deletion. Loses no capability, because none of it currently works. |
| **D1-B. Wire it durably.** `publish` enqueues to the outbox; a worker drains it; failures go to the retry queue then the DLQ. | The kernel gets the semantics its docstring already advertises. | Large. Needs persistence (the current components are in-memory dicts, so a restart still loses everything), a worker, and a migration if it gets its own table. | Two durable outboxes to operate and reconcile. The docstring becomes true. |
| **D1-C. Back it with the existing outbox.** `publish` writes to `outbox_events` via `outbox_service.py`; the kernel bus becomes a façade. | One durable path, and the kernel API survives. | Medium. An adapter plus a decision about event-name namespacing in a shared table. | Resolves IA-013, IA-014 and IA-016's durability half at once. Couples the kernel to a service-layer module. |

**Evidence bearing on the choice, not a recommendation:** the bus has zero subscribers, so
D1-A removes nothing anyone consumes today. D1-B is the only option that makes the kernel
docstring accurate. D1-C is the only one that avoids operating two durable outboxes.

---

## 3. Decision 2 — which protocol does the bus speak? (IA-016)

Unblocks 130 served operations across 8 domains, 4 of them clinical.

| Option | What it means | Cost | Consequence |
|---|---|---|---|
| **D2-A. Adapt at the boundary.** Inject a small adapter exposing `emit(name, dict)` that builds an `Event` and calls `publish`. | 8 one-line provider changes plus one adapter class. | Smallest. | Two protocols stay alive in the codebase; the seam is explicit and testable. |
| **D2-B. Add `emit` to the kernel `EventBus`** as an alias for `publish`. | One method. | Smallest. | Blesses a second public protocol on the kernel's own API. Note `test_documented_gap_emit_protocol_services_cannot_accept_the_kernel_bus` asserts `not hasattr(EventBus, "emit")` and will fail, by design, pointing here. |
| **D2-C. Convert the 8 services to `publish(Event)`.** | Change `_emit` and its call sites in 8 service modules. | Largest. Four are clinical (blood bank, critical care, EMS, public health) and need their own test pass. | One protocol. Cleanest end state. |

**Hard constraint:** whichever is chosen, the `hasattr` probe in those 8 files must be
repaired **in the same change** as the protocol fix, never before it. Repairing the probe
alone is proven to raise `AttributeError` on served clinical routes:

```
blood_bank     event_bus=None  -> _emit() silently no-ops (event lost)
blood_bank     event_bus=BUS   -> AttributeError: 'EventBus' object has no attribute 'emit'
```

D2-C's value depends on Decision 1: converting 8 services to `publish` is worth more if
`publish` durably delivers (D1-B/C) and close to worthless if the bus is retired (D1-A),
in which case the right move is to delete `_emit` and the probe together.

---

## 4. Decision 3 — what should the admin endpoints say? (IA-014)

`GET /kernel/events/outbox` returns `{"pending": 0}` and `GET /kernel/events/dlq` returns
`{"entries": [], "count": 0}` for the life of the process, whatever happens. This is a
served response shape, which `CLAUDE.md` places under "Requires human approval", so it is
not mine to pick.

| Option | Response | Consequence |
|---|---|---|
| **D3-A. Report the wiring state.** `{"pending": 0, "wired": false}` | Truthful and non-breaking for clients reading `pending`. Adds a field. |
| **D3-B. Fail loudly.** `501 Not Implemented` while unwired. | Impossible to mistake for health. Breaks any client or dashboard that currently polls a 200. |
| **D3-C. Remove the endpoints** (only coherent with D1-A). | No misreporting surface. Removes an operator view that never worked. |
| **D3-D. Do nothing** until Decision 1 lands. | The false-green persists, now documented and pinned by a test. |

D3 collapses into Decision 1: choose D1-B or D1-C and the endpoints become truthful with
no shape change at all; choose D1-A and D3-C follows.

---

## 5. What was fixed without a decision, and why that was safe

| Fix | Why no decision was needed |
|---|---|
| **IA-013a** — bound `EventStore` at 10 000 with oldest-first eviction | Unbounded growth on a process-lifetime singleton is a defect under any of the options above. STATIC VERIFIED that nothing in `app/` reads the kernel store except `bus.publish`, so the bound cannot truncate a consumer. |
| **IA-015** — `resolve_event_bus()` replacing the dead probe in 6 modules | The probe is unsatisfiable, so the branch the author wrote never ran. The intent is unambiguous and documented (`app/kernel/__init__.py` lists `EventBus` as a kernel subsystem; the bootloader registers exactly one). The fallback is preserved for `enable_event_bus=False` and pre-boot kernels. Those 6 use `publish`, so they carry no IA-016 protocol hazard. |

The two are coupled: repairing the probe moves 115 served operations from a per-request
store to the process-wide one, so shipping IA-015 without IA-013a would have introduced a
leak. They landed together, and the negative proof covers both directions.

---

## 6. Suggested order

1. **Decision 1** first — it determines whether Decisions 2 and 3 are work or deletions.
2. **Decision 3** follows mechanically from Decision 1.
3. **Decision 2** last, as one change per domain, probe repair and protocol repair
   together, clinical domains with their own test pass.

Until Decision 1 lands, the tests named in IA-014 and IA-016 hold the current state in
place: the gaps cannot close silently, and the probe cannot spread to a ninth module.
