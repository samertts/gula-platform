# GULA Offline & Synchronization Reassessment

**Directive:** GULA-PBR-2026-11-19, §9 (Priority P2)  
**Repository:** `gula-integration` · **Branch:** `integration/gula-unification-v1`  
**HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549` · **Date:** 2026-11-19  
**Method:** read-only source inspection. No code changed, no runtime drill simulated, no DB/Redis touched.

---

## 1. Status summary

| Capability | Observed implementation | Status | Production claim? |
|---|---|---|---|
| Offline event capture | Three distinct engines (see §2) | `IMPLEMENTED` | No |
| Durable event storage | In-process byte buffer / Python dicts only | `NOT IMPLEMENTED` (durable) | No |
| Retry / backoff | Bounded retry with injected clock in `durable_queue.py` | `TESTED` (synthetic harness) | No |
| Idempotency | Event-id keyed commit; `IdempotentProcessor` | `TESTED` (synthetic) | No |
| Conflict resolution | LWW + version check; quarantine strategy | `IMPLEMENTED` | No |
| Device-restart recovery | Simulated replay of in-memory WAL | `TESTED` (simulation only) | No |
| Interrupted sync / duplicate events / ordering | Handled in synthetic harness | `TESTED` (simulation only) | No |
| Tenant isolation in harness | tenant/facility mismatch rejection | `TESTED` (synthetic) | No |
| Audit preservation across sync | Canonical `log_action` used by `nhdw/offline.py`; local health-core offline `AuditLog` is a separate in-memory class | `IMPLEMENTED` (scoped) | No |
| Real device-partition / network-interruption drill | Not executed | `BLOCKED` (operational environment) | No |

No `PRODUCTION READY`, no `INTEGRATED`, no `INDEPENDENTLY VERIFIED` award made here.

---

## 2. Three offline engines (distinct, not yet unified)

| Engine | File | Storage | Notes |
|---|---|---|---|
| `OfflineSyncEngine` (service) | `backend/app/services/offline_sync_service.py:72` | `_operations: dict`, `_conflicts: dict`, `_vector_clocks: dict`, `_sync_log: list` | HMAC signing, vector clocks, `CONFLICT_QUARANTINE`; F-069/D-023 removed a misnamed "CRDT" strategy and replaced it with an honestly named quarantine strategy. |
| `OfflineSyncEngine` (core) | `backend/app/core/sync_engine.py:24` | `local_event_log: list`, `synced_event_ids: set` | LWW + strict version comparison; no persistence. |
| `OfflineSyncEngine` (health-core reliability) | `backend/app/health_core/reliability/durable_queue.py` | in-process checksummed/hash-chained byte buffer | Explicit boundary statement: "This is NOT production-grade durability and makes NO durability claim"; payload digests only, no keyed signature, no external anchor. |

Also present: `backend/app/integration/offline.py`, `backend/app/health_core/integration/offline.py`, `backend/app/citizen_platform/offline.py`, `backend/app/nhdw/offline.py`, `backend/app/platform/sync.py`, plus a simulation guide/script (`gula_offline_simulation_guide.md`, `gula_offline_simulation_test.py`). These are separate surfaces; no single durable offline subsystem is certified.

## 3. Evidence-backed limitations

1. **Process-local durability.** `durable_queue.py` states its log is a byte buffer; a "crash" is simulated by dropping derived state and replaying those bytes. There is no filesystem, DB, broker, network, keyed signature or external monotonic anchor. A restart-recovery test on this harness does not prove device-restart recovery.
2. **Payload loss on replay.** Only SHA-256 digests are persisted, so replayed events carry an empty payload. Recovering payload content would require a keyed, tenant-scoped external anchor — explicitly owner-blocked in the module header.
3. **In-memory service state.** `offline_sync_service.py` keeps all operations/conflicts/vector clocks in dictionaries; a process restart loses them. `core/sync_engine.py` keeps events in a list.
4. **Audit separation.** `health_core/reliability/*` uses a local in-memory `AuditLog` class (e.g. `performance.py:86`, `sync_conflicts.py:162`) that is NOT the canonical ORM `AuditLog`. It is a design-harness accounting object, not a tamper-evident persisted audit record. `nhdw/offline.py` does call canonical `log_action` (covered by `AUDIT-POSITIONAL-001`).
5. **No runtime drills.** Network interruption, device partition, clinical-alert outage and multi-device conflict under real conditions were not executed; only synthetic harness tests exist.

## 4. Focused implementation plan (safe scope only)

All items below require owner/architecture sign-off before touching production paths; engineering can prepare but not activate them.

| Step | Action | Safe now? | Owner gate |
|---|---|---|---|
| 1 | Adopt ONE durable event-store contract (append-only, tenant-scoped, checksummed, idempotency key) backed by an existing self-hosted store (PostgreSQL) — reuse before build | No — architectural decision | ADR / architecture owner |
| 2 | Replace the three in-memory engines with adapters to that contract; keep the synthetic harness as a conformance suite, not as production storage | No — code change + owner decision | Architecture owner |
| 3 | Add keyed, tenant-scoped external anchor so replay can recover payload safely (currently digests only) | No — security-sensitive key management | Security owner |
| 4 | Wire canonical `log_action` for all offline-originated security-sensitive events; keep local harness `AuditLog` clearly scoped to simulation | Partly — documentation only now | Security owner |
| 5 | Define ordering/idempotency semantics for out-of-order device events (vector clock → deterministic tie-break) and document conflict quarantine workflow | Documentation/spec safe | Clinical + architecture owner |
| 6 | Real device-partition / network-interruption / restart drills in a disposable environment with recorded RPO/RTO | No — operational environment | Operations owner |
| 7 | Add durable-store integration tests (restart, interrupted sync, duplicate events, tenant isolation, audit preservation) | After steps 1–3 | Engineering, after owner gate |

## 5. Non-claims

No `PRODUCTION READY`, no `INTEGRATED`, no E2E verification, no clinical/legal/regulatory approval, no operational drill result. No production DB/Redis access, real PHI, or secrets. No commit, push, merge, PR or deployment. Standing release decision remains **HOLD**; Stable v1.0.0 is **NOT declared**.
