---
id: MIGR-INDEX
type: migration
title: "Migration Framework"
version: "1.0.0"
created: "2026-08-05"
status: verified
confidence: 95%
tags: [migration, rollback, versioning, gula-kernel-ext-001]
---

# Migration Framework

> Mission: GULA-KERNEL-EXT-001 — Phase 4
> Implementation: `scripts/kernel/ext/migration.py`
> Machine-readable plans: `migration_plans.json`

Versioned, **reversible** migrations for the AI knowledge base: knowledge,
policies, plugins, registry entries, and config. Built on the Kernel
recovery layer (`scripts/kernel/recovery.py`) semantics — this module
orchestrates plans; retry/resume/recovery remain in the Kernel.

## Model

| Concept | Definition |
|---|---|
| MigrationStep | One forward or rollback action (description + callable) |
| MigrationPlan | id (MIGR-XXXXXX), target, from → to version, steps, rollback steps, precheck, state |
| State machine | planned → approved → executed \| failed → rolled_back |
| MigrationEngine | register (unique ids), execute (precheck → steps → audit), rollback, snapshot |

## Targets

`knowledge`, `policy`, `plugin`, `registry`, `config`

## Safety Properties

1. **Reversibility** — every plan declares rollback steps; failure runs
   rollback automatically and records a `failed` event in history.
2. **Immutability** — a plan that has executed cannot execute again.
3. **Prechecks** — a failing precheck aborts before any step runs.
4. **Audit** — every transition (registered/executed/failed/rolled_back)
   is recorded with a timestamp.
5. **Breaking detection** — `is_breaking` uses SemVer major-version bumps
   (shared with Phase 3 Compatibility); breaking migrations require an
   approval gate before execution.

## CLI

```bash
python scripts/kernel.py ext-migrate       # registry snapshot
python scripts/kernel.py ext-migrate-run   # execute demo plan (in-memory)
python scripts/kernel.py ext-check         # includes migration engine gate
```

## Reuse

Composes `scripts/kernel/recovery.py` (retry/incident semantics) and Phase 3
`is_breaking_change` — no retry or semver logic is duplicated.

## Related

- `migration_plans.json` — machine-readable plan registry
- Phase 3 Compatibility Framework — breaking-change detection
- `scripts/kernel/recovery.py` — rollback/resume/incident handling
- `docs/constitution/23_BACKWARD_COMPATIBILITY.md` — constitutional basis
