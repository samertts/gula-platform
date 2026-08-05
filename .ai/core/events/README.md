---
id: EVT-INDEX
type: event-bus
title: "Enterprise Event Bus"
version: "1.0.0"
created: "2026-08-05"
status: verified
confidence: 95%
tags: [events, loose-coupling, audit, replay, gula-kernel-ext-001]
---

# Enterprise Event Bus

> Mission: GULA-KERNEL-EXT-001 — Phase 5
> Implementation: `scripts/kernel/ext/event_bus.py`
> Journal: `event_journal.json`

**AI-operational only.** This bus decouples Kernel engines and extensions.
It is **not** the domain event bus — domain events keep using the outbox
pattern (`backend/app/outbox/`, `backend/app/services/outbox_service.py`)
per `docs/constitution/16_EVENT_CONSTITUTION.md`. Documented boundary:
this bus carries operational events (`migration.executed`,
`policy.changed`, `compat.break`, `plugin.installed`, …).

## Model

| Concept | Definition |
|---|---|
| Event | id (EVT-XXXXXX), name, publisher, payload, kind (domain/integration/system), priority |
| Delivery | audit record: event_id, handler, status (delivered/failed), detail |
| EventBus | subscribe (name or `*`), publish, replay, failures, snapshot, save |

## Guarantees (16_EVENT_CONSTITUTION)

1. **Loose coupling** — publishers and subscribers never reference each
   other; routing is by event name.
2. **At-least-once / idempotency** — an event id is delivered once per
   publish; handlers must be idempotent (replay support).
3. **Resilience** — a failed handler is recorded as `failed`; other
   handlers still run; ordering is preserved per publish call.
4. **Replay** — `replay()` re-delivers events (filterable by name) for
   recovery and backfill.
5. **Audit** — every delivery is journaled with status and detail.

## CLI

```bash
python scripts/kernel.py ext-event-bus   # demo publish + audit trail
python scripts/kernel.py ext-check       # includes event bus delivery gate
```

## Reuse

Composes `scripts/kernel/observability.py` (audit/trace semantics) and the
Kernel `utcnow` clock. Domain outbox infrastructure is deliberately NOT
imported — the two buses remain independent by design.

## Related

- `event_journal.json` — machine-readable delivery journal
- `docs/constitution/16_EVENT_CONSTITUTION.md` — event law
- `backend/app/outbox/` — domain event bus (out of scope, preserved)
