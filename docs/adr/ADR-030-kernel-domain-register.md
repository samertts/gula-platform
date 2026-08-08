# ADR-030: Kernel Domain Register — Strategic Exception (event bus) + Retain (DI, scheduler, cron)

**Status:** Accepted
**Date:** 2026-08-08
**Deciders:** Engineering Lead, Platform Architect, CTO
**Supersedes:** (none — registers the kernel cluster for the PROGRAM-01 final closure)
**Related:** ADR-028, ADR-029, ADR-024, ADR-034

---

## Context

The structural migration phase (ADR-028) reduces the acknowledged Shared Core
reimplementation findings in
`.ai/core/architecture/constitution_baseline.json` to canonical providers
(`SHARED_CORE_CATALOG` in `backend/app/domain_platform/shared_core.py`).

PROGRAM-01 FINAL CLOSURE (Wave 5 order 23) freezes the kernel-domain cluster.
The canonical providers in `shared/` for these capabilities are **dormant
stubs**:

- `shared/events` — 41-L sync pub/sub with **zero consumers and zero tests**.
- `shared/scheduler.py` — 79-L complete scheduler with **zero consumers**.
- `shared/di_container` — type-keyed auto-wiring container with **zero
  consumers**.

The kernel cluster (below) is the **live backbone** of the running platform
(event bus, scheduler, DI composition root). These are not duplicates of
working canonical infrastructure; they ARE the working infrastructure, and the
canonical `shared/` candidates are inactive placeholders.

### Findings in this register

| # | Path | Capability | Verdict |
|---|---|---|---|
| 18 | `kernel/event_bus/bus.py` — `EventBus` (809 L: store/outbox/DLQ/replay) | events | **Strategic Exception** |
| 11 | `kernel/runtime/di_container.py` — `DIContainer` (name-keyed locator) | dependency_injection | **Retain as Domain-Owned** (kernel) |
| 32 | `kernel/background/cron.py` — `CronEngine` (registry only, no exec) | scheduler | **Retain as Domain-Owned** (kernel) |
| 33 | `kernel/background/scheduler.py` — `Scheduler` (269-L composition root) | scheduler | **Retain as Domain-Owned** (kernel) |

**#18 (Strategic Exception, H\*):** the kernel `EventBus` is the platform
event backbone — store, outbox, DLQ, replay — used by 6+ services
(worker, outbox auto-repair, factory wiring). The canonical `shared/events`
(41 L, sync pub/sub) is a strict subset. Re-pointing the live backbone to a
strict subset with zero consumers would **remove** queue persistence, DLQ, and
replay — a behavior regression and an availability risk.

**#11/#32/#33 (kernel-domain Retain):** the kernel `DIContainer` is the
runtime composition root; the kernel `Scheduler`/`CronEngine` are the
registered background executors. Canonical `shared/di_container` and
`shared/scheduler` are incompatible (type-keyed auto-wiring vs name-keyed
locator; strict-subset) and have zero consumers. Consolidating would downgrade
live infrastructure to dormant placeholders.

**Behavioral equivalence:** freezing changes no behavior. The gate continues
to block growth (new files matching these rules fail) while the acknowledged
live implementations stay in place.

## Decision

Register the kernel cluster as a **frozen** finding class in the
constitution baseline, with explicit per-finding states:

1. **#18** — `Strategic Exception`: the kernel event bus is retained as the
   authoritative event backbone; `shared/events` remains dormant and is NOT a
   migration target. Any future consolidation requires a dedicated ADR and
   must first activate a feature-complete canonical provider.
2. **#11/#32/#33** — `Retain as Domain-Owned` (kernel-domain register): the
   kernel DI container, scheduler, and cron engine are retained. Their state
   is written to the baseline JSON alongside the Domain-Owned register
   (ADR-034).
3. **No behavior, API, schema, or audit change.** No code moves. The gate
   acknowledges these findings so future PRs cannot add new duplicate
   signals in these capabilities.
4. **ADR-028 Rules 1-7 apply.** The decision is documented, evidence-based,
   reversible, and committed atomically with the PROGRAM-01 final closure.

The first application is the PROGRAM-01 FINAL CLOSURE commit (Wave 5 order 23),
which writes the states to `.ai/core/architecture/constitution_baseline.json`
and freezes the baseline at 25 acknowledged findings (0 actionable).

## Alternatives Considered

### A. Consolidate the kernel bus onto `shared/events`

Rejected. `shared/events` (41 L, sync, zero consumers, zero tests) is a strict
subset of the kernel `EventBus` (809 L, store/outbox/DLQ/replay). This would
remove persistence, DLQ, and replay — an unacceptable behavior/availability
regression on the live event backbone.

### B. Promote the kernel cluster into `shared/` and make it canonical

Rejected. The kernel cluster is tightly coupled to kernel runtime
(`app.kernel`) and the platform composition root. Moving it to `shared/` is a
large, behavior-preserving refactor with no consumer benefit today; the
existing "canonical" `shared/` candidates are unused placeholders. This is
tracked as future work (requires an active canonical provider first), not a
safe final-closure action.

### C. Do nothing (leave findings actionable)

Rejected. PROGRAM-01 final closure must leave **zero actionable** findings.
The kernel cluster is legitimate live infrastructure; leaving it "actionable"
forces an unsafe migration or an infinite open finding. A formal frozen
register with explicit state is the correct governance.

## Consequences

**Positive**

- The kernel cluster (event bus, DI, scheduler, cron) is formally recognized
  as live infrastructure with an explicit `Strategic Exception` /
  `kernel-domain` state, ending PROGRAM-01 with **0 actionable** findings.
- The gate remains deterministic: any NEW signal in `events`,
  `dependency_injection`, or `scheduler` outside the acknowledged paths fails
  the PR.
- `shared/events` / `shared/scheduler` / `shared/di_container` remain dormant
  but unblocked for future canonical activation.

**Negative**

- The kernel event bus remains a non-`shared/` implementation; any future
  consumer of a canonical event bus must first activate a feature-complete
  `shared/events` provider (dedicated ADR).
- `shared/scheduler` and `shared/di_container` stay unused placeholders.

**Neutral**

- No code, schema, API, or behavior changes. Baseline freezes at 25
  acknowledged findings (0 actionable).

## References

- ADR-028 — Structural Migration Rules (`docs/adr/ADR-028-structural-migration.md`)
- ADR-029 — Canonical Provider Promotion (`docs/adr/ADR-029-canonical-provider-promotion.md`)
- ADR-034 — Retain-as-Domain-Owned Register (`docs/adr/ADR-034-retain-as-domain-owned-register.md`)
- `backend/app/kernel/event_bus/bus.py` — #18 kernel EventBus
- `backend/app/kernel/runtime/di_container.py` — #11 kernel DIContainer
- `backend/app/kernel/background/{cron,scheduler}.py` — #32/#33 kernel scheduler/cron
- `backend/app/domain_platform/shared_core.py` — `SHARED_CORE_CATALOG` (events, dependency_injection, scheduler)
- `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md` — §2 (#11/#18/#32/#33), Wave 5 order 23
