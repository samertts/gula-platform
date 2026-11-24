# C09 event and offline-stack consolidation — 2026-11-24

## Scope and authority

This batch implements an engineering consolidation seam. It does **not** change
release status, does not activate dormant stacks, does not change the kernel or
Health Core runtime, and does not imply owner approval of BK-017 or ADR-J/J1.
No broker, SaaS, or external network dependency was introduced. All runtime
code uses the existing PostgreSQL/SQLAlchemy/FastAPI stack.

## Duplication inventory and discrepancy

Governance records disagree on the exact enumeration:

* `docs/parallel-program/distributed/SYNCHRONIZATION_AUDIT.md` and
  `GULA_NATIONAL_ARCHITECTURE_BLUEPRINT_V2.md` describe kernel bus, shared
  in-process bus, Health Core synthetic events, and one SQL outbox — four
  implementations, with no code path connecting them.
* `GULA_NATIONAL_MODULE_REGISTRY_V2.md` lists BUS-1, BUS-2, BUS-3 and OUT-1.
* Offline engines are variously enumerated as health_core deterministic
  conflict engine / `core/sync_engine` LWW / native clients / hospital desktop,
  or as three backend modules (`services/offline_sync_service.py`,
  `core/sync_engine.py`, `health_core/reliability/durable_queue.py`).

The discrepancy is recorded, not silently resolved. The consolidation below
covers all named code paths through adapters while leaving ownership
rectification as an owner-gated documentation decision.

## Authoritative implementation

Single source of event semantics:

* `backend/app/eventing/authority.py`
  * `CanonicalEventEnvelope` — `IntegrationEventEnvelope` plus
    `aggregate_type`, `aggregate_id`, `sequence`.
  * `NationalEventAuthority.publish` — transactional append to `outbox_events`,
    no internal commit.
  * `NationalEventAuthority.drain` — ordered batch, row locking, explicit
    acknowledgement. `require_handler=True` is the canonical policy: an event
    with zero successful handlers is **not** marked done.
  * `NationalEventAuthority.stage_inbound` — the existing durable inbox with
    event-id and tenant/idempotency uniqueness.

Durable substrate:

* `backend/app/models/outbox.py` — added canonical columns and a unique
  `event_id` constraint while retaining all legacy defaults.
* `backend/migrations/versions/20261124_0003_canonical_event_fabric.py` —
  additive migration after `20261124_0002`; legacy rows are backfilled with
  stable synthetic identifiers. Alembic reports a single head
  `20261124_0003 (head)`.

## Compatibility adapters

`backend/app/eventing/adapters.py` translates, without duplicating delivery
logic:

| Historical surface | Adapter | Preserved behavior |
| --- | --- | --- |
| `emit_to_outbox` | `legacy_emit_to_outbox` | Original call signature, payload, no internal commit, synthetic attribution fields |
| `OutboxWorker.run_once` | `legacy_run_once(db, dispatcher=events.emit)` | Legacy zero-handler events are still acknowledged; `app.services.outbox_service.events` remains a monkeypatch seam |
| kernel `EventBus` event | `from_kernel_event` | Event name/id/timestamp/correlation/tenant mapped to canonical envelope |
| Health Core `DomainEvent` | `from_health_domain_event` | Source schema version retained inside payload; no synthetic record published |
| `core.sync_engine.SyncEvent` | `from_sync_engine_event` | Version mapped to sequence; LWW decisions unchanged |
| `services.offline_sync_service.SyncOperation` | `from_offline_operation` | Vector clock sum mapped to sequence; CONFLICT_QUARANTINE semantics untouched |

`backend/app/services/outbox_service.py` now delegates both writer and drain to
the adapters. No other module implements publish/drain semantics.

## Verification

| Evidence | Result |
| --- | --- |
| Targeted SQLite consolidation + legacy outbox suites | `26 passed, 1 warning in 3.67s`, exit `0` |
| PostgreSQL 16 migration to Alembic head | exit `0`; `20261124_0003`; canonical columns and unique constraint present |
| PostgreSQL 16 migration downgrade/upgrade round trip | exit `0`; `20261124_0002` with `0` canonical columns, then `20261124_0003` with `9` canonical columns |
| PostgreSQL 16 canonical tests | `4 passed, 1 warning in 1.59s`, exit `0` |
| No-STUB drift guard | `17 passed, 1 warning in 97.60s`, exit `0` |

Logs: `V4_EVENT_AUTHORITY_TARGETED_GREEN_2026_11_24.txt`,
`V4_EVENT_MIGRATION_2026_11_24.txt`,
`V4_EVENT_MIGRATION_ROUNDTRIP_2026_11_24.txt`,
`V4_EVENT_AUTHORITY_POSTGRES_GREEN_2026_11_24.txt`,
`V4_NO_STUB_DRIFT_GUARD_2026_11_24.txt`.

Preserved failures:

* `V4_EVENT_ADAPTER_PATCH_SEAM_FAILURE_2026_11_24.txt` — removing the legacy
  `events` attribute broke seven existing patch targets. The patch seam was
  restored and passed. Classification: backward-compatibility regression in
  the adapter, not a product defect.
* `V4_EVENT_PG_MISSING_COMMIT_FAILURE_2026_11_24.txt` — the PG harness closed
  sessions before committing canonical writes. Classification: harness error.
* `V4_EVENT_PG_DUPLICATE_ASSERTION_FAILURE_2026_11_24.txt` — uniqueness raised
  at `flush()` rather than at the later `commit()`. Classification: harness
  assertion error; both were corrected.

Coverage includes transactional rollback, duplicate `event_id`, ordered
persistence, strict acknowledgement, retry and final failure, all four adapter
shapes, stable replay identifiers, inbound inbox deduplication, and preservation
of legacy zero-handler acknowledgement.

## Residual status

* Event fabric: `IMPLEMENTED AS ENGINEERING SEAM · NOT ACTIVATED AS SOLE RUNTIME
  BUS · NOT ACCEPTED`. Kernel and Health Core stacks still exist and retain
  their historical behavior.
* ADR-J/J1, BK-017, C09 version bump, and G1/G4/G10 remain owner-gated.
* Dual outbox worker registration (`app/worker.py` and
  `app/core/startup.py`) was not changed in this batch; changing runtime
  ownership requires an owner decision.
* `contracts/export/asyncapi.json` remains a 102-byte stub; it was not promoted
  or regenerated in this batch.
